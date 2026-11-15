"""Editor video HyperFrames cho task video.

Tìm dự án HyperFrames (thư mục có hyperframes.json) trong thư mục task, bật/tắt HyperFrames Studio
(`npx hyperframes preview --background`) để chủ xem và sửa video ngay trong dashboard, và tạo dự án mới
từ một video sản phẩm của task (`npx hyperframes init --video …`).
Studio chỉ nghe trên 127.0.0.1, nên editor chỉ dùng được trên chính máy này.
"""
import json
import os
import re
import shutil
import socket
import subprocess
import threading
import time

import tracker

TASKS = tracker.TASKS
SKIP = {"node_modules", ".hyperframes", "__pycache__", ".git", "manager", "running", ".venv", "renders"}
VIDEO_EXT = (".mp4", ".mov", ".webm", ".m4v", ".mkv")
VIDEO_WORDS = re.compile(r"(video|clip|reels?|tiktok|shorts|youtube|hyperframes|motion graphic|dựng phim|quay phim)", re.I)
PORTS = range(3400, 3500)
_STATE = {}   # projdir -> {"t": thời điểm hỏi, "res": kết quả status của CLI}
_LOCK = threading.Lock()


def _npx():
    return shutil.which("npx") or "npx"


def _tdir(tid):
    if not tid or "/" in tid or tid.startswith(".") or not os.path.isdir(os.path.join(TASKS, tid)):
        raise RuntimeError("không có task")
    return os.path.realpath(os.path.join(TASKS, tid))


def _inside(base, rel):
    p = os.path.realpath(os.path.join(base, rel)) if rel else base
    if p != base and not p.startswith(base + os.sep):
        raise RuntimeError("đường dẫn không hợp lệ")
    return p


def _projects(base):
    out = []
    for root, dirs, files in os.walk(base):
        rel = os.path.relpath(root, base)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith(".")) if depth < 4 else []
        if "hyperframes.json" in files:
            out.append({"dir": "" if rel == "." else rel, "name": os.path.basename(root)})
            dirs[:] = []
    return out


def _videos(base, limit=40):
    out = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for f in files:
            if f.lower().endswith(VIDEO_EXT):
                p = os.path.join(root, f)
                try:
                    out.append({"path": os.path.relpath(p, base), "size": os.path.getsize(p), "mtime": int(os.path.getmtime(p))})
                except OSError:
                    pass
        if len(out) >= limit:
            break
    return out


