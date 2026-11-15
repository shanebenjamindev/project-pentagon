"""Thông báo cho chủ khi task có kết quả hoặc cần chủ (chạy trong bin/dashboard).

- Theo dõi trạng thái các task mỗi vài giây; khi đổi sang: xong / chờ chủ trả lời / dừng-lỗi / hết hạn mức
  thì tạo một thông báo.
- Gửi thông báo hệ thống macOS (góc phải màn hình, có âm thanh) nếu bật trong Cài đặt.
- Lưu danh sách thông báo ở ~/.pentagon/notifications.json để trang web hiện mục Thông báo.
"""
import json
import os
import subprocess
import sys
import threading
import time

import tracker

DATA = os.environ.get("ORCH_DATA") or os.path.expanduser("~/.pentagon")
NOTI = os.path.join(DATA, "notifications.json")
SEEN = os.path.join(DATA, "notify-state.json")
SETTINGS = os.path.join(DATA, "settings.json")
LOCK = threading.Lock()
DEFAULTS = {"notify_macos": True, "notify_sound": True, "lan_access": False}


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".%d.tmp" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


def settings():
    s = dict(DEFAULTS)
    s.update(_load(SETTINGS, {}))
    return s


def update_settings(**kw):
    s = settings()
    for k, v in kw.items():
        if k in DEFAULTS:
            s[k] = bool(v)
    _save(SETTINGS, s)
    return s


def items():
    with LOCK:
        return _load(NOTI, [])


def mark_read(nid=None):
    with LOCK:
        lst = _load(NOTI, [])
        for n in lst:
            if nid is None or n["id"] == nid:
                n["read"] = True
        _save(NOTI, lst)


def clear():
    with LOCK:
        _save(NOTI, [])


def remove(ids):
    """Xoá các thông báo có id trong ids."""
    ids = set(ids)
    with LOCK:
        _save(NOTI, [n for n in _load(NOTI, []) if n["id"] not in ids])


def read_many(ids):
    ids = set(ids)
    with LOCK:
        lst = _load(NOTI, [])
        for n in lst:
            if n["id"] in ids:
                n["read"] = True
        _save(NOTI, lst)


def macos_notify(title, subtitle, body, sound=True):
    if sys.platform != "darwin":
        return
    q = lambda t: '"%s"' % str(t).replace("\\", "\\\\").replace('"', '\\"')[:220]
    script = "display notification %s with title %s subtitle %s%s" % (
        q(body), q(title), q(subtitle), ' sound name "Glass"' if sound else "")
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        pass


def add(kind, task, title, body):
    n = {"id": "%d-%s" % (int(time.time() * 1000), kind), "ts": int(time.time()), "kind": kind,
         "task": task, "title": title, "body": body, "read": False}
    with LOCK:
        lst = _load(NOTI, [])
        lst.insert(0, n)
        _save(NOTI, lst[:200])
    s = settings()
    if s["notify_macos"]:
        head = {"xong": "Task đã xong", "cho": "Cần bạn trả lời", "loi": "Task bị dừng", "han-muc": "Hết hạn mức"}.get(kind, "Pentagon")
        macos_notify("Pentagon · " + head, title, body or "Mở Pentagon để xem.", s["notify_sound"])
    return n


def _key(t):
    m = t["manager"]
    return {"state": t["state"], "retry": 1 if m.get("retry_at", 0) > 1 else 0}


def check():
    """So trạng thái hiện tại với lần trước; trạng thái đổi theo hướng cần báo thì tạo thông báo."""
    seen = _load(SEEN, None)
    now = {}
    for tid in tracker.task_ids():
        t = tracker.summary(tid)
        now[tid] = (t, _key(t))
    if seen is None:  # lần đầu: chỉ ghi nhận, không báo những gì đã có từ trước
        _save(SEEN, {tid: k for tid, (t, k) in now.items()})
        return
    for tid, (t, k) in now.items():
        old = seen.get(tid)
        if old == k:
            continue
        st, oldst = k["state"], (old or {}).get("state")
        note = t.get("note") or ""
        if st != oldst:
            if st == "xong":
                add("xong", tid, t["title"], note or "Task đã hoàn thành — xem kết quả.")
            elif st == "cho" and not k["retry"]:
                add("cho", tid, t["title"], note or "Quản lý đang chờ bạn trả lời.")
            elif st == "loi":
                add("loi", tid, t["title"], note or "Task bị dừng.")
        if k["retry"] and not (old or {}).get("retry"):
            add("han-muc", tid, t["title"], note or "Mọi tài khoản hết hạn mức — sẽ tự làm tiếp khi có hạn mức.")
    _save(SEEN, {tid: k for tid, (t, k) in now.items()})


def watch_forever(interval=5):
    while True:
        try:
            check()
        except Exception as e:  # không để luồng nền chết
            sys.stderr.write("[dashboard] lỗi thông báo: %s\n" % e)
        time.sleep(interval)
