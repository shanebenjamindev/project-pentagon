"""Thử nghiệm: claude -p --input-format stream-json, stdin giữ mở, gửi tin 2 giữa lượt."""
import subprocess, json, time, sys, uuid, os, tempfile
sid = os.environ.get("SID") or str(uuid.uuid4())
mode = os.environ.get("MODE", "--session-id")
wd = os.environ.get("WD") or tempfile.mkdtemp(prefix="sjtest-")
cmd = ["claude", "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose", "--model", "haiku",
       "--permission-mode", "acceptEdits", "--allowedTools", "Bash(sleep:*)", "Bash(echo:*)", mode, sid] + sys.argv[1:]
p = subprocess.Popen(cmd, cwd=wd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
t0 = time.time()


def msg(t):
    return json.dumps({"type": "user", "message": {"role": "user", "content": t}}) + "\n"


first = os.environ.get("FIRST", "Chạy lần lượt 3 lệnh Bash riêng biệt: `sleep 5`, rồi `sleep 5`, rồi `sleep 5` (mỗi lệnh một lần gọi tool, không gộp). Sau đó trả lời 'XONG1'. Nếu trong lúc làm có tin nhắn mới của tôi, hãy làm theo nó.")
p.stdin.write(msg(first))
p.stdin.flush()
sent2 = False
results = 0
closed = False
close_after = int(os.environ.get("CLOSE_AFTER", "1"))
send2 = os.environ.get("SEND2", "1") == "1"
for line in p.stdout:
    try:
        e = json.loads(line)
    except ValueError:
        print("RAW", line[:100])
        continue
    tp = e.get("type")
    st = e.get("subtype")
    extra = ""
    if tp == "assistant":
        c = e["message"]["content"]
        extra = " | ".join((x.get("text") or (x.get("name", "") + str(x.get("input", ""))))[:80] for x in c)
    elif tp == "user":
        c = e.get("message", {}).get("content")
        extra = str(c)[:140] + (" [replay]" if e.get("isReplay") else "")
    elif tp == "result":
        results += 1
        extra = str(e.get("result"))[:100] + " turns=%s err=%s" % (e.get("num_turns"), e.get("is_error"))
    elif tp == "system":
        extra = str(e.get("session_id"))
    print("%5.1f %s %s %s" % (time.time() - t0, tp, st or "", extra), flush=True)
    if send2 and tp == "assistant" and not sent2 and any(x.get("type") == "tool_use" for x in e["message"]["content"]):
        p.stdin.write(msg("TIN 2: sau khi xong các lệnh sleep, hãy chạy thêm `echo CHEN` và trả lời kèm chữ 'DA-NHAN-TIN-2'."))
        p.stdin.flush()
        sent2 = True
        print("%5.1f >>> sent msg2" % (time.time() - t0), flush=True)
    if tp == "result" and not closed and results >= close_after:
        p.stdin.close()
        closed = True
        print("%5.1f >>> closed stdin" % (time.time() - t0), flush=True)
p.wait()
print("exit", p.returncode, "results", results, "t=%.1f" % (time.time() - t0))
print("stderr:", p.stderr.read()[:500])
print("SID", sid, "WD", wd)
