"""Quản lý tài khoản AI (config/workers.conf) cho trang Tài khoản trên web: thêm, sửa, bật/tắt, đổi thứ tự,
xoá, và đăng nhập ngay trên web (chạy lệnh đăng nhập của CLI trong một terminal ảo).

workers.conf giữ nguyên định dạng cũ: mỗi dòng "tên | công cụ | thư mục | mô tả | model".
Tài khoản bị TẮT được ghi thành dòng chú thích "#tắt: tên | ...", nên bin/ask bỏ qua nhưng vẫn khôi phục được.
Thứ tự dòng = thứ tự ưu tiên khi xoay vòng tài khoản.
"""
import fcntl
import json
import os
import pty
import re
import select
import shutil
import signal
import subprocess
import struct
import termios
import threading
import time

from tracker import ROOT

CONF = os.environ.get("ORCH_CONF") or os.path.join(ROOT, "config", "workers.conf")
DATA = os.environ.get("ORCH_DATA") or os.path.expanduser("~/.pentagon")
TOOLS = ("claude", "codex", "gemini")
OFF = "#tắt: "
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,29}$")
MODEL_RE = re.compile(r"^[A-Za-z0-9._:@/-]{0,60}$")
LOCK = threading.Lock()


def _lines():
    try:
        with open(CONF, encoding="utf-8") as f:
            return f.read().splitlines()
    except OSError:
        return []


def _write(lines):
    tmp = CONF + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip("\n") + "\n")
    os.replace(tmp, CONF)


def _parse(line):
    """(bật?, [tên, công cụ, thư mục, mô tả, model]) hoặc None nếu không phải dòng tài khoản."""
    enabled = True
    body = line
    if line.startswith(OFF):
        enabled, body = False, line[len(OFF):]
    elif line.lstrip().startswith("#"):
        return None
    cells = [c.strip() for c in body.split("|")]
    if len(cells) < 3 or not cells[0] or cells[1] not in TOOLS:
        return None
    cells = (cells + [""] * 5)[:5]
    return enabled, cells


def _fmt(cells, enabled=True):
    name, tool, home, desc, model = cells
    line = "%-12s | %-6s | %s | %s | %s" % (name, tool, home, desc, model)
    return (OFF if not enabled else "") + line.rstrip()


def accounts():
    out, prio = [], {}
    for i, line in enumerate(_lines()):
        p = _parse(line)
        if not p:
            continue
        enabled, (name, tool, home, desc, model) = p
        if enabled:  # thứ tự ưu tiên tính trong từng phòng ban (công cụ)
            prio[tool] = prio.get(tool, 0) + 1
        out.append({"name": name, "tool": tool, "home": home, "desc": desc, "model": model,
                    "enabled": enabled, "priority": prio.get(tool, 0) if enabled else 0, "line": i,
                    "default": home in ("", "default")})
    return out


def _find(lines, name):
    for i, line in enumerate(lines):
        p = _parse(line)
        if p and p[1][0] == name:
            return i, p
    return -1, None


def _clean_text(s, field):
    s = str(s or "").strip()
    if "|" in s or "\n" in s or "#" in s:
        raise RuntimeError("%s không được chứa ký tự |, # hoặc xuống dòng" % field)
    return s[:80]


def add(name, tool, desc="", model=""):
    name = str(name or "").strip().lower()
    if not NAME_RE.match(name):
        raise RuntimeError("tên chỉ gồm chữ thường, số, dấu - (vd claude-3)")
    if tool not in TOOLS:
        raise RuntimeError("công cụ phải là claude, codex hoặc gemini")
    desc, model = _clean_text(desc, "Mô tả"), _clean_text(model, "Model")
    if not MODEL_RE.match(model):
        raise RuntimeError("model không hợp lệ")
    with LOCK:
        lines = _lines()
        if _find(lines, name)[0] >= 0:
            raise RuntimeError("đã có tài khoản tên %s" % name)
        home = "~/.pentagon/accounts/%s" % name
        os.makedirs(os.path.join(DATA, "accounts", name), exist_ok=True)
        # chèn sau dòng tài khoản cuối cùng để giữ phần chú thích mẫu ở cuối file
        last = max([i for i, l in enumerate(lines) if _parse(l)] or [len(lines) - 1])
        lines.insert(last + 1, _fmt([name, tool, home, desc or "Tài khoản %s" % name, model]))
        _write(lines)
    return name


