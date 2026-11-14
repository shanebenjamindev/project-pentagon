"""Web app của Pentagon (bin/dashboard): xem tiến độ và thao tác — giao task, trò chuyện với quản lý,
duyệt, dừng, huỷ worker. Chỉ nghe trên 127.0.0.1.

Bảo vệ: chỉ nhận Host là 127.0.0.1/localhost (chống DNS rebinding); mọi thao tác (POST) phải có
header X-Pentagon và Content-Type JSON, nên trang web lạ mở trong trình duyệt không gửi lệnh được (CORS chặn).
Cookie không gắn theo cổng; dịch vụ khác trên cùng host có thể nhận cookie phiên.
"""
import json
import hashlib
import hmac
import os
import secrets
import subprocess
import sys
import threading
import time
import getpass
import mimetypes
import base64
import binascii
import datetime
from urllib.parse import unquote
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

import pt_manager
import pt_notify
import pt_followup
import tracker
from tracker import ROOT, TASKS, read, summary, task_ids

PAGE = os.path.join(ROOT, "web", "index.html")
LOGIN_PAGE = os.path.join(ROOT, "web", "login.html")
AUTH_FILE = os.path.join(ROOT, "config", "auth.conf")
STATIC = {"logo.png", "mark.png", "favicon.png", "favicon-32.png", "apple-touch-icon.png", "favicon.ico",
          "theme-sieu-anh-hung.css", "theme-apple.css"}
WORKERS = {"items": [], "checked": 0}
PORT = [8765]
POST_LIMIT = 200000                     # request POST thường / chưa đăng nhập
POST_LIMIT_BIG = 56 * 1024 * 1024       # /api/giao, /api/send có ảnh (8 ảnh × 5 MB, base64 ≈ +33%)


def human_size(n):
    return "%.1f MB" % (n / 1048576) if n >= 1048576 else "%d KB" % max(1, round(n / 1024))


# ---------------- phát hiện server đang chạy code cũ (file .py đổi sau khi khởi động)
CODE_FILES = ("pt_web.py", "pt_manager.py", "pt_notify.py", "pt_followup.py", "tracker.py",
              "pt_accounts.py", "pt_usage.py")


def code_mtimes():
    out = {}
    for name in CODE_FILES:
        try:
            out[name] = os.path.getmtime(os.path.join(ROOT, "bin", name))
        except OSError:
            pass
    return out


CODE_AT_START = code_mtimes()  # ghi lúc nạp module = lúc server khởi động
_STALE = {"at": 0.0, "files": []}


def stale_code():
    """Danh sách file .py của server đã đổi sau khi khởi động (cache 5 giây cho rẻ)."""
    now = time.time()
    if now - _STALE["at"] > 5:
        cur = code_mtimes()
        _STALE["files"] = sorted(f for f, m in cur.items() if f in CODE_AT_START and m != CODE_AT_START[f])
        _STALE["at"] = now
    return _STALE["files"]


SESSIONS = {}
AUTH_LOCK = threading.Lock()
VERIFY_LOCK = threading.Lock()
FAILURES = 0
LAST_FAILURE = 0
LOCKED_UNTIL = 0
SESSION_SECONDS = 7 * 24 * 60 * 60
PBKDF2_ROUNDS = 300000


def auth_config():
    try:
        with open(AUTH_FILE, encoding="ascii") as f:
            encoded = f.read().strip()
    except FileNotFoundError:
        return ""
    except (OSError, UnicodeError):
        return None
    try:
        algorithm, rounds, salt, digest = encoded.split("$")
        if algorithm != "pbkdf2_sha256" or int(rounds) < PBKDF2_ROUNDS or len(bytes.fromhex(salt)) != 16 or len(bytes.fromhex(digest)) != 32:
            return None
    except (ValueError, TypeError):
        return None
    return encoded


