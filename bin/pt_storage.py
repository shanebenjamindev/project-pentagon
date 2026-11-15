"""File của task và dung lượng.

- group_products(): tách file của task thành 3 nhóm cho tab Sản phẩm:
    main   — sản phẩm chính (file/thư mục mà final.md nhắc tới, hoặc thư mục out/, site/, dist/…)
    attach — file chủ gửi kèm (attachments/)
    work   — file làm việc: AI tải về, nháp, code phụ, ảnh trung gian…
- usage()/dir_usage(): task nào chiếm bao nhiêu, xem từng thư mục con.
- delete_path()/clean_junk()/empty_trash(): dọn dung lượng từ trang Cài đặt.
"""
import os
import re
import shutil

import tracker

TASKS = tracker.TASKS
TRASH = os.path.join(TASKS, ".trash")

# không bao giờ xoá từ trang Dung lượng: hồ sơ của task (yêu cầu, kế hoạch, kết quả, báo cáo, phiên quản lý)
PROTECTED = {"brief.md", "plan.md", "final.md", "status", "log.txt", "limited", ".deleted_at",
             "results", "manager", "attachments", "running"}
JUNK_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
JUNK_FILES = {".DS_Store"}
JUNK_EXT = (".pyc", ".pyo")
# thư mục thường chứa sản phẩm cuối / thường là đồ nháp
OUT_DIRS = {"out", "output", "outputs", "dist", "site", "final", "ket-qua", "san-pham", "build", "public", "deliverables"}
TMP_HINT = re.compile(r"^(tmp|temp|cache|\.cache|frames?|downloads?|assets?|raw|scratch|edit|draft|nhap)$", re.I)


def is_junk(name, is_dir):
    return name in JUNK_DIRS if is_dir else (name in JUNK_FILES or name.endswith(JUNK_EXT))


def _walk_size(p):
    """(bytes, số file) của một file hoặc thư mục — không đi theo symlink."""
    try:
        st = os.lstat(p)
    except OSError:
        return 0, 0
    if not os.path.isdir(p) or os.path.islink(p):
        return st.st_size, 1
    total, n = 0, 0
    for root, dirs, files in os.walk(p):
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_size
                n += 1
            except OSError:
                pass
    return total, n


# ---------------------------------------------------------------- nhóm sản phẩm

_MENTION = re.compile(r"[\w.\-/~]*[\w\-]+(?:\.[A-Za-z0-9]{1,6}|/)")


def _mentions(final_text, tid):
    """Các đường dẫn final.md nhắc tới, đã bỏ phần tasks/<id>/ ở đầu."""
    out = set()
    for m in _MENTION.findall(final_text or ""):
        m = m[2:] if m.startswith("./") else m
        k = m.find("tasks/%s/" % tid)
        if k >= 0:
            m = m[k + len("tasks/%s/" % tid):]
        elif m.startswith("/"):
            continue  # đường dẫn tuyệt đối ngoài task
        m = m.lstrip("/")
        if m and not m.startswith("http") and m not in ("final.md", "brief.md", "plan.md"):
            out.add(m)
    return out


def _match(path, mentions):
    """Đường dẫn final.md nhắc tới khớp với file này: tên file, hoặc thư mục (kết thúc bằng /) chứa nó."""
    best = None
    for m in mentions:
        if m.endswith("/"):
            if path.startswith(m) or ("/" + m) in ("/" + path):
                d = path[:path.index(m) + len(m)] if not path.startswith(m) else m
                best = best or d
        elif path == m or path.endswith("/" + m) or (("/" not in m) and os.path.basename(path) == m):
            return path  # nhắc thẳng tới file: ưu tiên hơn thư mục
    return best


BUNDLE_MIN = 12   # thư mục sản phẩm có từ chừng này file trở lên thì gom lại thành một mục
BUNDLE_KEEP = 40  # liệt kê tối đa chừng này file của một thư mục gom