def update(name, desc=None, model=None):
    with LOCK:
        lines = _lines()
        i, p = _find(lines, name)
        if i < 0:
            raise RuntimeError("không có tài khoản %s" % name)
        enabled, cells = p
        if desc is not None:
            cells[3] = _clean_text(desc, "Mô tả")
        if model is not None:
            m = _clean_text(model, "Model")
            if not MODEL_RE.match(m):
                raise RuntimeError("model không hợp lệ")
            cells[4] = m
        lines[i] = _fmt(cells, enabled)
        _write(lines)


def set_enabled(name, enabled):
    with LOCK:
        lines = _lines()
        i, p = _find(lines, name)
        if i < 0:
            raise RuntimeError("không có tài khoản %s" % name)
        if not enabled and len([a for a in accounts() if a["enabled"] and a["name"] != name]) == 0:
            raise RuntimeError("phải còn ít nhất một tài khoản đang bật")
        lines[i] = _fmt(p[1], enabled)
        _write(lines)


def move(name, direction):
    """Đổi thứ tự ưu tiên: đổi chỗ với tài khoản liền trước/sau trong file."""
    with LOCK:
        lines = _lines()
        tool = next((p[1][1] for p in map(_parse, lines) if p and p[1][0] == name), None)
        idx = [i for i, l in enumerate(lines) if _parse(l) and _parse(l)[1][1] == tool]
        names = [_parse(lines[i])[1][0] for i in idx]
        if name not in names:
            raise RuntimeError("không có tài khoản %s" % name)
        k = names.index(name)
        j = k - 1 if direction == "up" else k + 1
        if j < 0 or j >= len(idx):
            return
        a, b = idx[k], idx[j]
        lines[a], lines[b] = lines[b], lines[a]
        _write(lines)


def remove(name, forget_login=False):
    """Bỏ tài khoản khỏi danh sách. forget_login: xoá luôn thư mục đăng nhập riêng của nó (~/.pentagon/accounts/<tên>)."""
    with LOCK:
        lines = _lines()
        i, p = _find(lines, name)
        if i < 0:
            raise RuntimeError("không có tài khoản %s" % name)
        if p[0] and len([a for a in accounts() if a["enabled"] and a["name"] != name]) == 0:
            raise RuntimeError("phải còn ít nhất một tài khoản đang bật")
        home = p[1][2]
        del lines[i]
        _write(lines)
    if forget_login and home not in ("", "default"):
        d = os.path.realpath(os.path.expanduser(home))
        base = os.path.realpath(os.path.join(DATA, "accounts"))
        if d.startswith(base + os.sep) and os.path.isdir(d):  # chỉ xoá thư mục do Pentagon tạo
            shutil.rmtree(d)


# ---------------------------------------------------------------- đăng nhập trên web

LOGINS = {}   # tên -> {"pid", "fd", "out", "started", "done", "rc"}
ANSI = re.compile(r"\x1b\[[0-9;?<>=]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[()][A-Za-z0-9]|\r")
URL_RE = re.compile(r"https://\S+")


def _home_of(name):
    for a in accounts():
        if a["name"] == name:
            h = a["home"]
            return a, ("" if h in ("", "default") else os.path.expanduser(h))
    raise RuntimeError("không có tài khoản %s" % name)