def password_hash(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return "pbkdf2_sha256$%d$%s$%s" % (PBKDF2_ROUNDS, salt.hex(), digest.hex())


def valid_password(password, encoded):
    try:
        algorithm, rounds, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256" or int(rounds) < PBKDF2_ROUNDS:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(rounds)).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def set_password_cli(clear=False):
    if clear:
        try:
            os.remove(AUTH_FILE)
        except FileNotFoundError:
            pass
        print("Đã tắt đăng nhập dashboard.")
        return 0
    first = getpass.getpass("Mật khẩu dashboard: ")
    second = getpass.getpass("Nhập lại mật khẩu: ")
    if first != second:
        print("Mật khẩu nhập lại không khớp.", file=sys.stderr)
        return 1
    if len(first) < 8:
        print("Mật khẩu phải có ít nhất 8 ký tự.", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    temp_file = AUTH_FILE + ".tmp-" + secrets.token_hex(8)
    fd = os.open(temp_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="ascii") as f:
        f.write(password_hash(first) + "\n")
    os.replace(temp_file, AUTH_FILE)
    print("Đã đặt mật khẩu dashboard.")
    return 0


def write_auth(encoded):
    """Ghi (hoặc xoá khi encoded=None) file mật khẩu config/auth.conf, quyền 600."""
    if encoded is None:
        try:
            os.remove(AUTH_FILE)
        except FileNotFoundError:
            pass
        return
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    fd = os.open(AUTH_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="ascii") as f:
        f.write(encoded + "\n")
    os.chmod(AUTH_FILE, 0o600)


def check_password(password, encoded):
    """Kiểm tra mật khẩu hiện tại, dùng chung bộ đếm sai/khoá tạm với trang đăng nhập.
    Trả về None nếu đúng, hoặc (thông báo lỗi, mã HTTP)."""
    global FAILURES, LAST_FAILURE, LOCKED_UNTIL
    with VERIFY_LOCK:
        now = time.time()
        with AUTH_LOCK:
            if LAST_FAILURE and now - LAST_FAILURE > 600:
                FAILURES, LAST_FAILURE = 0, 0
            wait = max(0, int(LOCKED_UNTIL - now + 0.999))
        if wait:
            return ("Nhập sai quá nhiều lần, thử lại sau %d giây" % wait, 429)
        if isinstance(password, str) and valid_password(password, encoded):
            with AUTH_LOCK:
                FAILURES, LAST_FAILURE, LOCKED_UNTIL = 0, 0, 0
            return None
        with AUTH_LOCK:
            FAILURES += 1
            LAST_FAILURE = time.time()
            if FAILURES >= 5:
                FAILURES, LOCKED_UNTIL = 0, time.time() + 60
        return ("Mật khẩu hiện tại không đúng", 401)


def new_session(encoded):
    token = secrets.token_urlsafe(32)
    with AUTH_LOCK:
        SESSIONS.clear()  # đổi/đặt mật khẩu: mọi phiên cũ hết hiệu lực, chỉ giữ phiên của trình duyệt vừa đổi
        SESSIONS[token] = (time.time() + SESSION_SECONDS, encoded)
    return ("Set-Cookie", "pentagon_session=%s; HttpOnly; SameSite=Strict; Path=/; Max-Age=%d" % (token, SESSION_SECONDS))


def clear_sessions():
    with AUTH_LOCK:
        SESSIONS.clear()


def refresh_workers_forever():
    while True:
        refresh_workers_once()
        time.sleep(120)


def refresh_workers_once():
    if True:
        try:
            out = subprocess.run([os.path.join(ROOT, "bin", "workers"), "--tsv"], capture_output=True,
                                 text=True, timeout=90).stdout
            items = []
            for line in out.splitlines():
                p = line.split("\t")
                if len(p) >= 3:
                    items.append({"name": p[0], "tool": p[1], "login": p[2],
                                  "model": p[3] if len(p) > 3 else "", "desc": p[4] if len(p) > 4 else ""})
            WORKERS["items"], WORKERS["checked"] = items, int(time.time())
        except Exception as e:  # không để luồng nền chết
            sys.stderr.write("[dashboard] không đọc được bin/workers: %s\n" % e)


# ---------------- sản phẩm của task (trang Kết quả)
INTERNAL_FILES = {"brief.md", "plan.md", "final.md", "status", "log.txt", "limited", ".deleted_at", ".DS_Store"}
SKIP_DIRS = {"manager", "running", "prompts", "__pycache__", ".git", "node_modules", ".venv"}
KINDS = {
    "image": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp"},
    "html": {".html", ".htm"},
    "video": {".mp4", ".webm", ".mov"},
    "audio": {".mp3", ".wav", ".m4a", ".ogg"},
    "pdf": {".pdf"},
    "text": {".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx", ".css", ".json", ".csv", ".yml", ".yaml", ".sh",
             ".java", ".go", ".rs", ".c", ".cpp", ".h", ".sql", ".xml", ".toml", ".ini", ".rb", ".php", ".swift", ".kt"},
}


def file_kind(name):
    ext = os.path.splitext(name)[1].lower()
    for k, exts in KINDS.items():
        if ext in exts:
            return k
    return "other"


def task_files(tid):
    """Sản phẩm (file do worker/quản lý tạo ra) và báo cáo của từng nhân viên (results/*.md)."""
    base = os.path.join(TASKS, tid)
    products, reports = [], []
    for root, dirs, files in os.walk(base):
        rel_root = os.path.relpath(root, base)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("backup")
                         and not (rel_root == "." and d.startswith(".")))
        for n in sorted(files):
            rel = n if rel_root == "." else os.path.join(rel_root, n)
            if rel_root == "." and n in INTERNAL_FILES:
                continue
            p = os.path.join(root, n)
            try:
                st = os.stat(p)
            except OSError:
                continue
            item = {"path": rel, "name": n, "size": st.st_size, "mtime": int(st.st_mtime), "kind": file_kind(n)}
            if rel_root == "results" and (n.endswith(".md") or n.startswith("dang-do-")):
                reports.append(item)
            else:
                products.append(item)
            if len(products) > 400:
                return {"products": products, "reports": reports, "truncated": True}
    products.sort(key=lambda x: ({"html": 0, "image": 1, "pdf": 2, "video": 3, "audio": 3, "text": 4}.get(x["kind"], 5), x["path"]))
    return {"products": products, "reports": reports, "truncated": False}


def decode_images(images):
    """Validate client data URLs and return (server filename, bytes)."""
    if not isinstance(images, list) or len(images) > 8:
        raise ValueError("Tối đa 8 ảnh mỗi lần gửi")
    result = []
    total = 0
    signatures = {"image/png": ("png", b"\x89PNG\r\n\x1a\n"),
                  "image/jpeg": ("jpg", b"\xff\xd8\xff"),
                  "image/gif": ("gif", b"GIF8"),
                  "image/webp": ("webp", b"RIFF")}
    for index, item in enumerate(images, 1):
        if not isinstance(item, dict):
            raise ValueError("Ảnh đính kèm không hợp lệ")
        data_url = item.get("data", "")
        if not isinstance(data_url, str) or "," not in data_url:
            raise ValueError("Dữ liệu ảnh không hợp lệ")
        header, encoded = data_url.split(",", 1)
        mime = header[5:].split(";", 1)[0].lower() if header.startswith("data:") else ""
        if mime not in signatures or not header.lower().endswith(";base64"):
            raise ValueError("Chỉ nhận ảnh PNG, JPEG, GIF hoặc WebP")
        if len(encoded) > 7_000_000:
            raise ValueError("Mỗi ảnh phải có dung lượng tối đa 5 MB")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("Dữ liệu base64 của ảnh không hợp lệ")
        if not raw or len(raw) > 5 * 1024 * 1024:
            raise ValueError("Mỗi ảnh phải có dung lượng tối đa 5 MB")
        total += len(raw)
        if total > 40 * 1024 * 1024:
            raise ValueError("Tổng dung lượng ảnh tối đa 40 MB")
        ext, magic = signatures[mime]
        if not raw.startswith(magic) or (mime == "image/webp" and raw[8:12] != b"WEBP"):
            raise ValueError("Nội dung ảnh không khớp định dạng khai báo")
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        result.append(("img-%s-%02d-%s.%s" % (stamp, index, secrets.token_hex(3), ext), raw))
    return result


def save_images(tid, images):
    return pt_manager.save_task_images(tid, images)


# ---------------- xem trên điện thoại (cùng Wi-Fi)
LAN = {"server": None, "ip": ""}


def lan_ip():
    """Địa chỉ của máy trong mạng nội bộ (không gửi gói tin nào ra ngoài)."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except OSError:
        ip = ""
    finally:
        s.close()
    if ip.startswith("127.") or not ip:
        return ""
    return ip


def lan_private(ip):
    import ipaddress
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def start_lan():
    if LAN["server"]:
        return LAN["ip"]
    ip = lan_ip()
    if not ip or not lan_private(ip):
        raise RuntimeError("không tìm thấy mạng Wi-Fi nội bộ của máy")
    srv = ThreadingHTTPServer((ip, PORT[0]), Handler)
    srv.is_lan = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    LAN.update(server=srv, ip=ip)
    return ip


def stop_lan():
    srv = LAN["server"]
    LAN.update(server=None, ip="")
    if srv:
        threading.Thread(target=lambda: (srv.shutdown(), srv.server_close()), daemon=True).start()


def lan_status():
    on = bool(LAN["server"])
    return {"enabled": on, "url": ("http://%s:%d" % (LAN["ip"], PORT[0])) if on else "",
            "ip": LAN["ip"] or lan_ip()}


def accounts_view():
    """Trang Tài khoản: mọi tài khoản trong workers.conf + đăng nhập, rảnh/bận, usage, phiên đăng nhập web."""
    import pt_accounts
    import pt_usage
    login = {w["name"]: w["login"] for w in WORKERS["items"]}
    desks = {d["name"]: d for d in office()["desks"]}
    out = []
    for a in pt_accounts.accounts():
        d = desks.get(a["name"], {})
        home = "" if a["default"] else os.path.expanduser(a["home"])
        blocked = tracker.read(os.path.join(pt_usage.UDIR, a["name"] + ".blocked")) or ""
        a.update(login=login.get(a["name"], "?" if a["enabled"] else "off"), blocked=blocked.strip(),
                 busy=len(d.get("working", [])), done_today=d.get("done_today", 0), fails_today=d.get("fails_today", 0),
                 usage=d.get("usage") or pt_usage.usage_for(a["name"], a["tool"], home),
                 login_session=pt_accounts.login_status(a["name"]))
        out.append(a)
    return {"accounts": out, "checked": WORKERS["checked"]}


def retry_forever():
    """Tự cho quản lý làm tiếp các task đã hẹn giờ (sau khi mọi tài khoản hết hạn mức)."""
    while True:
        try:
            pt_manager.check_retries()
            pt_manager.check_queue()
            pt_manager.check_orphans()
        except Exception as e:
            sys.stderr.write("[dashboard] lỗi khi tự làm tiếp: %s\n" % e)
        time.sleep(10)


def office():
    """Văn phòng làm việc: mỗi worker một bàn (đang làm gì, rảnh/bận, hôm nay làm bao nhiêu), cộng các AI quản lý đang chạy."""
    today = time.strftime("%Y-%m-%d")
    now = time.time()
    desks = {w["name"]: dict(w, working=[], done_today=0, secs_today=0, fails_today=0, limited_at="", last="")
             for w in WORKERS["items"]}
    managers = []
    for tid in task_ids():
        tdir = os.path.join(TASKS, tid)
        recent = now - tracker.newest_mtime(tdir) < 86400
        if not recent and not tid.startswith(today.replace("-", "")):
            continue
        t = summary(tid)
        for r in t["running"]:
            d = desks.setdefault(r.get("worker", "?"), {"name": r.get("worker", "?"), "tool": r.get("tool", ""),
                                 "login": "ok", "model": "", "desc": "", "working": [], "done_today": 0,
                                 "secs_today": 0, "fails_today": 0, "limited_at": "", "last": ""})
            d["working"].append({"task": tid, "title": t["title"], "summary": r.get("summary", ""),
                                 "started": r["started"], "model": r.get("model", ""), "perm": r.get("perm", "")})
        for r in tracker.list_results(tdir):
            if r.get("worker") in desks and str(r.get("at", "")).startswith(today):
                desks[r["worker"]]["done_today"] += 1
                desks[r["worker"]]["secs_today"] += r.get("secs", 0)
                desks[r["worker"]]["last"] = max(desks[r["worker"]]["last"], r.get("at", ""))
        if tid.startswith(today.replace("-", "")) or recent:
            for i in tracker.parse_log(read(os.path.join(tdir, "log.txt"))):
                if i["who"] in desks and i["kind"] == "fail":
                    desks[i["who"]]["fails_today"] += 1
                    if "hết hạn mức" in i["text"] and i["time"] > desks[i["who"]]["limited_at"]:
                        desks[i["who"]]["limited_at"] = i["time"]
        m = t["manager"]
        if m["running"] or m["pending"] or m["retry_at"] > 1:
            managers.append({"task": tid, "title": t["title"], "running": m["running"], "pending": m["pending"],
                             "started": m["started"], "model": m["model"], "account": m["account"],
                             "retry_at": m["retry_at"], "state": t["state"], "step": t["step"],
                             "step_label": t["step_label"]})
    # usage của từng tài khoản: % hạn mức gói thuê bao + token hôm nay (không tốn thêm lượt gọi)
    import pt_usage
    homes = {r[0]: pt_manager.resolve_home(r[2]) for r in pt_manager.conf_rows(pt_manager.WORKERS)}
    for d in desks.values():
        d["usage"] = pt_usage.usage_for(d["name"], d.get("tool", ""), homes.get(d["name"], ""))
        d["blocked"] = (tracker.read(os.path.join(pt_usage.UDIR, d["name"] + ".blocked")) or "").strip()
    return {"now": int(now), "desks": list(desks.values()), "managers": managers,
            "workers_checked": WORKERS["checked"]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8", extra_headers=None):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Length", str(len(data)))
        for name, value in extra_headers or []:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def json(self, obj, code=200, extra_headers=None):
        self.send(code, json.dumps(obj, ensure_ascii=False), extra_headers=extra_headers)

    def discard_body(self, n, cap=128 * 1024 * 1024):
        """Đọc bỏ tối đa `cap` byte thân request (không giữ trong bộ nhớ)."""
        left = min(n, cap)
        try:
            while left > 0:
                chunk = self.rfile.read(min(left, 1 << 20))
                if not chunk:
                    break
                left -= len(chunk)
        except OSError:
            pass

    def session_tokens(self):
        tokens = []
        for part in (self.headers.get("Cookie") or "").split(";"):
            key, sep, value = part.strip().partition("=")
            if sep and key == "pentagon_session":
                tokens.append(value)
        return tokens

    def logged_in(self, encoded):
        now = time.time()
        with AUTH_LOCK:
            for token in self.session_tokens():
                item = SESSIONS.get(token)
                if item and item[0] > now and hmac.compare_digest(item[1], encoded):
                    return True
                if item:
                    SESSIONS.pop(token, None)
        return False

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def serve_task_file(self, rest, download=False):
        tid, _, rel = rest.partition("/")
        if tid not in task_ids() or not rel:
            return self.send(404, "không có file", "text/plain; charset=utf-8")
        base = os.path.realpath(os.path.join(TASKS, tid))
        p = os.path.realpath(os.path.join(base, rel))
        if not p.startswith(base + os.sep) or not os.path.isfile(p) or os.path.getsize(p) > 50 * 1024 * 1024:
            return self.send(404, "không có file", "text/plain; charset=utf-8")
        ctype = mimetypes.guess_type(p)[0] or "application/octet-stream"
        if file_kind(p) == "text" or ctype.startswith("text/"):
            ctype = ("text/html" if file_kind(p) == "html" else "text/plain") + "; charset=utf-8"
        elif ctype in ("text/html", "image/svg+xml") or file_kind(p) == "html":
            ctype += "; charset=utf-8" if "charset" not in ctype else ""
        with open(p, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        # Cách ly: trang/ảnh do AI tạo chạy ở origin riêng, không gọi được API của Pentagon, không đọc được cookie
        self.send_header("Content-Security-Policy", "sandbox allow-scripts allow-popups allow-forms allow-modals")
        if download:
            self.send_header("Content-Disposition", "attachment; filename*=UTF-8''%s" % quote(os.path.basename(p)))
        self.end_headers()
        self.wfile.write(data)

    def from_lan(self):
        return getattr(self.server, "is_lan", False)

    def host_ok(self):
        host = (self.headers.get("Host") or "").lower()
        if self.from_lan():  # truy cập từ điện thoại: chỉ khi đã có mật khẩu và đúng địa chỉ nội bộ
            return bool(LAN["ip"]) and host == "%s:%d" % (LAN["ip"], PORT[0]) and bool(auth_config()) \
                and lan_private(self.client_address[0])
        return host in ("127.0.0.1:%d" % PORT[0], "localhost:%d" % PORT[0])

    def do_GET(self):
        if not self.host_ok():
            return self.json({"error": "Host không hợp lệ"}, 403)
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            encoded = auth_config()
            if encoded is None and not u.path.startswith("/static/"):
                return self.send(503, "config/auth.conf bị hỏng — chạy bin/dashboard --set-password hoặc --clear-password", "text/plain; charset=utf-8")
            if not encoded:
                clear_sessions()
            if u.path == "/login":
                if not encoded or self.logged_in(encoded):
                    return self.redirect("/")
                return self.send(200, read(LOGIN_PAGE) or "thiếu web/login.html", "text/html; charset=utf-8")
            if encoded and u.path.startswith("/api/") and not self.logged_in(encoded):
                return self.json({"error": "chưa đăng nhập"}, 401)
            is_page = u.path in ("/", "/dieu-hanh", "/van-phong", "/giao", "/thung-rac", "/tai-khoan", "/nhan-vien", "/cai-dat", "/thong-bao", "/agent") or u.path.startswith("/task/")
            if encoded and is_page and not self.logged_in(encoded):
                return self.redirect("/login")
            if is_page:
                return self.send(200, read(PAGE) or "thiếu web/index.html", "text/html; charset=utf-8")
            if u.path.startswith("/files/"):  # sản phẩm của task: ảnh, trang HTML, file chữ…
                if encoded and not self.logged_in(encoded):
                    return self.send(401, "chưa đăng nhập", "text/plain; charset=utf-8")
                return self.serve_task_file(unquote(u.path[len("/files/"):]), q.get("dl") == "1")
            name = u.path[8:] if u.path.startswith("/static/") else u.path[1:] if u.path in (
                "/favicon.ico", "/apple-touch-icon.png") else ""
            if name in STATIC:  # ảnh logo / icon tab: không cần đăng nhập
                with open(os.path.join(ROOT, "web", name), "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/x-icon" if name.endswith(".ico") else
                                 "text/css; charset=utf-8" if name.endswith(".css") else "image/png")
                self.send_header("Cache-Control", "public, max-age=86400")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if u.path == "/api/tasks":
                tasks = [summary(i) for i in task_ids()]
                busy = sorted({r.get("worker") for t in tasks for r in t["running"]})
                return self.json({"now": int(time.time()), "tasks": tasks, "busy": busy, "auth": bool(encoded),
                                  "sizes": pt_manager.manager_models(), "model_options": pt_manager.model_options(),
                                  "roles": pt_manager.role_names(),
                                  "workers": WORKERS["items"], "workers_checked": WORKERS["checked"],
                                  "stale": bool(stale_code()), "stale_files": stale_code()})
            if u.path == "/api/config":  # Cài đặt: quyền quản lý, bảng model theo cỡ, vai trò subagent
                return self.json({"manager": pt_manager.manager_settings(), "models": pt_manager.models_table(),
                                  "roles": pt_manager.roles_list()})
            if u.path == "/api/files":
                tid = q.get("id", "")
                if tid not in task_ids():
                    return self.json({"error": "không có task"}, 404)
                return self.json(task_files(tid))
            if u.path == "/api/lan":
                return self.json(lan_status())
            if u.path == "/api/agents":
                return self.json(pt_followup.agents_view())
            if u.path == "/api/notifications":
                lst = pt_notify.items()
                return self.json({"items": lst[:100], "unread": sum(1 for n in lst if not n.get("read")),
                                  "settings": pt_notify.settings()})
            if u.path == "/api/auth":
                return self.json({"enabled": bool(encoded)})
            if u.path == "/api/accounts":
                return self.json(accounts_view())
            if u.path == "/api/trash":
                return self.json({"items": pt_manager.trash_list()})
            if u.path == "/api/office":
                return self.json(office())
            if u.path == "/api/task":
                tid = q.get("id", "")
                if tid not in task_ids():
                    return self.json({"error": "không có task"}, 404)
                t = summary(tid, with_docs=True)
                t["chat"] = pt_manager.chat(tid)
                t["inbox"] = pt_manager.inbox_view(tid)
                last = t["chat"][-1]["role"] if t["chat"] else ""
                t["manager_stderr"] = pt_manager.stderr_tail(tid) if last == "error" or (
                    t["manager"]["session"] and not t["manager"]["running"] and last not in ("end", "event")) else ""
                return self.json(t)
            if u.path == "/api/file":
                tid, rel = q.get("id", ""), q.get("path", "")
                if tid not in task_ids():
                    return self.json({"error": "không có task"}, 404)
                base = os.path.realpath(os.path.join(TASKS, tid))
                p = os.path.realpath(os.path.join(base, rel))
                if not p.startswith(base + os.sep) or not os.path.isfile(p):
                    return self.json({"error": "không có file"}, 404)
                return self.json({"path": rel, "text": read(p) or ""})
            return self.json({"error": "không có"}, 404)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        if not self.host_ok() or self.headers.get("X-Pentagon") != "1" \
                or not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return self.json({"error": "từ chối"}, 403)
        origin = self.headers.get("Origin")
        if origin and origin.lower() not in ("http://127.0.0.1:%d" % PORT[0], "http://localhost:%d" % PORT[0]) + (
                ("http://%s:%d" % (LAN["ip"], PORT[0]),) if self.from_lan() else ()):
            return self.json({"error": "từ chối"}, 403)
        path = urlparse(self.path).path
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n < 0:
                return self.json({"error": "Content-Length không hợp lệ"}, 400)
            encoded = auth_config()
            if encoded is None:
                return self.json({"error": "config/auth.conf bị hỏng"}, 503)
            # Login always stays small; unauthenticated callers cannot make us read a large body.
            authed = not encoded or self.logged_in(encoded)
            if not authed and path not in ("/api/login", "/api/logout"):
                # hết phiên: báo 401 (để trang chuyển sang đăng nhập) thay vì 413 khi gửi kèm ảnh
                self.close_connection = True
                return self.json({"error": "chưa đăng nhập"}, 401)
            limit = POST_LIMIT_BIG if authed and path in ("/api/giao", "/api/send") else POST_LIMIT
            if n > limit:
                if authed:
                    self.discard_body(n)  # đọc bỏ phần thân để trình duyệt nhận được mã 413 thay vì lỗi mạng
                self.close_connection = True
                return self.json({"error": "Nội dung gửi lên quá lớn (%s), server chỉ nhận tối đa %s%s" % (
                    human_size(n), human_size(limit),
                    " — ảnh đính kèm quá lớn" if path in ("/api/giao", "/api/send") else "")}, 413)
            body = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(body, dict):
                body = {}
        except ValueError:
            return self.json({"error": "JSON không hợp lệ"}, 400)
        encoded = auth_config()
        if encoded is None:
            return self.json({"error": "config/auth.conf bị hỏng — chạy bin/dashboard --set-password hoặc --clear-password"}, 503)
        if path in ("/api/login", "/api/logout"):
            if path == "/api/logout":
                with AUTH_LOCK:
                    for token in self.session_tokens():
                        SESSIONS.pop(token, None)
                return self.json({"ok": True}, extra_headers=[("Set-Cookie", "pentagon_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0")])
            if not encoded:
                return self.json({"ok": True})
            global FAILURES, LAST_FAILURE, LOCKED_UNTIL
            with VERIFY_LOCK:
                now = time.time()
                with AUTH_LOCK:
                    if LAST_FAILURE and now - LAST_FAILURE > 600:
                        FAILURES, LAST_FAILURE = 0, 0
                    wait = max(0, int(LOCKED_UNTIL - now + 0.999))
                if wait:
                    self.json({"error": "Đăng nhập tạm khoá", "retry_after": wait}, 429)
                    return
                password = body.get("password", "")
                if not isinstance(password, str) or not valid_password(password, encoded):
                    with AUTH_LOCK:
                        FAILURES += 1
                        LAST_FAILURE = time.time()
                        if FAILURES >= 5:
                            FAILURES, LOCKED_UNTIL = 0, time.time() + 60
                            wait = 60
                        else:
                            wait = 0
                    if wait:
                        self.json({"error": "Đăng nhập tạm khoá", "retry_after": wait}, 429)
                    else:
                        self.json({"error": "Mật khẩu không đúng"}, 401)
                    return
                token = secrets.token_urlsafe(32)
                with AUTH_LOCK:
                    FAILURES, LAST_FAILURE, LOCKED_UNTIL = 0, 0, 0
                    now = time.time()
                    for old_token, session in list(SESSIONS.items()):
                        if session[0] <= now:
                            SESSIONS.pop(old_token, None)
                    SESSIONS[token] = (now + SESSION_SECONDS, encoded)
                return self.json({"ok": True}, extra_headers=[("Set-Cookie", "pentagon_session=%s; HttpOnly; SameSite=Strict; Path=/; Max-Age=%d" % (token, SESSION_SECONDS))])
        if encoded and path.startswith("/api/") and not self.logged_in(encoded):
            return self.json({"error": "chưa đăng nhập"}, 401)
        if path in ("/api/auth/set", "/api/auth/disable"):
            if encoded is None:
                return self.json({"error": "file mật khẩu bị hỏng"}, 500)
            if encoded:  # đang bật đăng nhập: phải nhập đúng mật khẩu hiện tại
                bad = check_password(body.get("current", ""), encoded)
                if bad:
                    return self.json({"error": bad[0]}, bad[1])
            if path == "/api/auth/disable":
                write_auth(None)
                clear_sessions()
                stop_lan()  # không còn mật khẩu thì đóng truy cập từ điện thoại
                pt_notify.update_settings(lan_access=False)
                return self.json({"ok": True, "enabled": False},
                                 extra_headers=[("Set-Cookie", "pentagon_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0")])
            new, confirm = body.get("new", ""), body.get("confirm", "")
            if not isinstance(new, str) or len(new) < 8:
                return self.json({"error": "Mật khẩu mới phải có ít nhất 8 ký tự"}, 400)
            if new != confirm:
                return self.json({"error": "Hai lần nhập mật khẩu mới không khớp"}, 400)
            enc = password_hash(new)
            write_auth(enc)
            return self.json({"ok": True, "enabled": True}, extra_headers=[new_session(enc)])
        tid = body.get("id", "")
        try:
            if path == "/api/giao":
                images = decode_images(body.get("images") or [])
                request = str(body.get("text", "")).strip() or ("Xem ảnh đính kèm" if images else "")
                mode = body.get("mode") if body.get("mode") in ("duyet", "lam-luon") else "tu-quyet"
                size = body.get("size") if body.get("size") in ("nho", "vua", "lon") else "auto"
                split = body.get("split") if body.get("split") in ("mot", "song-song") else "auto"
                tid = pt_manager.launch_new(request, mode, size, split, background=True,
                                            assignee=str(body.get("assignee") or ""), images=images)
                return self.json({"ok": True, "id": tid})
            if path == "/api/lan":
                if self.from_lan():
                    return self.json({"error": "chỉ bật/tắt được trên chính máy Mac"}, 403)
                if body.get("enabled"):
                    if not auth_config():
                        return self.json({"error": "Đặt mật khẩu trang web trước (mục bên dưới)"}, 400)
                    try:
                        start_lan()
                    except (RuntimeError, OSError) as e:
                        return self.json({"error": str(e)}, 400)
                else:
                    stop_lan()
                pt_notify.update_settings(lan_access=bool(body.get("enabled")))
                return self.json(dict(lan_status(), ok=True))
            if path == "/api/notifications/read":
                pt_notify.mark_read(body.get("id") or None)
                return self.json({"ok": True})
            if path == "/api/notifications/clear":
                pt_notify.clear()
                return self.json({"ok": True})
            if path == "/api/notifications/test":
                pt_notify.add("thu", "", "Thông báo thử", "Pentagon sẽ báo như thế này khi task có kết quả.")
                return self.json({"ok": True})
            if path == "/api/settings":
                return self.json({"ok": True, "settings": pt_notify.update_settings(
                    **{k: body[k] for k in ("notify_macos", "notify_sound") if k in body})})
            if path == "/api/config/manager":  # {model?: str, allow?: [quyền, ...]}
                return self.json({"ok": True, "manager": pt_manager.save_manager_settings(
                    model=body.get("model"), allow=body.get("allow"))})
            if path == "/api/config/models":  # {rows: {vai_trò: [nhỏ, vừa, lớn]}}
                return self.json({"ok": True, "models": pt_manager.save_models_table(body.get("rows"))})
            if path == "/api/config/roles/save":  # {key, name, perm: doc|theo-viec, desc, body, create: bool}
                role = pt_manager.save_role(body.get("key"), body.get("name"), body.get("perm"), body.get("desc"),
                                            body.get("body"), create=bool(body.get("create")))
                return self.json({"ok": True, "role": role, "roles": pt_manager.roles_list()})
            if path == "/api/config/roles/delete":  # {key}
                pt_manager.delete_role(body.get("key"))
                return self.json({"ok": True, "roles": pt_manager.roles_list()})
            if path.startswith("/api/accounts/"):
                import pt_accounts
                name = str(body.get("name", ""))
                op = path[len("/api/accounts/"):]
                if op == "add":
                    name = pt_accounts.add(name, str(body.get("tool", "")), body.get("desc", ""), body.get("model", ""))
                elif op == "update":
                    pt_accounts.update(name, desc=body.get("desc"), model=body.get("model"))
                elif op == "enable":
                    pt_accounts.set_enabled(name, bool(body.get("enabled")))
                elif op == "move":
                    pt_accounts.move(name, "up" if body.get("dir") == "up" else "down")
                elif op == "remove":
                    pt_accounts.remove(name, forget_login=bool(body.get("forget")))
                elif op == "login":
                    pt_accounts.login_start(name)
                elif op == "login-code":
                    pt_accounts.login_send(name, body.get("code", ""))
                elif op == "login-cancel":
                    pt_accounts.login_cancel(name)
                elif op == "logout":
                    pt_accounts.logout(name)
                else:
                    return self.json({"error": "không có"}, 404)
                threading.Thread(target=refresh_workers_once, daemon=True).start()
                return self.json({"ok": True, "name": name})
            if path == "/api/task/restore":
                return self.json({"ok": True, "id": pt_manager.restore_task(str(body.get("trash_id", "")))})
            if path == "/api/task/purge":
                pt_manager.purge_task(str(body.get("trash_id", "")))
                return self.json({"ok": True})
            if tid not in task_ids():
                return self.json({"error": "không có task"}, 404)
            if path == "/api/task/update":
                title = body.get("title")
                brief = body.get("brief")
                pt_manager.update_task(tid, title=str(title) if title is not None else None,
                                       brief=str(brief) if brief is not None else None)
            elif path == "/api/task/delete":
                return self.json({"ok": True, "trash_id": pt_manager.delete_task(tid)})
            elif path == "/api/task/reopen":
                pt_manager.reopen(tid)
            elif path == "/api/followup":
                pt_followup.start(tid, str(body.get("file", "")), str(body.get("question", "")))
            elif path == "/api/send":
                if not isinstance(tid, str) or tid not in task_ids():
                    return self.json({"error": "không có task"}, 404)
                images = decode_images(body.get("images") or [])
                message = str(body.get("text", "")).strip() or ("Xem ảnh đính kèm" if images else "")
                attachment = save_images(tid, images)
                try:
                    sent = pt_manager.send(tid, message + attachment, reaper=True, size=str(body.get("size") or "auto"),
                                           model=str(body.get("model") or ""), worker=str(body.get("worker") or ""),
                                           worker_model=str(body.get("worker_model") or ""))
                except Exception:
                    for line in attachment.splitlines():
                        candidate = line.removeprefix("- ")
                        if candidate:
                            try: os.remove(candidate)
                            except OSError: pass
                    raise
                return self.json({"ok": True, "id": tid, **(sent if isinstance(sent, dict) else {"queued": False})})
            elif path == "/api/task/inbox/clear":
                pt_manager.clear_inbox(tid)
            elif path == "/api/task/inbox/run":
                pt_manager.run_paused_inbox(tid)
            elif path == "/api/stop":
                pt_manager.stop(tid)
            elif path == "/api/kill-worker":
                pt_manager.kill_worker(tid, str(body.get("pid", "")))
            elif path == "/api/cancel":
                pt_manager.cancel_task(tid)
            elif path == "/api/set-split":
                split = body.get("split") if body.get("split") in ("mot", "song-song") else "auto"
                pt_manager.put(tid, "split", split)
                pt_manager.append_event(tid, "pentagon_event", "Chủ đổi kiểu giao việc: %s (áp dụng từ lượt sau)."
                                        % pt_manager.SPLIT_TXT[split])
            elif path == "/api/set-assignee":
                who = str(body.get("assignee") or "")
                if who and who not in pt_manager.worker_names():
                    return self.json({"error": "không có AI tên %s" % who}, 400)
                pt_manager.put(tid, "assignee", who or None)
                pt_manager.append_event(tid, "pentagon_event", "Chủ đổi AI làm việc: %s (áp dụng từ lượt sau)."
                                        % (who or "để quản lý tự chọn"))
            elif path == "/api/retry-now":
                pt_manager.put(tid, "retry_at", "1")
                pt_manager.check_retries()
            elif path == "/api/done":
                subprocess.run([os.path.join(ROOT, "bin", "progress"), os.path.join(TASKS, tid), "xong",
                                "chủ đánh dấu hoàn thành"], capture_output=True)
            else:
                return self.json({"error": "không có"}, 404)
            return self.json({"ok": True, "id": tid})
        except ValueError as e:
            return self.json({"error": str(e)}, 400)
        except RuntimeError as e:
            return self.json({"error": str(e)}, 409)
        except (BrokenPipeError, ConnectionResetError):
            pass


def cmd_dashboard(argv):
    port, do_open = 8765, False
    if argv == ["--set-password"]:
        return set_password_cli()
    if argv == ["--clear-password"]:
        return set_password_cli(clear=True)
    i = 0
    while i < len(argv):
        if argv[i] in ("-p", "--port") and i + 1 < len(argv):
            port = int(argv[i + 1])
            i += 1
        elif argv[i] == "--open":
            do_open = True
        elif argv[i] in ("-h", "--help"):
            print("Cách dùng: bin/dashboard [--port N] [--open] | --set-password | --clear-password\n"
                  "  Web app Pentagon tại http://127.0.0.1:8765 (chỉ máy này truy cập được).\n"
                  "  --open  mở luôn trình duyệt\n"
                  "  --set-password  đặt mật khẩu dashboard (tối thiểu 8 ký tự)\n"
                  "  --clear-password  tắt đăng nhập dashboard")
            return 0
        i += 1
    server = None
    for p in range(port, port + 10):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if not server:
        print("Không mở được cổng %d-%d" % (port, port + 9), file=sys.stderr)
        return 1
    PORT[0] = port
    if pt_notify.settings().get("lan_access") and auth_config():
        try:
            print("Xem trên điện thoại: http://%s:%d" % (start_lan(), port), flush=True)
        except (RuntimeError, OSError) as e:
            print("Không mở được cho điện thoại: %s" % e, flush=True)
    threading.Thread(target=refresh_workers_forever, daemon=True).start()
    threading.Thread(target=retry_forever, daemon=True).start()
    threading.Thread(target=pt_notify.watch_forever, daemon=True).start()
    url = "http://127.0.0.1:%d" % port
    print("Pentagon: %s   (Ctrl+C để tắt; các quản lý đang chạy nền vẫn tiếp tục)" % url, flush=True)
    if do_open:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        try:
            subprocess.Popen([opener, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    return 0
