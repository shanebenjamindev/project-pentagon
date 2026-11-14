#!/usr/bin/env python3
"""Theo dõi tiến độ task của Pentagon. Chỉ dùng thư viện chuẩn của Python 3.

  python3 bin/tracker.py status [-a] [-w [giây]] [task]   (bin/status)
  python3 bin/tracker.py dashboard [--port N] [--open]    (bin/dashboard — web app, xem pt_web.py)
  python3 bin/tracker.py manager ...                      (bin/manager — chạy AI quản lý nền, xem pt_manager.py)

Đọc từ mỗi thư mục tasks/<id>/:
  brief.md, plan.md, final.md   — do AI quản lý viết
  status                        — bước hiện tại, do bin/progress ghi
  log.txt                       — nhật ký, do bin/ask và bin/progress ghi
  running/<pid>                 — worker đang chạy, do bin/ask tạo và tự xoá khi xong
  results/*.md                  — câu trả lời của từng worker
  manager/                      — phiên AI quản lý chạy nền từ web (session, pid, stream.jsonl)
"""
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(ROOT, "tasks")
STEPS = ["Tiếp nhận", "Tối ưu yêu cầu", "Lập kế hoạch", "Giao việc", "Kiểm tra", "Tổng hợp"]
STATE_LABEL = {"dang-lam": "Đang làm", "cho": "Chờ chủ", "xong": "Hoàn thành", "loi": "Dừng/lỗi"}


# ---------------------------------------------------------------- đọc dữ liệu task