def login_start(name):
    a, home = _home_of(name)
    cur = LOGINS.get(name)
    if cur and not cur["done"]:
        return
    env = dict(os.environ)
    cwd, creds = ROOT, None
    if home:
        os.makedirs(home, exist_ok=True)
    if a["tool"] == "gemini":
        # Gemini không có lệnh login riêng: mở giao diện tương tác của nó, chọn sẵn "Đăng nhập bằng Google",
        # chế độ không tự mở trình duyệt -> nó in link đăng nhập và chờ dán mã. Có file oauth_creds.json là xong.
        base = os.path.join(home or os.path.expanduser("~"), ".gemini")
        _gemini_select_google_login(base)
        creds = os.path.join(base, "oauth_creds.json")
        if os.path.exists(creds):
            os.rename(creds, creds + ".cu")  # đăng nhập lại: giữ bản cũ, khôi phục nếu huỷ giữa chừng
        env.update(GOOGLE_GENAI_USE_GCA="true", NO_BROWSER="true", GEMINI_CLI_TRUST_WORKSPACE="true",
                   TERM="xterm-256color")
        if home:
            env["GEMINI_CLI_HOME"] = home
        cwd = home or os.path.join(DATA, "workspace")
        os.makedirs(cwd, exist_ok=True)
        cmd = ["gemini"]
    else:
        cmd = ["claude", "auth", "login"] if a["tool"] == "claude" else ["codex", "login"]
        if home:
            env["CLAUDE_CONFIG_DIR" if a["tool"] == "claude" else "CODEX_HOME"] = home
    master, slave = pty.openpty()  # terminal ảo: CLI tưởng đang chạy trong terminal thật
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 50, 1000, 0, 0))  # rộng để link không bị xuống dòng
    try:
        p = subprocess.Popen(cmd, stdin=slave, stdout=slave, stderr=slave, env=env, cwd=cwd,
                             start_new_session=True, close_fds=True)
    finally:
        os.close(slave)
    st = {"pid": p.pid, "fd": master, "out": "", "started": int(time.time()), "done": False, "rc": None,
          "proc": p, "tool": a["tool"], "creds": creds}
    LOGINS[name] = st

    def pump():
        while True:
            try:
                r, _, _ = select.select([master], [], [], 1.0)
                if r:
                    data = os.read(master, 4096)
                    if not data:
                        break
                    st["out"] = (st["out"] + data.decode("utf-8", "replace"))[-8000:]
                elif p.poll() is not None:
                    break
                if creds and os.path.exists(creds):  # Gemini đã lưu đăng nhập: tắt giao diện của nó
                    st["rc"] = 0
                    time.sleep(1)
                    _stop_group(p)
                    break
            except OSError:
                break
        try:
            rc = p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _stop_group(p)
            rc = p.poll()
        if st["rc"] is None:
            st["rc"] = rc
        if creds:  # bỏ bản cũ nếu đăng nhập mới thành công, khôi phục nếu không
            old = creds + ".cu"
            if os.path.exists(old):
                if os.path.exists(creds):
                    os.remove(old)
                else:
                    os.rename(old, creds)
        st["done"] = True
        try:
            os.close(master)
        except OSError:
            pass
    threading.Thread(target=pump, daemon=True).start()


def _stop_group(p):
    """Tắt CLI đăng nhập: thử tắt nhẹ, quá 3 giây thì buộc tắt (giao diện của Gemini bỏ qua tín hiệu tắt nhẹ)."""
    for sig, wait in ((signal.SIGTERM, 3), (signal.SIGKILL, 3)):
        try:
            os.killpg(p.pid, sig)
        except OSError:
            pass
        try:
            p.wait(timeout=wait)
            return
        except subprocess.TimeoutExpired:
            continue


def _gemini_select_google_login(base):
    """Ghi vào settings.json của Gemini: kiểu đăng nhập = Google (giữ nguyên các cài đặt khác)."""
    os.makedirs(base, exist_ok=True)
    p = os.path.join(base, "settings.json")
    try:
        with open(p, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        cfg = {}
    auth = cfg.setdefault("security", {}).setdefault("auth", {})
    if auth.get("selectedType") != "oauth-personal":
        auth["selectedType"] = "oauth-personal"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)


def login_status(name):
    st = LOGINS.get(name)
    if not st:
        return {"active": False}
    text = ANSI.sub("", st["out"])
    lines = []
    for l in (x.strip() for x in text.split("\n")):
        if l and l not in lines[-20:]:
            lines.append(l)
    text = "\n".join(lines)
    urls = [u for u in URL_RE.findall(text) if "oauth" in u or "accounts.google" in u or "auth" in u] or URL_RE.findall(text)
    return {"active": True, "done": st["done"], "rc": st["rc"], "text": text[-3000:],
            "url": urls[-1] if urls else "", "wants_code": "code" in text.lower() and not st["done"],
            "started": st["started"]}


def login_send(name, code):
    st = LOGINS.get(name)
    if not st or st["done"]:
        raise RuntimeError("không có phiên đăng nhập đang chờ")
    code = str(code or "").strip()
    if not code or "\n" in code or len(code) > 500:
        raise RuntimeError("mã không hợp lệ")
    os.write(st["fd"], (code + "\r").encode("utf-8"))


def login_cancel(name):
    st = LOGINS.get(name)
    if st and not st["done"]:
        threading.Thread(target=_stop_group, args=(st["proc"],), daemon=True).start()


def logout(name):
    a, home = _home_of(name)
    env = dict(os.environ)
    if home:
        env["CLAUDE_CONFIG_DIR" if a["tool"] == "claude" else "CODEX_HOME"] = home
    if a["tool"] == "claude":
        subprocess.run(["claude", "auth", "logout"], env=env, capture_output=True, timeout=60)
    elif a["tool"] == "codex":
        subprocess.run(["codex", "logout"], env=env, capture_output=True, timeout=60)
    else:  # Gemini: xoá thông tin đăng nhập đã lưu
        base = os.path.join(home or os.path.expanduser("~"), ".gemini")
        for f in ("oauth_creds.json", "google_accounts.json"):
            try:
                os.remove(os.path.join(base, f))
            except OSError:
                pass