def _cli(args, cwd, timeout=180):
    """Chạy `npx hyperframes …` ở cwd, trả JSON cuối cùng in ra (hoặc báo lỗi dễ hiểu)."""
    pin = None
    try:
        with open(os.path.join(cwd, "package.json"), encoding="utf-8") as f:
            m = re.search(r"hyperframes@([0-9][\w.\-]*)", f.read())
            pin = m.group(1) if m else None
    except OSError:
        pass
    cmd = [_npx(), "--yes", "hyperframes@%s" % pin if pin else "hyperframes"] + args
    env = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1", CI="1")
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env,
                           stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        raise RuntimeError("máy chưa cài Node.js (cần Node 22+ để chạy HyperFrames)")
    except subprocess.TimeoutExpired:
        raise RuntimeError("HyperFrames chạy quá lâu, thử lại sau")
    for line in reversed((r.stdout or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    tail = ((r.stderr or "") + (r.stdout or "")).strip().splitlines()[-3:]
    if r.returncode != 0:
        raise RuntimeError("HyperFrames báo lỗi: %s" % (" ".join(tail)[:300] or "mã %d" % r.returncode))
    return {}


def _port_free(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def _alive(res):
    try:
        os.kill(int(res.get("pid")), 0)
    except (OSError, TypeError, ValueError):
        return False
    return not _port_free(int(res.get("port") or 0))


def _status(projdir, fresh=False):
    with _LOCK:
        st = _STATE.get(projdir)
    if st and not fresh and time.time() - st["t"] < 20:
        res = st["res"]
        return res if (not res or _alive(res)) else None
    try:
        j = _cli(["preview", "--status", "--json"], projdir, timeout=60)
        res = j.get("result") if j.get("ok") and (j.get("result") or {}).get("state") == "running" else None
    except RuntimeError:
        res = None
    with _LOCK:
        _STATE[projdir] = {"t": time.time(), "res": res}
    return res


def _proj_view(base, p, check=True):
    projdir = _inside(base, p["dir"])
    res = _status(projdir) if check else None
    return dict(p, running=bool(res), url=(res or {}).get("studioUrl"))


def info(tid):
    base = _tdir(tid)
    projs = _projects(base)
    pdirs = [p["dir"] + "/" for p in projs if p["dir"]]
    # video nằm trong dự án là nguồn của dự án, không phải bản đã xuất
    vids = [v for v in _videos(base) if not any(v["path"].startswith(d) for d in pdirs)] if "" not in [p["dir"] for p in projs] else []
    title = ""
    try:
        with open(os.path.join(base, "brief.md"), encoding="utf-8", errors="replace") as f:
            title = f.read(4000)
    except OSError:
        pass
    video = bool(projs or vids or VIDEO_WORDS.search(title))
    return {"video": video, "projects": [_proj_view(base, p) for p in projs] if video else [],
            "videos": sorted(vids, key=lambda v: -v["mtime"])[:20], "node": bool(shutil.which("npx"))}


def start(tid, rel):
    base = _tdir(tid)
    projdir = _inside(base, rel)
    if not os.path.isfile(os.path.join(projdir, "hyperframes.json")):
        raise RuntimeError("thư mục này không phải dự án HyperFrames")
    res = _status(projdir, fresh=True)
    if not res:
        port = next((p for p in PORTS if _port_free(p)), None)
        if port is None:
            raise RuntimeError("hết cổng trống (3400–3499) — tắt bớt editor đang mở")
        j = _cli(["preview", "--background", "--no-open", "--port", str(port), "--json"], projdir)
        if not j.get("ok"):
            raise RuntimeError("không mở được Studio: %s" % ((j.get("error") or {}).get("message") or "không rõ lỗi"))
        res = j.get("result") or {}
        with _LOCK:
            _STATE[projdir] = {"t": time.time(), "res": res}
    return {"dir": rel, "name": os.path.basename(projdir), "running": True, "url": res.get("studioUrl")}


def stop(tid, rel):
    base = _tdir(tid)
    projdir = _inside(base, rel)
    _cli(["preview", "--stop", "--json"], projdir, timeout=60)
    with _LOCK:
        _STATE[projdir] = {"t": time.time(), "res": None}


def init(tid, video=""):
    """Tạo dự án HyperFrames mới trong task (thư mục video-editor[-N]); có video thì dựng sẵn từ video đó."""
    base = _tdir(tid)
    name = "video-editor"
    k = 2
    while os.path.exists(os.path.join(base, name)):
        name = "video-editor-%d" % k
        k += 1
    args = ["init", name, "--skip-skills", "--non-interactive"]
    if video:
        vp = _inside(base, video)
        if not os.path.isfile(vp) or not vp.lower().endswith(VIDEO_EXT):
            raise RuntimeError("không có video này trong task")
        args += ["--video", vp, "--skip-transcribe"]
        try:
            out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                  "stream=width,height", "-of", "csv=p=0", vp], capture_output=True, text=True, timeout=20)
            w, h = (int(x) for x in out.stdout.strip().split(",")[:2])
            args += ["--resolution", "portrait" if h > w else "square" if h == w else "landscape"]
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass
    _cli(args, base, timeout=600)
    if not os.path.isfile(os.path.join(base, name, "hyperframes.json")):
        raise RuntimeError("HyperFrames không tạo được dự án")
    return {"dir": name, "name": name, "running": False, "url": None}
