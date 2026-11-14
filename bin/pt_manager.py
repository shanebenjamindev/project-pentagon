"""Chạy AI quản lý (Claude Code) ở chế độ nền cho một task, để chủ thao tác từ web.

Mỗi task có một phiên Claude Code riêng, lưu trong tasks/<id>/manager/:
  session        id phiên (uuid) — lượt sau dùng --resume để quản lý nhớ ngữ cảnh
  begun          có file này = phiên đã thật sự bắt đầu (lượt sau phải --resume)
  pid            tiến trình đang chạy lượt hiện tại (pid=, started=)
  pending        đang chuẩn bị (vd đang phân loại cỡ task), chưa chạy
  size           cỡ task: nho | vua | lon  → chọn model quản lý theo config/models.conf
  model          model quản lý (vd haiku, sonnet@high) — chủ đổi được trên web
  split          kiểu giao việc: mot (một worker làm) | song-song
  account        tài khoản Claude đang dùng (tên trong workers.conf)
  retry_at       giờ tự làm tiếp (epoch) khi mọi tài khoản đều hết hạn mức
  stream.jsonl   toàn bộ sự kiện các lượt (stream-json của Claude Code)
                 + dòng của Pentagon: {"type":"pentagon_owner"|"pentagon_event", ...}
  input-*.txt    nội dung đã gửi cho quản lý ở mỗi lượt
  stderr.log     lỗi (nếu có)

Hết hạn mức giữa chừng: lượt đang chạy dừng lại, phiên được chép sang tài khoản Claude kế tiếp trong
workers.conf và quản lý làm tiếp đúng phiên đó. Hết sạch tài khoản: task chuyển "chờ", tự làm tiếp khi
hạn mức làm mới (cần bin/dashboard đang chạy).

Dòng lệnh (bin/manager):
  bin/manager new [--duyet|--lam-luon] [--co auto|nho|vua|lon] [--mot|--song-song] [--ai <worker>] "yêu cầu"
                                                   tạo task và cho quản lý bắt đầu (mặc định: quản lý tự phân loại cỡ,
                                                   tự chọn cách giao và AI làm; --ai chỉ định AI, AI bận thì task chờ)
  bin/manager send <task> "tin nhắn"               gửi tin nhắn (lượt mới) cho quản lý của task
  bin/manager stop <task>                          dừng quản lý (và các worker nó đang chạy)
  bin/manager kill-worker <task> <pid>             huỷ một worker đang chạy
  bin/manager size <task> <nho|vua|lon> ["lý do"]  quản lý đổi cỡ task (model đổi từ lượt sau)
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

import tracker
from tracker import ROOT, TASKS, kv, pid_alive, read

CONF = os.path.join(ROOT, "config", "manager.conf")
MODELS = os.path.join(ROOT, "config", "models.conf")
WORKERS = os.environ.get("ORCH_CONF") or os.path.join(ROOT, "config", "workers.conf")
SIZES = {"nho": "nhỏ", "vua": "vừa", "lon": "lớn"}
LIMIT_RE = re.compile(r"usage limit|rate limit|limit reached|hit your limit|out of (usage|credits)|quota|"
                      r"exhausted|too many requests|\b429\b", re.I)

# Quyền mặc định của quản lý khi chạy nền. Muốn thêm: config/manager.conf, dòng allow=...
BASE_TOOLS = [
    "Bash(bin/ask:*)", "Bash(bin/progress:*)", "Bash(bin/new-task:*)", "Bash(bin/workers)",
    "Bash(bin/workers:*)", "Bash(bin/status:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(head:*)",
    "Bash(tail:*)", "Bash(wc:*)", "Bash(mkdir:*)", "Bash(date)", "Bash(date:*)", "Bash(bin/manager size:*)",
    "Read", "Write", "Edit", "Glob", "Grep", "Agent", "Task", "TodoWrite",
]

WEB_RULES = """Bạn đang chạy ở CHẾ ĐỘ WEB của Pentagon (không tương tác).
Chủ làm việc với bạn qua giao diện web: chủ chỉ thấy các câu trả lời bằng chữ của bạn, nhật ký và các file trong thư mục task.
- Thư mục task của phiên này: {task}
  Thư mục đã được tạo sẵn và yêu cầu gốc đã ghi vào brief.md. KHÔNG chạy bin/new-task.
  Nếu tiêu đề (dòng # đầu tiên của brief.md) dài hoặc chưa rõ, sửa lại cho ngắn gọn.
- Luôn ghi tiến độ bằng bin/progress {task} <bước> "..." như CLAUDE.md quy định.
- {split}
- {assignee}
- CỠ TASK: {size} — do bạn (quản lý) phân loại. Làm một lúc mà thấy cỡ sai (task lớn/nhỏ hơn dự đoán) thì chạy
  bin/manager size {task} <nho|vua|lon> "lý do" — model của bạn đổi theo từ lượt sau.
  Mỗi việc con, chọn cỡ theo độ khó của CHÍNH việc đó và truyền cho bin/ask:
  -s nho (việc ngắn, rõ ràng) | -s vua | -s lon (khó, cần suy luận sâu). Việc dễ luôn dùng -s nho để đỡ tốn hạn mức.
  Ghi cỡ đã chọn vào cột Worker trong plan.md, vd "codex (-s nho)".
- Khi cần chủ duyệt hoặc trả lời: chạy bin/progress {task} cho "<câu hỏi ngắn>", rồi KẾT THÚC lượt bằng câu hỏi rõ ràng.
  Chủ sẽ trả lời ở lượt sau. Không dùng công cụ hỏi tương tác, không ngồi chờ.
- Chạy bin/ask TRỰC TIẾP (không chạy nền, không dùng run_in_background, không dùng Monitor để chờ), đặt timeout của lệnh
  Bash là 600000 ms; việc lâu hơn thì giao qua agent worker. Không kết thúc lượt khi còn worker đang chạy: lượt kết thúc
  là mọi lệnh đang chạy bị dừng và phần việc đó bị mất.
- Hết hạn mức: bin/ask tự chuyển tài khoản và tài khoản sau làm tiếp phần dở. Nếu bin/ask báo MỌI tài khoản của
  một công cụ đều hết hạn mức (mã thoát 75): chuyển việc sang công cụ khác phù hợp; không còn cách thì chạy
  bin/progress {task} cho "hết hạn mức, chờ tự làm tiếp" và kết thúc lượt — hệ thống sẽ tự gọi bạn làm tiếp khi có hạn mức.
- Kết thúc mỗi lượt bằng 2-4 dòng tóm tắt: đã làm gì, đang ở bước nào, cần chủ làm gì (nếu có).
- Một số lệnh có thể bị từ chối vì quyền chạy nền bị giới hạn. Khi đó ghi rõ trong câu trả lời lệnh nào cần chủ chạy tay."""

SPLIT_RULES = {
    "auto": "KIỂU GIAO VIỆC: BẠN TỰ CHỌN (chủ để quản lý quyết). Ưu tiên giao cho MỘT worker phù hợp nhất, làm lần lượt. "
            "Chỉ chạy song song nhiều worker khi task có các phần độc lập, đủ lớn và làm song song lợi rõ ràng.",
    "mot": "KIỂU GIAO VIỆC: MỘT WORKER (chủ chọn). Giao việc cho MỘT worker phù hợp nhất (gọi theo tên công cụ, "
           "vd bin/ask codex, để tự xoay tài khoản). Nếu có nhiều bước thì giao LẦN LƯỢT từng bước. KHÔNG chạy song "
           "song, không gọi nhiều agent worker cùng lúc. Bạn tự kiểm tra kết quả; chỉ nhờ worker khác kiểm tra chéo "
           "khi task thật sự quan trọng.",
    "song-song": "KIỂU GIAO VIỆC: SONG SONG (chủ chọn). Chia thành các việc con độc lập và giao cho nhiều worker "
                 "cùng lúc (nhiều agent worker trong cùng một lượt), rồi tổng hợp.",
}

CONTINUE_MSG = ("Tài khoản Claude trước đó hết hạn mức giữa chừng nên bạn được chuyển sang tài khoản khác. "
                "Kiểm tra lại tình trạng task (status, plan.md, log.txt, results/ — có worker có thể đã xong hoặc bị dừng) "
                "rồi LÀM TIẾP phần còn dở. Không làm lại việc đã xong.")
RETRY_MSG = ("Hạn mức đã được làm mới. Kiểm tra lại tình trạng task (status, plan.md, log.txt, results/) "
             "rồi LÀM TIẾP phần còn dở. Không làm lại việc đã xong.")


# ---------------------------------------------------------------- cấu hình

def conf():
    d = kv(CONF)
    return {"model": d.get("model", ""), "allow": d.get("allow", "").split()}


def conf_rows(path):
    rows = []
    for line in (read(path) or "").splitlines():
        line = line.split("#", 1)[0]
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 3 and cells[0]:
            rows.append(cells + [""] * (5 - len(cells)))
    return rows


def resolve_home(h):
    if h in ("", "default"):
        return ""
    return os.path.expanduser(h)


def claude_accounts():
    acc = [{"name": r[0], "home": resolve_home(r[2])} for r in conf_rows(WORKERS) if r[1] == "claude"]
    return acc or [{"name": "claude", "home": ""}]


def tier_spec(role, size):
    col = {"nho": 1, "vua": 2, "lon": 3}.get(size)
    if not col:
        return ""
    for r in conf_rows(MODELS):
        if r[0] == role and len(r) > col and r[col] not in ("", "-"):
            return r[col]
    return ""


def manager_models():
    return {s: tier_spec("quan-ly", s) or "mặc định" for s in SIZES}


def norm_size(s):
    s = (s or "").strip().lower()
    return {"nhỏ": "nho", "small": "nho", "vừa": "vua", "medium": "vua", "lớn": "lon", "large": "lon"}.get(s, s) \
        if s else ""


# ---------------------------------------------------------------- file trạng thái của phiên

def mdir(tid):
    return os.path.join(TASKS, tid, "manager")


def get(tid, name):
    return (read(os.path.join(mdir(tid), name)) or "").strip()


def put(tid, name, value):
    os.makedirs(mdir(tid), exist_ok=True)
    p = os.path.join(mdir(tid), name)
    if value is None:
        try:
            os.remove(p)
        except OSError:
            pass
        return
    with open(p, "w", encoding="utf-8") as f:
        f.write(str(value) + "\n")


def append_event(tid, kind, text):
    os.makedirs(mdir(tid), exist_ok=True)
    with open(os.path.join(mdir(tid), "stream.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": kind, "text": text, "ts": int(time.time())}, ensure_ascii=False) + "\n")


def log_line(tid, text):
    with open(os.path.join(TASKS, tid, "log.txt"), "a", encoding="utf-8") as f:
        f.write("%s quan-ly %s\n" % (time.strftime("%H:%M:%S"), text))


def progress(tid, step, note):
    subprocess.run([os.path.join(ROOT, "bin", "progress"), os.path.join(TASKS, tid), step, note],
                   capture_output=True)


def set_size(tid, size):
    size = norm_size(size)
    if size not in SIZES:
        raise RuntimeError("cỡ không hợp lệ: %s" % size)
    put(tid, "size", size)
    put(tid, "model", tier_spec("quan-ly", size) or conf()["model"] or None)


def rules_for(tid):
    size = get(tid, "size") or "vua"
    split = get(tid, "split") or "auto"
    who = get(tid, "assignee")
    assignee = ("AI LÀM VIỆC: chủ chỉ định %s. Giao mọi việc con cho đúng worker này: bin/ask %s ... "
                "(nếu nó hết hạn mức, bin/ask tự chuyển sang tài khoản khác cùng công cụ)." % (who, who)) if who else \
               "AI LÀM VIỆC: bạn tự chọn worker phù hợp (xem bin/workers), ưu tiên worker đang rảnh."
    return WEB_RULES.format(task=os.path.join(TASKS, tid), split=SPLIT_RULES.get(split, SPLIT_RULES["auto"]),
                            assignee=assignee,
                            size="%s (task nhỏ thì cả quản lý lẫn worker dùng model nhỏ)" % SIZES.get(size, size))


SPLIT_TXT = {"auto": "quản lý tự chọn cách giao", "mot": "một worker", "song-song": "song song"}


def worker_names():
    return [r[0] for r in conf_rows(WORKERS)]


def worker_busy(name):
    """Worker đang làm việc ở task nào không (bin/ask đang chạy với tên đó)."""
    for t in tracker.task_ids():
        for r in tracker.running_workers(os.path.join(TASKS, t)):
            if r.get("worker") == name:
                return t
    return ""


def start_or_queue(tid, prompt, reaper=False):
    """Bắt đầu lượt đầu; nếu chủ chỉ định một AI đang bận thì để task pending, tự chạy khi AI đó rảnh."""
    who = get(tid, "assignee")
    busy = worker_busy(who) if who else ""
    if busy:
        with open(os.path.join(mdir(tid), "queued.txt"), "w", encoding="utf-8") as f:
            f.write(prompt)
        put(tid, "pending", "Đang chờ %s rảnh (đang làm task khác) — sẽ tự bắt đầu." % who)
        append_event(tid, "pentagon_event", "%s đang bận ở task khác → task này chờ (pending), tự bắt đầu khi %s rảnh."
                     % (who, who))
        return 0
    return start_turn(tid, prompt, reaper=reaper)


def check_queue():
    """Gọi định kỳ từ bin/dashboard: task pending vì AI được chỉ định đang bận → chạy khi AI đó rảnh."""
    for tid in tracker.task_ids():
        qf = os.path.join(mdir(tid), "queued.txt")
        if not os.path.exists(qf):
            continue
        who = get(tid, "assignee")
        if who and worker_busy(who):
            continue
        prompt = read(qf) or ""
        os.remove(qf)
        put(tid, "pending", None)
        append_event(tid, "pentagon_event", "%s đã rảnh → bắt đầu task." % (who or "AI"))
        try:
            start_turn(tid, prompt, reaper=True)
        except RuntimeError as e:
            append_event(tid, "pentagon_event", "Không bắt đầu được: %s" % e)


# ---------------------------------------------------------------- phân loại cỡ task

CLASSIFY = """Phân loại độ lớn của task dưới đây để chọn model AI. Trả lời đúng MỘT từ: nho, vua hoặc lon.
- nho: việc ngắn và rõ ràng, 1-2 bước: viết 1 hàm/đoạn văn ngắn, trả lời câu hỏi, sửa 1 chỗ, dịch, tóm tắt ngắn.
- vua: vài việc con, cần lập kế hoạch nhưng không quá phức tạp.
- lon: dài hoặc mơ hồ, nhiều phần, cần suy luận sâu, thiết kế/kiến trúc, nhiều file, review kỹ.
<task>
%s
</task>"""


def classify_size(text):
    """Dùng model nhỏ (haiku) để đoán cỡ task. Lỗi thì trả 'vua'."""
    wd = os.path.join(os.environ.get("ORCH_DATA") or os.path.expanduser("~/.pentagon"), "workspace")
    os.makedirs(wd, exist_ok=True)
    model = tier_spec("claude", "nho").split("@")[0] or "haiku"
    for acc in claude_accounts():
        env = dict(os.environ)
        if acc["home"]:
            env["CLAUDE_CONFIG_DIR"] = acc["home"]
        try:
            r = subprocess.run(["claude", "-p", "--model", model, "--output-format", "text"],
                               input=CLASSIFY % text[:6000], capture_output=True, text=True, timeout=120,
                               cwd=wd, env=env)
        except (OSError, subprocess.TimeoutExpired):
            continue
        m = re.search(r"\b(nho|vua|lon|nhỏ|vừa|lớn)\b", r.stdout.lower())
        if r.returncode == 0 and m:
            return norm_size(m.group(1))
        if not LIMIT_RE.search(r.stdout + r.stderr):
            break
    return "vua"


# ---------------------------------------------------------------- chạy một lượt

def start_turn(tid, message, owner_text=None, reaper=False):
    """Bắt đầu một lượt của quản lý ở nền (qua tiến trình _run). Trả về pid. Lỗi thì raise RuntimeError."""
    tdir = os.path.join(TASKS, tid)
    if not os.path.isdir(tdir):
        raise RuntimeError("không có task %s" % tid)
    info = tracker.manager_info(tdir)
    if info["running"]:
        raise RuntimeError("quản lý đang làm, chờ xong lượt này hoặc bấm Dừng")
    if not get(tid, "session"):
        put(tid, "session", str(uuid.uuid4()))
    put(tid, "retry_at", None)
    if owner_text is not None:
        append_event(tid, "pentagon_owner", owner_text)
    d = mdir(tid)
    inp = os.path.join(d, "input-%d.txt" % int(time.time() * 1000))
    with open(inp, "w", encoding="utf-8") as f:
        f.write(message)
    pid = spawn_detached([sys.executable, os.path.join(ROOT, "bin", "tracker.py"), "manager", "_run", tid, inp],
                         os.path.join(d, "stderr.log"))
    with open(os.path.join(d, "pid"), "w") as f:
        f.write("pid=%d\nstarted=%d\n" % (pid, int(time.time())))
    return pid


def spawn_detached(cmd, log_path):
    """Chạy tiến trình tách hẳn khỏi tiến trình gọi (fork 2 lần + setsid): tắt/khởi động lại bin/dashboard hay đóng
    terminal không làm chết AI quản lý đang chạy. Trả về pid của tiến trình đó."""
    r, w = os.pipe()
    first = os.fork()
    if first == 0:  # con thứ nhất: tạo session mới, fork tiếp rồi thoát ngay
        try:
            os.close(r)
            os.setsid()
            second = os.fork()
            if second == 0:  # cháu: thành con của launchd/init, không còn thuộc cây tiến trình của dashboard
                os.close(w)
                fd_in = os.open(os.devnull, os.O_RDONLY)
                fd_log = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
                os.dup2(fd_in, 0)
                os.dup2(fd_log, 1)
                os.dup2(fd_log, 2)
                os.chdir(ROOT)
                try:
                    os.execvp(cmd[0], cmd)
                finally:
                    os._exit(127)
            os.write(w, str(second).encode())
        finally:
            os._exit(0)
    os.close(w)
    data = b""
    while True:
        chunk = os.read(r, 64)
        if not chunk:
            break
        data += chunk
    os.close(r)
    os.waitpid(first, 0)
    if not data.strip().isdigit():
        raise RuntimeError("không chạy được quản lý")
    return int(data.strip())


def project_dir(home):
    base = home or os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    return os.path.join(base, "projects", re.sub(r"[^A-Za-z0-9]", "-", ROOT))


def copy_session(sid, src_home, dst_home):
    """Chép lịch sử phiên sang thư mục của tài khoản khác để --resume được ở đó."""
    src, dst = project_dir(src_home), project_dir(dst_home)
    f = os.path.join(src, sid + ".jsonl")
    if not os.path.isfile(f):
        return False
    try:
        os.makedirs(dst, exist_ok=True)
        shutil.copy2(f, os.path.join(dst, sid + ".jsonl"))
        if os.path.isdir(os.path.join(src, sid)):
            shutil.copytree(os.path.join(src, sid), os.path.join(dst, sid), dirs_exist_ok=True)
        return True
    except OSError:
        return False


def session_started(tid, home=None):
    """Phiên đã thật sự bắt đầu chưa (lượt sau phải --resume). Task tạo bằng bản cũ không có file begun:
    nhận ra qua lịch sử phiên trong thư mục tài khoản, hoặc sự kiện init trong stream.jsonl."""
    if os.path.exists(os.path.join(mdir(tid), "begun")):
        return True
    sid = get(tid, "session")
    if not sid:
        return False
    homes = [home] if home is not None else [a["home"] for a in claude_accounts()]
    if any(os.path.isfile(os.path.join(project_dir(h), sid + ".jsonl")) for h in homes):
        put(tid, "begun", "1")
        return True
    return False


def scan_limit(stream_path, offset, err_path, err_offset):
    """Xem phần stream mới của lượt vừa chạy: (hết hạn mức?, giờ làm mới hạn mức, đã bắt đầu phiên?)"""
    limited, reset_at, begun = False, 0, False
    try:
        with open(stream_path, encoding="utf-8", errors="replace") as f:
            f.seek(offset)
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                t = e.get("type")
                if t == "system" and e.get("subtype") == "init":
                    begun = True
                elif t == "rate_limit_event":
                    info = e.get("rate_limit_info") or {}
                    if info.get("status") not in (None, "allowed", "allowed_warning"):
                        limited = True
                        reset_at = int(info.get("resetsAt") or 0)
                elif t == "result":
                    if e.get("is_error") and (e.get("api_error_status") == 429 or
                                              LIMIT_RE.search(str(e.get("result") or ""))):
                        limited = True
                    elif not e.get("is_error"):
                        limited = False  # lượt xong bình thường
                elif t == "assistant" and LIMIT_RE.search(json.dumps(e.get("message", {}).get("content", ""))[:400]) \
                        and len(json.dumps(e.get("message", {}).get("content", ""))) < 400:
                    limited = True  # câu báo "You've hit your limit" ngắn thay cho câu trả lời
    except OSError:
        pass
    try:
        with open(err_path, encoding="utf-8", errors="replace") as f:
            f.seek(err_offset)
            if LIMIT_RE.search(f.read()):
                limited = True
    except OSError:
        pass
    return limited, reset_at, begun


def run_turn(tid, inp):
    """Tiến trình nền của một lượt: chạy claude, hết hạn mức thì chuyển tài khoản và làm tiếp."""
    d = mdir(tid)
    stream, errp = os.path.join(d, "stream.jsonl"), os.path.join(d, "stderr.log")
    message = read(inp) or ""
    accounts = claude_accounts()
    names = [a["name"] for a in accounts]
    idx = names.index(get(tid, "account")) if get(tid, "account") in names else 0
    tried = set()
    turn_start = time.time()
    c = conf()
    while True:
        acc = accounts[idx]
        put(tid, "account", acc["name"])
        sid = get(tid, "session")
        spec = get(tid, "model") or c["model"]
        cmd = ["claude", "-p", "--output-format", "stream-json", "--verbose",
               "--permission-mode", "acceptEdits", "--append-system-prompt", rules_for(tid),
               "--disallowedTools", "Monitor", "ScheduleWakeup", "CronCreate", "RemoteTrigger",
               "--allowedTools"] + BASE_TOOLS + c["allow"]
        if spec:
            cmd += ["--model", spec.split("@")[0]]
            if "@" in spec:
                cmd += ["--effort", spec.split("@", 1)[1]]
        cmd += (["--resume", sid] if session_started(tid, acc["home"]) else ["--session-id", sid])
        env = dict(os.environ)
        # lệnh Bash của quản lý (bin/ask) được chạy tới 10 phút, tối đa 20 phút; mặc định chỉ 2 phút là quá ngắn
        env.setdefault("BASH_DEFAULT_TIMEOUT_MS", "600000")
        env.setdefault("BASH_MAX_TIMEOUT_MS", "1200000")
        if acc["home"]:
            env["CLAUDE_CONFIG_DIR"] = acc["home"]
        offset = os.path.getsize(stream) if os.path.exists(stream) else 0
        eoff = os.path.getsize(errp) if os.path.exists(errp) else 0
        with open(stream, "a", encoding="utf-8") as out, open(errp, "a", encoding="utf-8") as err:
            p = subprocess.Popen(cmd, cwd=ROOT, stdin=subprocess.PIPE, stdout=out, stderr=err, env=env)
            try:
                p.communicate(message.encode("utf-8"))
            except KeyboardInterrupt:
                p.terminate()
                raise
        limited, reset_at, begun = scan_limit(stream, offset, errp, eoff)
        try:
            with open(errp, encoding="utf-8", errors="replace") as ef:
                ef.seek(eoff)
                in_use = "already in use" in ef.read()
        except OSError:
            in_use = False
        if in_use and not begun and not os.path.exists(os.path.join(d, "begun")):
            put(tid, "begun", "1")  # phiên đã có từ trước: chạy lại bằng --resume
            continue
        try:  # thống kê usage cho tài khoản này (web: Văn phòng làm việc)
            import pt_usage
            pt_usage.record_claude_events(acc["name"], pt_usage.read_events(stream, offset))
        except Exception:
            pass
        if begun:
            put(tid, "begun", "1")
        if not limited:
            break
        tried.add(idx)
        nxt = next((i for i in range(len(accounts)) if i not in tried), None)
        if nxt is None:
            when = reset_at if reset_at > time.time() else int(time.time()) + 1800
            put(tid, "retry_at", when + 60)
            put(tid, "account", accounts[0]["name"])
            hhmm = time.strftime("%H:%M %d/%m", time.localtime(when + 60))
            append_event(tid, "pentagon_event", "Mọi tài khoản Claude đều hết hạn mức. Phần đã làm được giữ nguyên; "
                                                "quản lý sẽ tự làm tiếp lúc %s (cần bin/dashboard đang chạy)." % hhmm)
            progress(tid, "cho", "hết hạn mức mọi tài khoản Claude — tự làm tiếp lúc %s" % hhmm)
            break
        new = accounts[nxt]
        if copy_session(sid, acc["home"], new["home"]):
            message = CONTINUE_MSG
        else:  # không chép được phiên: mở phiên mới, đọc lại task từ file
            put(tid, "session", str(uuid.uuid4()))
            put(tid, "begun", None)
            message = resume_prompt(tid, CONTINUE_MSG)
        append_event(tid, "pentagon_event", "Tài khoản %s hết hạn mức giữa chừng → chuyển sang %s, làm tiếp phần dở."
                     % (acc["name"], new["name"]))
        log_line(tid, "[ĐỔI TÀI KHOẢN] %s hết hạn mức → %s làm tiếp" % (acc["name"], new["name"]))
        idx = nxt

    # Lưới an toàn: lượt kết thúc khi worker còn chạy -> worker bị dừng giữa chừng. Cho quản lý lượt nữa để làm tiếp.
    killed = killed_workers(tid, turn_start)
    st0 = kv(os.path.join(TASKS, tid, "status"))
    auto = int(get(tid, "auto_continue") or 0)
    if killed and not get(tid, "retry_at") and st0.get("state") not in ("xong", "loi") and auto < 2:
        put(tid, "auto_continue", auto + 1)
        append_event(tid, "pentagon_event", "Lượt kết thúc khi %s còn đang làm nên bị dừng giữa chừng. Phần dở đã được giữ; "
                                            "quản lý tự làm tiếp." % ", ".join(killed))
        try:
            os.remove(os.path.join(d, "pid"))
        except OSError:
            pass
        start_turn(tid, ("Lượt trước của bạn kết thúc khi worker %s vẫn đang chạy, nên worker bị dừng giữa chừng "
                         "(xem log.txt và results/dang-do-*). Giao lại phần việc đó — chạy bin/ask TRỰC TIẾP, không chạy nền, "
                         "dặn worker làm tiếp từ phần dở — rồi tiếp tục task." % ", ".join(killed)))
        return 0
    if not killed:
        put(tid, "auto_continue", None)

    # Worker hết hạn mức ở mọi tài khoản trong lượt này và task chưa xong: hẹn tự làm tiếp sau 30 phút
    lim = os.path.join(TASKS, tid, "limited")
    st = kv(os.path.join(TASKS, tid, "status"))
    if os.path.exists(lim) and os.path.getmtime(lim) >= turn_start and not get(tid, "retry_at") \
            and st.get("state") not in ("xong", "loi"):
        when = int(time.time()) + 1800
        put(tid, "retry_at", when)
        append_event(tid, "pentagon_event", "Worker hết hạn mức ở mọi tài khoản. Quản lý sẽ tự làm tiếp lúc %s."
                     % time.strftime("%H:%M", time.localtime(when)))
    try:
        os.remove(os.path.join(d, "pid"))
    except OSError:
        pass
    return 0


def killed_workers(tid, since):
    """Worker bắt đầu trong lượt này mà không có dòng ok/FAIL nào sau đó (bị dừng không kịp ghi), hoặc ghi 'bị dừng giữa chừng'."""
    lines = (read(os.path.join(TASKS, tid, "log.txt")) or "").splitlines()
    t0 = time.strftime("%H:%M:%S", time.localtime(since))
    open_, killed = {}, []
    for i in tracker.parse_log("\n".join(lines)):
        if not i["time"] or i["time"] < t0 or i["who"] == "quan-ly":
            continue
        if i["kind"] == "start":
            open_[i["who"]] = True
        elif i["kind"] in ("ok", "fail"):
            if "bị dừng giữa chừng" in i["text"] and i["who"] not in killed:
                killed.append(i["who"])
            open_.pop(i["who"], None)
    alive = {r.get("worker") for r in tracker.running_workers(os.path.join(TASKS, tid))}
    return killed + [w for w in open_ if w not in alive and w not in killed]


def check_orphans():
    """Gọi định kỳ từ bin/dashboard: lượt của quản lý bị chết đột ngột (vd máy tắt, bị kill) — file pid còn mà tiến trình
    không còn — thì cho quản lý làm tiếp, tối đa 2 lần liên tiếp."""
    for tid in tracker.task_ids():
        pf = os.path.join(mdir(tid), "pid")
        if not os.path.exists(pf):
            continue
        st = kv(pf)
        if st.get("pid") and pid_alive(st["pid"]):
            continue
        try:
            started = int(st.get("started") or 0)
        except ValueError:
            started = 0
        if time.time() - started < 15:  # vừa mới chạy, tiến trình có thể chưa kịp lên
            continue
        os.remove(pf)
        status = kv(os.path.join(TASKS, tid, "status"))
        auto = int(get(tid, "auto_continue") or 0)
        if status.get("state") in ("xong", "loi") or auto >= 2:
            append_event(tid, "pentagon_event", "Quản lý bị dừng đột ngột. Gửi tin nhắn để quản lý làm tiếp.")
            continue
        put(tid, "auto_continue", auto + 1)
        killed = killed_workers(tid, started)
        append_event(tid, "pentagon_event", "Quản lý bị dừng đột ngột giữa lượt%s. Phần đã làm được giữ; quản lý tự làm tiếp."
                     % ((" (worker %s cũng bị dừng)" % ", ".join(killed)) if killed else ""))
        log_line(tid, "[TỰ LÀM TIẾP] quản lý bị dừng đột ngột")
        try:
            start_turn(tid, ("Lượt trước của bạn bị dừng đột ngột (tiến trình bị tắt), không phải do bạn. "
                             "Worker đang chạy lúc đó (%s) có thể đã làm xong một phần hoặc toàn bộ: kiểm tra results/, "
                             "log.txt, plan.md và các file đầu ra trước. Việc nào đã có kết quả đúng thì KHÔNG giao lại; "
                             "việc còn dở thì giao lại (chạy bin/ask trực tiếp, dặn làm tiếp phần dở). Sau đó đi tiếp các bước "
                             "còn lại của quy trình." % (", ".join(killed) or "nếu có")))
        except RuntimeError as e:
            append_event(tid, "pentagon_event", "Không tự làm tiếp được: %s" % e)


def check_retries():
    """Gọi định kỳ từ bin/dashboard: task nào đến giờ tự làm tiếp thì cho quản lý chạy lượt mới."""
    now = time.time()
    for tid in tracker.task_ids():
        rt = get(tid, "retry_at")
        if not rt:
            continue
        try:
            due = int(rt) <= now
        except ValueError:
            due = True
        st = kv(os.path.join(TASKS, tid, "status"))
        if st.get("state") in ("xong", "loi"):
            put(tid, "retry_at", None)
            continue
        if not due or tracker.manager_info(os.path.join(TASKS, tid))["running"]:
            continue
        try:
            put(tid, "account", claude_accounts()[0]["name"])
            append_event(tid, "pentagon_event", "Đến giờ hẹn: quản lý tự làm tiếp.")
            if st.get("state") == "cho":
                progress(tid, "tiep", "tự làm tiếp sau khi hết hạn mức")
            start_turn(tid, RETRY_MSG, reaper=True)
        except RuntimeError as e:
            append_event(tid, "pentagon_event", "Không tự làm tiếp được: %s" % e)


# ---------------------------------------------------------------- tạo task, nhắn, dừng

def giao_prompt(request, mode):
    tpl = read(os.path.join(ROOT, ".claude", "commands", "giao.md")) or "Chủ giao task:\n$ARGUMENTS"
    tpl = re.sub(r"^---\n.*?\n---\n", "", tpl, flags=re.S)  # bỏ phần frontmatter
    extra = {
        "duyet": "\n\nChủ muốn DUYỆT kế hoạch trước: lập kế hoạch xong thì dừng lại chờ chủ đồng ý rồi mới giao việc.",
        "lam-luon": "\n\nChủ cho phép LÀM LUÔN: không cần chờ duyệt kế hoạch, chỉ hỏi khi thật sự thiếu thông tin.",
    }.get(mode, "")
    return tpl.replace("$ARGUMENTS", request.strip()) + extra


def new_task(request, mode="tu-quyet", size="auto", split="auto", assignee=""):
    """Tạo task từ yêu cầu của chủ. Trả về (id task, prompt lượt đầu). Chưa chạy quản lý."""
    request = request.strip()
    if not request:
        raise RuntimeError("yêu cầu đang trống")
    title = re.sub(r"\s+", " ", request.splitlines()[0])[:60].strip() or "task"
    r = subprocess.run([os.path.join(ROOT, "bin", "new-task"), title], capture_output=True, text=True)
    tdir = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    if r.returncode != 0 or not os.path.isdir(tdir):
        raise RuntimeError("không tạo được task: %s" % (r.stderr.strip() or r.stdout.strip()))
    tid = os.path.basename(tdir)
    bp = os.path.join(tdir, "brief.md")
    brief = read(bp) or ""
    brief = brief.replace("## Yêu cầu gốc (nguyên văn)\n", "## Yêu cầu gốc (nguyên văn)\n\n" + request + "\n", 1)
    with open(bp, "w", encoding="utf-8") as f:
        f.write(brief)
    put(tid, "split", split if split in SPLIT_RULES else "auto")
    if assignee:
        if assignee not in worker_names():
            raise RuntimeError("không có AI tên %s" % assignee)
        put(tid, "assignee", assignee)
    if norm_size(size) in SIZES:
        set_size(tid, size)
    return tid, giao_prompt(request, mode)


def launch_new(request, mode="tu-quyet", size="auto", split="auto", background=True, assignee=""):
    """Tạo task và cho quản lý bắt đầu. size=auto: AI phân loại cỡ trước (ở luồng nền nếu background).
    assignee: AI chủ chỉ định; nếu AI đó đang bận, task pending đến khi nó rảnh."""
    if assignee and assignee not in worker_names():
        raise RuntimeError("không có AI tên %s" % assignee)
    tid, prompt = new_task(request, mode, size, split, assignee)
    append_event(tid, "pentagon_owner", request.strip())
    extra = (" · giao cho %s" % assignee) if assignee else ""
    if norm_size(size) in SIZES:
        append_event(tid, "pentagon_event", "Chủ chọn cỡ %s → quản lý dùng %s · %s%s."
                     % (SIZES[norm_size(size)], get(tid, "model") or "model mặc định",
                        SPLIT_TXT.get(get(tid, "split"), ""), extra))
        start_or_queue(tid, prompt, reaper=background)
        return tid

    def work():
        try:
            s = classify_size(request)
            set_size(tid, s)
            append_event(tid, "pentagon_event", "Quản lý phân loại: task %s → dùng model %s · %s%s."
                         % (SIZES[s], get(tid, "model") or "model mặc định", SPLIT_TXT.get(get(tid, "split"), ""), extra))
        finally:
            put(tid, "pending", None)
        start_or_queue(tid, prompt, reaper=background)

    put(tid, "pending", "Quản lý đang phân loại cỡ task để chọn model…")
    if background:
        threading.Thread(target=work, daemon=True).start()
    else:
        work()
    return tid


def resume_prompt(tid, message):
    """Tin nhắn cho phiên mới của một task đã có (tạo từ terminal, hoặc đổi tài khoản không chép được phiên)."""
    tdir = os.path.join(TASKS, tid)
    return ("Tiếp tục task ở %s (task này đã có từ trước). Đọc brief.md, plan.md, log.txt, status, "
            "final.md (nếu có) và results/ để nắm tình hình, rồi xử lý tin nhắn sau của chủ:\n\n%s") % (tdir, message)


def send(tid, message, reaper=False):
    message = message.strip()
    if not message:
        raise RuntimeError("tin nhắn đang trống")
    if get(tid, "pending"):
        raise RuntimeError("đang chuẩn bị quản lý, đợi vài giây")
    prompt = message if session_started(tid) else resume_prompt(tid, message)
    if not get(tid, "split"):
        put(tid, "split", "auto")
    pid = start_turn(tid, prompt, owner_text=message, reaper=reaper)
    st = kv(os.path.join(TASKS, tid, "status"))
    if st.get("state") == "cho":  # chủ đã trả lời: chuyển task về "đang làm"
        progress(tid, "tiep", "chủ đã trả lời")
    return pid


def descendants(pid):
    out, todo = [], [pid]
    while todo:
        p = todo.pop()
        try:
            r = subprocess.run(["pgrep", "-P", str(p)], capture_output=True, text=True)
        except OSError:
            break
        kids = [int(x) for x in r.stdout.split() if x.isdigit()]
        out += kids
        todo += kids
    return out


def kill_tree(pid):
    """Dừng một tiến trình và mọi tiến trình con của nó (claude, CLI của worker, ...)."""
    pids = [pid] + descendants(pid)
    for p in pids:
        try:
            os.kill(p, signal.SIGTERM)
        except OSError:
            pass
    time.sleep(1.5)
    for p in pids:
        if pid_alive(p):
            try:
                os.kill(p, signal.SIGKILL)
            except OSError:
                pass


def stop(tid):
    info = tracker.manager_info(os.path.join(TASKS, tid))
    put(tid, "retry_at", None)
    if not info["running"]:
        raise RuntimeError("quản lý không chạy")
    kill_tree(info["pid"])
    put(tid, "pid", None)
    append_event(tid, "pentagon_event", "Chủ đã dừng quản lý giữa chừng.")


def kill_worker(tid, pid):
    run = tracker.running_workers(os.path.join(TASKS, tid))
    hit = [r for r in run if str(r.get("pid")) == str(pid)]
    if not hit:
        raise RuntimeError("worker này không còn chạy")
    kill_tree(int(pid))
    with open(os.path.join(TASKS, tid, "log.txt"), "a", encoding="utf-8") as f:
        f.write("%s %s FAIL: chủ huỷ từ web\n" % (time.strftime("%H:%M:%S"), hit[0].get("worker", "?")))


def cancel_task(tid):
    put(tid, "retry_at", None)
    if os.path.exists(os.path.join(mdir(tid), "queued.txt")):
        os.remove(os.path.join(mdir(tid), "queued.txt"))
        put(tid, "pending", None)
    if tracker.manager_info(os.path.join(TASKS, tid))["running"]:
        stop(tid)
    for r in tracker.running_workers(os.path.join(TASKS, tid)):
        kill_tree(int(r["pid"]))
    progress(tid, "loi", "chủ huỷ task")


# ---------------------------------------------------------------- sửa / xoá / khôi phục task (CRUD trên web)

TRASH = os.path.join(TASKS, ".trash")


def _busy(tid):
    tdir = os.path.join(TASKS, tid)
    return tracker.manager_info(tdir)["running"] or bool(tracker.running_workers(tdir)) or bool(get(tid, "pending"))


def update_task(tid, title=None, brief=None):
    """Sửa tiêu đề (dòng # đầu của brief.md) và/hoặc toàn bộ nội dung brief.md."""
    bp = os.path.join(TASKS, tid, "brief.md")
    text = read(bp) or ""
    changed = []
    if brief is not None and brief != text:
        text = brief if brief.endswith("\n") else brief + "\n"
        changed.append("yêu cầu (brief.md)")
    if title is not None:
        title = re.sub(r"\s+", " ", title).strip()
        if not title:
            raise RuntimeError("tiêu đề đang trống")
        if re.search(r"^#\s+.*$", text, re.M):
            new = re.sub(r"^#\s+.*$", lambda m: "# " + title, text, count=1, flags=re.M)
        else:
            new = "# %s\n\n%s" % (title, text)
        if new != text:
            text = new
            changed.append("tiêu đề")
    if not changed:
        return False
    with open(bp, "w", encoding="utf-8") as f:
        f.write(text)
    log_line(tid, "[CHỦ SỬA] %s" % ", ".join(changed))
    if os.path.isdir(mdir(tid)):
        append_event(tid, "pentagon_event", "Chủ đã sửa %s. Quản lý sẽ đọc lại ở lượt sau." % ", ".join(changed))
    return True


def reopen(tid):
    st = kv(os.path.join(TASKS, tid, "status"))
    if st.get("state") not in ("xong", "loi"):
        raise RuntimeError("task đang mở sẵn")
    progress(tid, "tiep", "chủ mở lại task")


def delete_task(tid):
    """Chuyển task vào tasks/.trash/ (khôi phục được). Đang chạy thì dừng quản lý và worker trước."""
    if _busy(tid):
        cancel_task(tid)
    put(tid, "retry_at", None)
    os.makedirs(TRASH, exist_ok=True)
    dst = os.path.join(TRASH, tid)
    if os.path.exists(dst):
        dst += "-%d" % int(time.time())
    shutil.move(os.path.join(TASKS, tid), dst)
    with open(os.path.join(dst, ".deleted_at"), "w") as f:
        f.write(str(int(time.time())))
    return os.path.basename(dst)


def trash_list():
    out = []
    if not os.path.isdir(TRASH):
        return out
    for n in sorted(os.listdir(TRASH), reverse=True):
        d = os.path.join(TRASH, n)
        if not os.path.isdir(d):
            continue
        m = re.search(r"^#\s+(.+)$", read(os.path.join(d, "brief.md")) or "", re.M)
        try:
            at = int((read(os.path.join(d, ".deleted_at")) or "0").strip())
        except ValueError:
            at = int(os.path.getmtime(d))
        out.append({"trash_id": n, "title": m.group(1).strip() if m else n, "deleted_at": at,
                    "created": tracker.created_of(n)})
    return out


def _trash_path(trash_id):
    if not trash_id or "/" in trash_id or trash_id.startswith("."):
        raise RuntimeError("không có trong thùng rác")
    p = os.path.join(TRASH, trash_id)
    if not os.path.isdir(p):
        raise RuntimeError("không có trong thùng rác")
    return p


def restore_task(trash_id):
    src = _trash_path(trash_id)
    tid = re.sub(r"-\d{10}$", "", trash_id) if re.search(r"^\d{8}-\d{4}-", trash_id) else trash_id
    if os.path.exists(os.path.join(TASKS, tid)):
        tid = trash_id
    if os.path.exists(os.path.join(TASKS, tid)):
        raise RuntimeError("đã có task trùng tên %s" % tid)
    shutil.move(src, os.path.join(TASKS, tid))
    try:
        os.remove(os.path.join(TASKS, tid, ".deleted_at"))
    except OSError:
        pass
    return tid


def purge_task(trash_id):
    """Xoá vĩnh viễn một task trong thùng rác."""
    shutil.rmtree(_trash_path(trash_id))


# ---------------------------------------------------------------- đọc hội thoại

_CHAT_CACHE = {}


def _tool_text(name, inp):
    inp = inp or {}
    rel = lambda p: os.path.relpath(p, ROOT) if isinstance(p, str) and p.startswith(ROOT) else p
    if name == "Bash":
        return "$ " + str(inp.get("command", ""))[:300]
    if name in ("Agent", "Task"):
        return "giao cho agent %s: %s" % (inp.get("subagent_type", ""), inp.get("description", ""))
    if name in ("Write", "Edit", "MultiEdit"):
        return "ghi file %s" % rel(inp.get("file_path", ""))
    if name == "Read":
        return "đọc %s" % rel(inp.get("file_path", ""))
    if name in ("Glob", "Grep"):
        return "tìm %s" % (inp.get("pattern", ""))
    if name == "TodoWrite":
        return "cập nhật danh sách việc"
    return name


def chat(tid):
    """Hội thoại giữa chủ và quản lý, rút gọn cho giao diện."""
    p = os.path.join(mdir(tid), "stream.jsonl")
    try:
        stt = os.stat(p)
    except OSError:
        return []
    key = (stt.st_size, stt.st_mtime)
    hit = _CHAT_CACHE.get(p)
    if hit and hit[0] == key:
        return hit[1]
    items = []
    with open(p, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            t = e.get("type")
            if t == "pentagon_owner":
                items.append({"role": "owner", "text": e.get("text", ""), "ts": e.get("ts")})
            elif t == "pentagon_event":
                items.append({"role": "event", "text": e.get("text", ""), "ts": e.get("ts")})
            elif t == "assistant" and not e.get("parent_tool_use_id"):
                for blk in (e.get("message") or {}).get("content") or []:
                    if blk.get("type") == "text" and blk.get("text", "").strip():
                        items.append({"role": "manager", "text": blk["text"]})
                    elif blk.get("type") == "tool_use":
                        items.append({"role": "tool", "text": _tool_text(blk.get("name"), blk.get("input"))})
            elif t == "result":
                secs = int((e.get("duration_ms") or 0) / 1000)
                if e.get("is_error") and LIMIT_RE.search(str(e.get("result") or "")):
                    items.append({"role": "event", "text": "Tài khoản hết hạn mức: %s" % str(e.get("result") or "")[:200]})
                elif e.get("is_error") or e.get("subtype") != "success":
                    items.append({"role": "error", "text": "Lượt bị lỗi (%s): %s" % (
                        e.get("subtype", ""), str(e.get("result") or "")[:500])})
                else:
                    items.append({"role": "end", "text": "Hết lượt · %s" % tracker.dur(secs)})
    _CHAT_CACHE[p] = (key, items)
    return items


def stderr_tail(tid):
    t = read(os.path.join(mdir(tid), "stderr.log")) or ""
    return t[-1500:]


# ---------------------------------------------------------------- dòng lệnh

def resolve_or_die(arg):
    tid = tracker.resolve_task(arg)
    if not tid:
        print("Không tìm thấy task: %s" % arg, file=sys.stderr)
        sys.exit(1)
    return tid


def cmd_manager(argv):
    usage = __doc__.split("Dòng lệnh (bin/manager):")[1]
    if not argv or argv[0] in ("-h", "--help"):
        print(usage)
        return 0
    try:
        if argv[0] == "_run" and len(argv) == 3:  # tiến trình nền nội bộ
            return run_turn(argv[1], argv[2])
        if argv[0] == "new":
            mode, size, split, who, rest = "tu-quyet", "auto", "auto", "", argv[1:]
            while rest and rest[0].startswith("--"):
                a = rest.pop(0)
                if a in ("--duyet", "--lam-luon"):
                    mode = a[2:]
                elif a == "--song-song":
                    split = "song-song"
                elif a == "--mot":
                    split = "mot"
                elif a == "--ai" and rest:
                    who = rest.pop(0)
                elif a == "--co" and rest:
                    size = rest.pop(0)
                else:
                    print(usage, file=sys.stderr)
                    return 1
            req = " ".join(rest) if rest else sys.stdin.read()
            tid = launch_new(req, mode, size, split, background=False, assignee=who)
            print("Đã tạo task %s (cỡ %s, model quản lý %s). Theo dõi: bin/status %s"
                  % (tid, SIZES.get(get(tid, "size"), "?"), get(tid, "model") or "mặc định", tid))
        elif argv[0] == "send" and len(argv) >= 2:
            tid = resolve_or_die(argv[1])
            msg = " ".join(argv[2:]) if len(argv) > 2 else sys.stdin.read()
            pid = send(tid, msg)
            print("Đã gửi cho quản lý của %s (pid %d)" % (tid, pid))
        elif argv[0] == "stop" and len(argv) >= 2:
            tid = resolve_or_die(argv[1])
            stop(tid)
            print("Đã dừng quản lý của %s" % tid)
        elif argv[0] == "size" and len(argv) >= 3:
            tid = resolve_or_die(argv[1])
            set_size(tid, argv[2])
            why = " ".join(argv[3:])
            append_event(tid, "pentagon_event", "Quản lý đổi cỡ task: %s → model %s từ lượt sau.%s"
                         % (SIZES[get(tid, "size")], get(tid, "model") or "mặc định", (" Lý do: " + why) if why else ""))
            print("Cỡ task %s: %s (model %s từ lượt sau)" % (tid, SIZES[get(tid, "size")], get(tid, "model") or "mặc định"))
        elif argv[0] == "kill-worker" and len(argv) >= 3:
            tid = resolve_or_die(argv[1])
            kill_worker(tid, argv[2])
            print("Đã huỷ worker pid %s" % argv[2])
        else:
            print(usage, file=sys.stderr)
            return 1
    except RuntimeError as e:
        print("Lỗi: %s" % e, file=sys.stderr)
        return 1
    return 0
