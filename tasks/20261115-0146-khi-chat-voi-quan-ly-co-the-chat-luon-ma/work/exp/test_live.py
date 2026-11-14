"""Mô phỏng run_turn với một 'claude' giả đọc stdin stream-json — không gọi API, không đụng tasks/ thật.

Chạy:  python3 -I tasks/<task>/work/exp/test_live.py /đường/dẫn/repo
Kiểm tra:
  A. tin gửi giữa lượt được nạp vào stdin TRƯỚC result của tin 1 (claude giả ghi nhận "mid-turn")
  B. inbox.jsonl trống sau khi nạp, event "Quản lý đã nhận tin (giữa lượt)" có, pentagon_owner không bị ghi trùng
  C. tin gửi SAU khi stdin đã đóng (sau result) vẫn nằm trong inbox → drain_inbox mở lượt mới (không mất tin)
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
TMP = tempfile.mkdtemp(prefix="pt-live-")
FAKEBIN = os.path.join(TMP, "bin")
os.makedirs(FAKEBIN)
LOG = os.path.join(TMP, "fake-claude.log")

# claude giả: 3 "bước" mỗi bước 1.5s; giữa các bước đọc stdin không chặn (mô phỏng chèn tin giữa lượt).
FAKE = r'''#!/usr/bin/env python3
import json, os, select, sys, time
log = open(%r, "a")
def out(o): sys.stdout.write(json.dumps(o) + "\n"); sys.stdout.flush()
def readline(timeout):
    r, _, _ = select.select([sys.stdin], [], [], timeout)
    return sys.stdin.readline() if r else None
out({"type": "system", "subtype": "init", "session_id": "x"})
turn = 0
while True:
    line = readline(None)
    if not line:
        break
    msg = json.loads(line)["message"]["content"]
    turn += 1
    log.write("turn%%d start: %%s\n" %% (turn, msg[:60])); log.flush()
    steps = 3 if turn == 1 else 1
    for i in range(steps):
        out({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "sleep"}}]}})
        time.sleep(1.5)
        more = readline(0)
        if more:
            log.write("turn%%d mid-turn: %%s\n" %% (turn, json.loads(more)["message"]["content"].replace(chr(10), " ")[-120:])); log.flush()
    out({"type": "assistant", "message": {"content": [{"type": "text", "text": "xong turn %%d" %% turn}]}})
    out({"type": "result", "subtype": "success", "is_error": False, "result": "ok", "duration_ms": 10})
log.write("EOF exit\n"); log.flush()
''' % LOG
with open(os.path.join(FAKEBIN, "claude"), "w") as f:
    f.write(FAKE)
os.chmod(os.path.join(FAKEBIN, "claude"), 0o755)

os.environ["PATH"] = FAKEBIN + os.pathsep + os.environ["PATH"]
os.environ["ORCH_DATA"] = os.path.join(TMP, "data")
conf = os.path.join(TMP, "workers.conf")
with open(conf, "w") as f:
    f.write("claude | claude | default | test | \n")
os.environ["ORCH_CONF"] = conf

sys.path.insert(0, os.path.join(REPO, "bin"))
import pt_manager as M  # noqa: E402

M.TASKS = os.path.join(TMP, "tasks")
M.progress = lambda *a, **k: None          # không gọi bin/progress thật
tid = "20990101-0000-test"
tdir = os.path.join(M.TASKS, tid)
os.makedirs(os.path.join(tdir, "manager"))
open(os.path.join(tdir, "status"), "w").write("state=dang-lam\n")
open(os.path.join(tdir, "log.txt"), "w").close()
M.put(tid, "session", "00000000-0000-0000-0000-000000000001")
started_turns = []
M.start_turn = lambda t, msg, *a, **k: started_turns.append(msg) or 1  # drain_inbox → ghi lại thay vì spawn
# manager_info: coi như đang chạy trong lúc run_turn chạy
running = {"v": True}
orig_info = M.tracker.manager_info
M.tracker.manager_info = lambda d: dict(orig_info(d), running=running["v"])

inp = os.path.join(TMP, "input.txt")
open(inp, "w").write("TIN 1: làm 3 bước")


def owner_send(text):
    with M.inbox_lock(tid):
        return M.enqueue_inbox_locked(tid, text, "auto", "", "", "")


th = threading.Thread(target=lambda: M.run_turn(tid, inp))
th.start()
time.sleep(2.0)
owner_send("TIN 2: gửi giữa lượt")
th.join(timeout=30)
running["v"] = False
inbox_left = M.inbox_read(tid)

# C: gửi sau khi lượt kết thúc → vẫn nằm trong inbox, drain_inbox lấy
owner_send("TIN 3: gửi sau khi hết lượt")
M.drain_inbox(tid)

log = open(LOG).read()
stream = [json.loads(x) for x in open(os.path.join(tdir, "manager", "stream.jsonl"))]
owners = [e["text"] for e in stream if e.get("type") == "pentagon_owner"]
events = [e["text"] for e in stream if e.get("type") == "pentagon_event"]
print(log)
print("events:", events)
checks = {
    "A tin 2 vào giữa lượt 1": "turn1 mid-turn" in log and "TIN 2" in log.split("turn1 mid-turn", 1)[1].split("\n")[0],
    "B inbox trống sau lượt": inbox_left == [],
    "B có event nhận giữa lượt": any("giữa lượt" in e for e in events),
    "B pentagon_owner không trùng": owners.count("TIN 2: gửi giữa lượt") == 1,
    "C tin 3 mở lượt mới": len(started_turns) == 1 and "TIN 3" in started_turns[0],
    "cờ live đã xoá": not os.path.exists(os.path.join(tdir, "manager", "live")),
    "claude giả thoát do EOF": "EOF exit" in log,
    "inflight trống (tin đã xác nhận xử lý)": not os.path.exists(os.path.join(tdir, "manager", "inflight.jsonl")),
}

# D: tin đã nạp mà lượt bị Dừng/chết trước result thành công → trả về hàng chờ, không mất
with M.inbox_lock(tid):
    M.inflight_add_locked(tid, [{"text": "TIN 4: nạp rồi bị Dừng", "ts": 1}])
    n = M.requeue_inflight_locked(tid)
    rows = M.inbox_read(tid)
checks["D tin chưa xử lý quay lại hàng chờ"] = n == 1 and any("TIN 4" in r.get("text", "") for r in rows)
with M.inbox_lock(tid):
    M.inflight_add_locked(tid, [dict(r) for r in M.inbox_read(tid) if "TIN 4" in r.get("text", "")])
    os.remove(os.path.join(tdir, "manager", "inbox.jsonl"))
    M.requeue_inflight_locked(tid, count=True)   # lỗi lần 1 → còn
    M.inflight_add_locked(tid, M.inbox_read(tid))
    os.remove(os.path.join(tdir, "manager", "inbox.jsonl"))
    M.requeue_inflight_locked(tid, count=True)   # lỗi lần 2 → bỏ, không lặp vô hạn
checks["D lỗi 2 lần thì bỏ tin"] = M.inbox_read(tid) == []
for k, v in checks.items():
    print(("OK   " if v else "FAIL ") + k)
print("thư mục tạm:", TMP)
sys.exit(0 if all(checks.values()) else 1)