def group_products(tid, products):
    """Gắn item["group"] = main | attach | work cho từng file sản phẩm (đã bỏ báo cáo results/*.md).
    Thư mục sản phẩm lớn (vd bản sao cả trang web) được gom: trả về trong "bundles", chỉ giữ vài file đại diện.
    Trả về (products đã lọc, info)."""
    final = ""
    try:
        with open(os.path.join(TASKS, tid, "final.md"), encoding="utf-8", errors="replace") as f:
            final = f.read()
    except OSError:
        pass
    mentions = _mentions(final, tid)
    for it in products:
        p = it["path"]
        if p.startswith("attachments/"):
            it["group"] = "attach"
            continue
        hit = _match(p, mentions)
        it["group"] = "main" if hit else "work"
        if hit and hit.endswith("/"):
            it["bundle"] = hit
    from_final = any(it["group"] == "main" for it in products)
    if not from_final:
        # final.md không chỉ rõ: lấy file trong thư mục kiểu out/, site/… và file trang web/tài liệu ở ngay gốc task
        for it in products:
            if it["group"] != "work":
                continue
            dirs = it["path"].split("/")[:-1]
            if any(TMP_HINT.match(d) or d in JUNK_DIRS for d in dirs):
                continue
            k = next((i for i, d in enumerate(dirs) if d.lower() in OUT_DIRS), None)
            if k is not None:
                it["group"], it["bundle"] = "main", "/".join(dirs[:k + 1]) + "/"
            elif not dirs and it["kind"] in ("html", "pdf", "image", "video", "audio"):
                it["group"] = "main"
    # gom thư mục lớn
    members = {}
    for it in products:
        if it["group"] == "main" and it.get("bundle"):
            members.setdefault(it["bundle"], []).append(it)
    bundles, drop = [], set()
    for d, items in members.items():
        if len(items) < BUNDLE_MIN:
            for it in items:
                it.pop("bundle", None)
            continue
        entry = next((it for it in sorted(items, key=lambda x: x["path"].count("/"))
                      if it["name"].lower() in ("index.html", "index.htm")), None)
        keep = sorted(items, key=lambda x: (x is not entry, x["path"].count("/"), x["path"]))[:BUNDLE_KEEP]
        drop.update(id(x) for x in items if x not in keep)
        bundles.append({"dir": d, "count": len(items), "size": sum(x["size"] for x in items),
                        "entry": entry["path"] if entry else None})
    products = [x for x in products if id(x) not in drop]
    bundles.sort(key=lambda b: b["dir"])
    return products, {"from_final": from_final, "bundles": bundles}


# ---------------------------------------------------------------- dung lượng

def _task_ids():
    try:
        return sorted((n for n in os.listdir(TASKS) if not n.startswith(".") and os.path.isdir(os.path.join(TASKS, n))),
                      reverse=True)
    except OSError:
        return []


def _title(tdir, fallback):
    try:
        with open(os.path.join(tdir, "brief.md"), encoding="utf-8", errors="replace") as f:
            m = re.search(r"^#\s+(.+)$", f.read(), re.M)
        return m.group(1).strip() if m else fallback
    except OSError:
        return fallback


def _junk_size(tdir):
    total = 0
    for root, dirs, files in os.walk(tdir):
        for d in [d for d in dirs if is_junk(d, True)]:
            total += _walk_size(os.path.join(root, d))[0]
            dirs.remove(d)
        for f in files:
            if is_junk(f, False):
                try:
                    total += os.lstat(os.path.join(root, f)).st_size
                except OSError:
                    pass
    return total


def usage(busy):
    """Tổng quan: dung lượng từng task, thùng rác, ổ đĩa. busy(tid) -> True nếu task đang chạy."""
    tasks, total = [], 0
    for tid in _task_ids():
        tdir = os.path.join(TASKS, tid)
        size, n = _walk_size(tdir)
        total += size
        tasks.append({"id": tid, "title": _title(tdir, tid), "size": size, "files": n,
                      "junk": _junk_size(tdir), "busy": bool(busy(tid))})
    tasks.sort(key=lambda x: -x["size"])
    tsize, tn = _walk_size(TRASH) if os.path.isdir(TRASH) else (0, 0)
    try:
        du = shutil.disk_usage(TASKS)
        disk = {"total": du.total, "free": du.free}
    except OSError:
        disk = None
    return {"total": total, "tasks": tasks, "disk": disk,
            "trash": {"size": tsize, "count": len([n for n in os.listdir(TRASH)]) if os.path.isdir(TRASH) else 0}}