def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def kv(path):
    d = {}
    for line in (read(path) or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except PermissionError:
        return True
    except (OSError, ValueError):
        return False


def running_workers(tdir):
    out = []
    rdir = os.path.join(tdir, "running")
    if not os.path.isdir(rdir):
        return out
    for n in sorted(os.listdir(rdir)):
        p = os.path.join(rdir, n)
        d = kv(p)
        if not d.get("pid") or not pid_alive(d["pid"]):
            try:  # bin/ask bị giết đột ngột nên chưa kịp dọn
                os.remove(p)
            except OSError:
                pass
            continue
        try:
            d["started"] = int(d.get("started") or 0)
        except ValueError:
            d["started"] = 0
        out.append(d)
    return out


LOG_RE = re.compile(r"^(\d\d:\d\d:\d\d) (\S+) ?(.*)$")


def parse_log(text):
    items = []
    for line in (text or "").splitlines():
        if not line.strip():
            continue
        m = LOG_RE.match(line)
        if not m:
            items.append({"time": "", "who": "", "kind": "info", "text": line})
            continue
        t, who, rest = m.groups()
        if who == "quan-ly":
            kind = "manager"
        elif rest.startswith("START"):
            kind = "start"
        elif rest.startswith("ok"):
            kind = "ok"
        elif rest.startswith("FAIL"):
            kind = "fail"
        else:
            kind = "info"
        items.append({"time": t, "who": who, "kind": kind, "text": rest})
    return items


HDR_RE = re.compile(r"<!-- worker: (\S+) \((\w+)\) \| ([^|]+) \| (\d+)s \| quyền: ([^|]+) \|")


def list_results(tdir):
    rdir = os.path.join(tdir, "results")
    out = []
    if not os.path.isdir(rdir):
        return out
    for n in sorted(os.listdir(rdir)):
        p = os.path.join(rdir, n)
        if not os.path.isfile(p):
            continue
        head = (read(p) or "")[:400]
        m = HDR_RE.search(head)
        item = {"file": "results/" + n, "name": n, "size": os.path.getsize(p),
                "mtime": int(os.path.getmtime(p))}
        if m:
            item.update(worker=m.group(1), tool=m.group(2), at=m.group(3).strip(),
                        secs=int(m.group(4)), perm=m.group(5).strip())
        out.append(item)
    return out


def plan_progress(plan):
    """(số việc con đã xong, tổng số) đếm từ cột cuối bảng trong plan.md."""
    rows = [l for l in (plan or "").splitlines() if l.strip().startswith("|")]
    rows = [r for r in rows[2:] if r.strip("| \t-")]  # bỏ dòng tiêu đề và dòng ---
    done = 0
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        last = cells[-1].lower() if cells else ""
        if last.startswith("xong") or last.startswith("đạt") or "✅" in last or last.startswith("done"):
            done += 1
    return done, len(rows)


def manager_info(tdir):
    mdir = os.path.join(tdir, "manager")
    sid = (read(os.path.join(mdir, "session")) or "").strip()
    st = kv(os.path.join(mdir, "pid"))
    alive = bool(st.get("pid")) and pid_alive(st["pid"])
    try:
        started = int(st.get("started") or 0)
    except ValueError:
        started = 0
    f = lambda n: (read(os.path.join(mdir, n)) or "").strip()
    retry = f("retry_at")
    return {"session": sid, "running": alive, "pid": int(st["pid"]) if alive else 0,
            "started": started if alive else 0, "begun": os.path.exists(os.path.join(mdir, "begun")),
            "pending": f("pending"), "size": f("size"), "model": f("model"), "split": f("split"),
            "account": f("account"), "retry_at": int(retry) if retry.isdigit() else 0}


def newest_mtime(tdir):
    m = 0
    for sub in ("", "results", "running", "manager"):
        d = os.path.join(tdir, sub)
        if not os.path.isdir(d):
            continue
        for n in os.listdir(d):
            try:
                m = max(m, int(os.path.getmtime(os.path.join(d, n))))
            except OSError:
                pass
    return m


def task_ids():
    if not os.path.isdir(TASKS):
        return []
    ids = [n for n in os.listdir(TASKS) if os.path.isdir(os.path.join(TASKS, n)) and not n.startswith(".")]
    return sorted(ids, reverse=True)


def created_of(tid):
    m = re.match(r"(\d{4})(\d\d)(\d\d)-(\d\d)(\d\d)", tid)
    return "%s-%s-%s %s:%s" % m.groups() if m else ""


def summary(tid, with_docs=False):
    tdir = os.path.join(TASKS, tid)
    brief = read(os.path.join(tdir, "brief.md")) or ""
    plan = read(os.path.join(tdir, "plan.md")) or ""
    final = read(os.path.join(tdir, "final.md"))
    log = parse_log(read(os.path.join(tdir, "log.txt")))
    st = kv(os.path.join(tdir, "status"))
    run = running_workers(tdir)
    results = list_results(tdir)
    pdone, ptotal = plan_progress(plan)

    m = re.search(r"^#\s+(.+)$", brief, re.M)
    title = m.group(1).strip() if m else tid

    if st.get("step"):
        try:
            step = max(1, min(6, int(st["step"])))
        except ValueError:
            step = 1
        state = st.get("state") or "dang-lam"
    else:  # task cũ chưa có file status: đoán từ các file đã có
        state = "dang-lam"
        if final and final.strip():
            step, state = 6, "xong"
        elif results or run:
            step = 4 if run else 5
        elif ptotal:
            step = 3
        elif re.search(r"^- Mục tiêu:[ \t]*\S", brief, re.M):
            step = 2
        else:
            step = 1

    info = {
        "id": tid, "title": title, "created": created_of(tid),
        "step": step, "step_label": STEPS[step - 1],
        "state": state, "state_label": STATE_LABEL.get(state, state),
        "note": st.get("note", ""),
        "updated": newest_mtime(tdir),
        "running": run,
        "results_count": len(results),
        "fails": sum(1 for i in log if i["kind"] == "fail"),
        "plan_done": pdone, "plan_total": ptotal,
        "last_log": log[-1] if log else None,
        "has_final": bool(final and final.strip()),
        "manager": manager_info(tdir),
    }
    if with_docs:
        info.update(brief=brief, plan=plan, final=final or "", log=log, results=results)
    return info


def resolve_task(arg):
    ids = task_ids()
    if not ids:
        return None
    if arg in ("", "latest", "moi", "mới"):
        return ids[0]
    base = os.path.basename(os.path.normpath(arg))
    if base in ids:
        return base
    hits = [i for i in ids if arg.lower() in i.lower()]
    return hits[0] if hits else None


# ---------------------------------------------------------------- bin/status

USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def c(code, s):
    return "\033[%sm%s\033[0m" % (code, s) if USE_COLOR else s


STATE_COLOR = {"dang-lam": "36", "cho": "33", "xong": "32", "loi": "31"}
KIND_COLOR = {"manager": "35", "start": "36", "ok": "32", "fail": "31", "info": "0"}


def dur(secs):
    secs = max(0, int(secs))
    if secs < 60:
        return "%ds" % secs
    if secs < 3600:
        return "%dm%02ds" % (secs // 60, secs % 60)
    return "%dh%02dm" % (secs // 3600, secs % 3600 // 60)


def ago(ts):
    if not ts:
        return "?"
    d = time.time() - ts
    if d < 60:
        return "vừa xong"
    if d < 3600:
        return "%d phút trước" % (d // 60)
    if d < 86400:
        return "%d giờ trước" % (d // 3600)
    return time.strftime("%d/%m %H:%M", time.localtime(ts))


def steps_bar(step, state):
    if state == "xong":
        return c("32", "●" * 6)
    cur = c(STATE_COLOR.get(state, "36"), "◉")
    return c("32", "●" * (step - 1)) + cur + "○" * (6 - step)


def state_text(t):
    if t["state"] == "dang-lam":
        txt = "Bước %d/6 · %s" % (t["step"], t["step_label"])
    elif t["state"] == "xong":
        txt = "HOÀN THÀNH"
    else:
        txt = "%s (bước %d · %s)" % (t["state_label"].upper(), t["step"], t["step_label"])
    return c(STATE_COLOR.get(t["state"], "0") + ";1", txt)


def print_running(run, indent="  "):
    now = time.time()
    for r in run:
        print(indent + c("36;1", "▶ %s" % r.get("worker", "?")) +
              c("2", " (%s, %s) %s" % (r.get("tool", "?"), r.get("perm", "?"), dur(now - r["started"]))) +
              " — " + r.get("summary", "")[:90])


def print_list(show_all):
    ids = task_ids()
    if not ids:
        print("Chưa có task nào. Giao task bằng /giao trong Claude Code.")
        return
    tasks = [summary(i) for i in ids]
    active = [t for t in tasks if t["state"] != "xong" or t["running"]]
    shown = tasks if show_all else (active + [t for t in tasks if t not in active])[:max(10, len(active))]
    nrun = sum(len(t["running"]) for t in tasks)
    print(c("1", "PENTAGON") + c("2", "  %d task · %d đang làm · %d worker đang chạy · %s" % (
        len(tasks), len(active), nrun, time.strftime("%H:%M:%S"))))
    print()
    for t in shown:
        print("%s  %s  %s" % (steps_bar(t["step"], t["state"]), c("1", t["title"]), c("2", t["id"])))
        bits = [state_text(t)]
        if t["plan_total"]:
            bits.append("việc con %d/%d xong" % (t["plan_done"], t["plan_total"]))
        bits.append("%d kết quả" % t["results_count"])
        if t["fails"]:
            bits.append(c("31", "%d lần lỗi" % t["fails"]))
        bits.append("cập nhật " + ago(t["updated"]))
        print("        " + " · ".join(bits))
        if t["note"]:
            print("        " + c("2", "↳ " + t["note"][:110]))
        print_running(t["running"], "        ")
        print()
    if len(shown) < len(tasks):
        print(c("2", "(còn %d task cũ — xem tất cả: bin/status -a)" % (len(tasks) - len(shown))))
    print(c("2", "Chi tiết 1 task: bin/status <id>   ·   Tự làm mới: bin/status -w   ·   Giao diện web: bin/dashboard"))


def print_detail(tid):
    t = summary(tid, with_docs=True)
    print(c("1", t["title"]) + c("2", "   " + t["id"] + " · tạo " + t["created"]))
    print("%s  %s" % (steps_bar(t["step"], t["state"]), state_text(t)))
    print("    " + "  ".join(
        c("32" if (i + 1 < t["step"] or t["state"] == "xong") else ("1" if i + 1 == t["step"] else "2"),
          "%d.%s" % (i + 1, s)) for i, s in enumerate(STEPS)))
    if t["note"]:
        print(c("2", "↳ " + t["note"]))
    print()
    if t["running"]:
        print(c("1", "Đang chạy"))
        print_running(t["running"])
        print()
    plan_rows = [l for l in t["plan"].splitlines() if l.strip().startswith("|")]
    if len(plan_rows) > 2:
        print(c("1", "Kế hoạch") + c("2", "  (%d/%d việc con xong)" % (t["plan_done"], t["plan_total"])))
        for l in plan_rows:
            print("  " + l)
        print()
    if t["results"]:
        print(c("1", "Kết quả worker"))
        for r in t["results"]:
            meta = "%s, %ss, quyền %s" % (r.get("worker", "?"), r.get("secs", "?"), r.get("perm", "?")) \
                if r.get("worker") else "%d byte" % r["size"]
            print("  %s  %s" % (r["file"], c("2", meta)))
        print()
    print(c("1", "Nhật ký") + c("2", "  (mới nhất ở dưới)"))
    for i in t["log"][-20:]:
        print("  " + c("2", i["time"]) + " " + c(KIND_COLOR[i["kind"]], i["who"]) + " " + i["text"][:140])
    if not t["log"]:
        print(c("2", "  (trống)"))
    print()
    print(c("2", "File: tasks/%s/  ·  kết quả cuối: %s" % (t["id"], "final.md" if t["has_final"] else "chưa có")))


def cmd_status(argv):
    show_all, watch, target = False, 0, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-a", "--all"):
            show_all = True
        elif a in ("-w", "--watch"):
            watch = 3
            if i + 1 < len(argv) and argv[i + 1].isdigit():
                watch = max(1, int(argv[i + 1]))
                i += 1
        elif a in ("-h", "--help"):
            print("Cách dùng: bin/status [-a] [-w [giây]] [task]\n"
                  "  (không có task)  danh sách task và tiến độ\n"
                  "  task             id, một phần id, hoặc 'latest' — xem chi tiết\n"
                  "  -a               hiện cả các task cũ\n"
                  "  -w [giây]        tự làm mới (mặc định 3 giây), Ctrl+C để thoát")
            return 0
        else:
            target = a
        i += 1
    tid = None
    if target is not None:
        tid = resolve_task(target)
        if not tid:
            print("Không tìm thấy task: %s" % target, file=sys.stderr)
            return 1

    def draw():
        print_detail(tid) if tid else print_list(show_all)

    if not watch:
        draw()
        return 0
    try:
        while True:
            sys.stdout.write("\033[H\033[2J")
            draw()
            print(c("2", "\nTự làm mới mỗi %ds — Ctrl+C để thoát" % watch))
            sys.stdout.flush()
            time.sleep(watch)
    except KeyboardInterrupt:
        print()
    return 0


# ---------------------------------------------------------------- điểm vào

def main():
    cmds = ("status", "dashboard", "manager")
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        return 1
    if sys.argv[1] == "status":
        return cmd_status(sys.argv[2:])
    if sys.argv[1] == "dashboard":
        import pt_web
        return pt_web.cmd_dashboard(sys.argv[2:])
    import pt_manager
    return pt_manager.cmd_manager(sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