def _resolve(tid, rel):
    """Đường dẫn thật bên trong tasks/<tid>/ (không cho thoát ra ngoài)."""
    if tid not in _task_ids():
        raise RuntimeError("không có task")
    base = os.path.realpath(os.path.join(TASKS, tid))
    rel = (rel or "").strip("/")
    if rel and any(x in ("..", ".", "") for x in rel.split("/")):
        raise RuntimeError("đường dẫn không hợp lệ")
    p = os.path.join(base, rel) if rel else base
    parent = os.path.realpath(os.path.dirname(p)) if rel else base
    if parent != base and not parent.startswith(base + os.sep):
        raise RuntimeError("đường dẫn không hợp lệ")
    return base, p, rel


def dir_usage(tid, rel=""):
    """Các mục con của một thư mục trong task, lớn nhất trước."""
    base, p, rel = _resolve(tid, rel)
    if not os.path.isdir(p) or os.path.islink(p):
        raise RuntimeError("không phải thư mục")
    out = []
    for n in os.listdir(p):
        q = os.path.join(p, n)
        is_dir = os.path.isdir(q) and not os.path.islink(q)
        size, cnt = _walk_size(q)
        path = n if not rel else rel + "/" + n
        out.append({"name": n, "path": path, "dir": is_dir, "size": size, "files": cnt,
                    "protected": not rel and n in PROTECTED,
                    "junk": is_junk(n, is_dir), "tmp": bool(is_dir and TMP_HINT.match(n))})
    out.sort(key=lambda x: (-x["size"], x["name"]))
    return {"id": tid, "path": rel, "title": _title(base, tid), "entries": out}


def delete_path(tid, rel, busy):
    """Xoá vĩnh viễn một file/thư mục trong task (trừ hồ sơ của task). Trả về số byte đã giải phóng."""
    base, p, rel = _resolve(tid, rel)
    if not rel:
        raise RuntimeError("muốn xoá cả task thì dùng nút Xoá của task")
    if rel.split("/")[0] in PROTECTED:
        raise RuntimeError("đây là hồ sơ của task (yêu cầu, kết quả, báo cáo…), không xoá ở đây")
    if busy(tid):
        raise RuntimeError("task đang chạy — dừng task rồi hãy dọn")
    if not os.path.lexists(p):
        raise RuntimeError("không còn file này")
    size = _walk_size(p)[0]
    if os.path.isdir(p) and not os.path.islink(p):
        shutil.rmtree(p)
    else:
        os.remove(p)
    return size


def clean_junk(tids, busy):
    """Xoá file rác (__pycache__, .pyc, .DS_Store…) trong các task không chạy. Trả về (bytes, số task bỏ qua)."""
    freed, skipped = 0, 0
    for tid in tids:
        if busy(tid):
            skipped += 1
            continue
        for root, dirs, files in os.walk(os.path.join(TASKS, tid)):
            for d in [d for d in dirs if is_junk(d, True)]:
                q = os.path.join(root, d)
                freed += _walk_size(q)[0]
                shutil.rmtree(q, ignore_errors=True)
                dirs.remove(d)
            for f in files:
                if is_junk(f, False):
                    q = os.path.join(root, f)
                    try:
                        freed += os.lstat(q).st_size
                        os.remove(q)
                    except OSError:
                        pass
    return freed, skipped


def empty_trash():
    """Xoá vĩnh viễn mọi task trong thùng rác. Trả về số byte đã giải phóng."""
    if not os.path.isdir(TRASH):
        return 0
    freed = 0
    for n in os.listdir(TRASH):
        q = os.path.join(TRASH, n)
        freed += _walk_size(q)[0]
        if os.path.isdir(q) and not os.path.islink(q):
            shutil.rmtree(q, ignore_errors=True)
        else:
            try:
                os.remove(q)
            except OSError:
                pass
    return freed


def task_ids():
    return _task_ids()


if __name__ == "__main__":  # bin/pt_storage.py — in nhanh dung lượng
    u = usage(lambda t: False)
    for t in u["tasks"][:10]:
        print("%8.1f MB  %s" % (t["size"] / 1048576, t["id"]))
    print("Tổng %.1f MB · thùng rác %.1f MB" % (u["total"] / 1048576, u["trash"]["size"] / 1048576))
