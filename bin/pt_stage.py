"""Quy trình (workflow) cho task: các bước có mục tiêu riêng, chuyển bước có điều kiện, có cổng kiểm tra bắt buộc.

Định nghĩa: config/workflows/<khoá>.json
  {"name": "...", "desc": "...", "stages": [
     {"key": "lam", "name": "Làm", "buoc": 4, "goal": "...", "rules": ["..."],
      "next": ["kiem-tra"],            # bước được đi tiếp ("xong" = kết thúc quy trình)
      "rework": ["lam"],               # bước được QUAY LẠI làm lại (không cần qua cổng), tối đa max_rework lần
      "max_rework": 2,
      "gate": {                        # cổng: phải đạt mới được đi tiếp (không áp cho quay lại)
        "review": true,                #   có kết quả -r review từ lúc vào bước này, lần gần nhất kết luận ĐẠT
        "khac_loai": true,             #   người review khác phòng ban với người làm gần nhất (-r code / viet)
        "khi_co": ["lon", "sieu"],     #   chỉ áp cổng review khi cỡ task thuộc danh sách này
        "council": true,               #   có biên bản hội đồng ĐỒNG THUẬN từ lúc vào bước này
        "final": true}}]}              #   final.md đã có mục "## Sản phẩm"
Trạng thái của task: <task>/workflow.json. "buoc" (1-6) tự cập nhật tiến độ trên dashboard khi vào bước.

  bin/stage <task> list                 các quy trình đang có
  bin/stage <task> start <khoá>         bắt đầu quy trình (vào bước đầu)
  bin/stage <task>                      bước hiện tại: mục tiêu, quy tắc, điều kiện còn thiếu
  bin/stage <task> <bước|xong> ["ghi chú"]   chuyển bước — bị TỪ CHỐI (mã 2) nếu chưa qua cổng / không được phép
"""
import glob
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, "config", "workflows")
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
VERDICT_RE = re.compile(r"(CHƯA\s+ĐẠT|KHÔNG\s+ĐẠT|ĐẠT)")
HEAD_RE = re.compile(r"^<!-- worker: (\S+) \((\w+)\) \| (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \|(.*?)-->", re.S)


# ---------------------------------------------------------------- định nghĩa
def validate(d, key=""):
    if not isinstance(d, dict) or not isinstance(d.get("stages"), list) or not d["stages"]:
        raise ValueError("quy trình %s cần danh sách stages" % key)
    keys = [s.get("key") for s in d["stages"]]
    if len(set(keys)) != len(keys) or not all(isinstance(k, str) and KEY_RE.match(k) for k in keys):
        raise ValueError("quy trình %s: khoá bước phải khác nhau, chỉ gồm a-z 0-9 -" % key)
    for s in d["stages"]:
        for t in list(s.get("next") or []) + list(s.get("rework") or []):
            if t != "xong" and t not in keys:
                raise ValueError("quy trình %s, bước %s: không có bước '%s'" % (key, s["key"], t))
        if not s.get("next"):
            raise ValueError("quy trình %s, bước %s: thiếu next" % (key, s["key"]))
    return d


def defs():
    out = {}
    for f in sorted(glob.glob(os.path.join(WDIR, "*.json"))):
        k = os.path.basename(f)[:-5]
        try:
            out[k] = validate(json.load(open(f, encoding="utf-8")), k)
            out[k]["key"] = k
        except (OSError, ValueError) as e:
            print("[stage] bỏ qua %s: %s" % (f, e), file=sys.stderr)
    return out


def defs_list():
    return [{"key": k, "name": d.get("name", k), "desc": d.get("desc", ""),
             "stages": [{"key": s["key"], "name": s.get("name", s["key"]), "goal": s.get("goal", ""),
                         "next": s.get("next", []), "rework": s.get("rework", []), "gate": s.get("gate") or {}}
                        for s in d["stages"]]} for k, d in defs().items()]


# ---------------------------------------------------------------- trạng thái
def spath(task):
    return os.path.join(task, "workflow.json")


def load_state(task):
    try:
        return json.load(open(spath(task), encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save_state(task, st):
    tmp = spath(task) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    os.replace(tmp, spath(task))


def stage_of(d, key):
    return next((s for s in d["stages"] if s["key"] == key), None)


# ---------------------------------------------------------------- cổng kiểm tra
def results(task):
    """[(ts, công cụ, vai trò, đường dẫn)] của các báo cáo nhân viên."""
    out = []
    for f in glob.glob(os.path.join(task, "results", "*.md")):
        try:
            head = open(f, encoding="utf-8", errors="replace").readline()
        except OSError:
            continue
        m = HEAD_RE.match(head)
        if not m:
            continue
        meta = dict(p.split(":", 1) for p in m.group(4).split(" | ") if ":" in p)
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        try:
            ts = time.mktime(time.strptime(m.group(3), "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            ts = os.path.getmtime(f)
        out.append((ts, m.group(2), meta.get("vai trò", ""), f))
    return sorted(out)


def verdict(path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""
    ans = text.split("## Trả lời", 1)[-1]
    hits = VERDICT_RE.findall(ans)
    return re.sub(r"\s+", " ", hits[-1]) if hits else ""


def task_size(task):
    try:
        return open(os.path.join(task, "manager", "size"), encoding="utf-8").read().strip()
    except OSError:
        return ""


def gate_missing(task, st, stage):
    """Danh sách điều kiện còn thiếu để rời bước hiện tại (đi tiếp)."""
    g = stage.get("gate") or {}
    miss, since = [], st.get("entered", 0)
    if g.get("review") and (not g.get("khi_co") or task_size(task) in g["khi_co"] or not task_size(task)):
        reviews = [r for r in results(task) if r[2] == "review" and r[0] >= since - 1]
        if not reviews:
            miss.append("chưa có kết quả kiểm tra (bin/ask … -r review) nào từ lúc vào bước này")
        else:
            ts, tool, _, f = reviews[-1]
            v = verdict(f)
            if v != "ĐẠT":
                miss.append("lần kiểm tra gần nhất (%s) kết luận %s — sửa rồi cho kiểm tra lại, hoặc quay lại bước làm"
                            % (os.path.relpath(f, task), v or "không rõ (không thấy chữ ĐẠT)"))
            if g.get("khac_loai"):
                makers = [r for r in results(task) if r[2] in ("code", "viet")]
                if makers and makers[-1][1] == tool:
                    miss.append("người kiểm tra (%s) cùng phòng ban với người làm (%s) — giao kiểm tra cho phòng ban khác"
                                % (tool, makers[-1][1]))
    if g.get("council"):
        ok = False
        for f in glob.glob(os.path.join(task, "hoi-dong", "*.md")):
            try:
                if os.path.getmtime(f) >= since - 1 and "ĐỒNG THUẬN" in open(f, encoding="utf-8").readline():
                    ok = True
            except OSError:
                pass
        if not ok:
            miss.append("chưa có biên bản hội đồng ĐỒNG THUẬN (bin/council) từ lúc vào bước này")
    if g.get("final"):
        try:
            final = open(os.path.join(task, "final.md"), encoding="utf-8").read()
        except OSError:
            final = ""
        if not final.strip():
            miss.append("chưa có final.md")
        elif not re.search(r"^##\s*Sản phẩm", final, re.M | re.I):
            miss.append("final.md chưa có mục '## Sản phẩm'")
    return miss


# ---------------------------------------------------------------- xem / chuyển bước
def view(task):
    """Cho web: quy trình của task, bước nào xong / đang làm, điều kiện còn thiếu."""
    st = load_state(task)
    if not st:
        return None
    d = defs().get(st.get("key"))
    if not d:
        return {"key": st.get("key"), "name": st.get("name", st.get("key")), "missing_def": True, "stages": []}
    visited = {h["stage"] for h in st.get("history", [])}
    cur = st.get("stage")
    stages = []
    for s in d["stages"]:
        stages.append({"key": s["key"], "name": s.get("name", s["key"]), "goal": s.get("goal", ""),
                       "state": "dang" if s["key"] == cur and not st.get("done") else
                       ("xong" if s["key"] in visited or st.get("done") else "chua"),
                       "rework": st.get("rework", {}).get(s["key"], 0), "gate": bool(s.get("gate"))})
    s = stage_of(d, cur)
    return {"key": st["key"], "name": d.get("name"), "stage": cur, "done": bool(st.get("done")),
            "entered": st.get("entered"), "stages": stages,
            "missing": gate_missing(task, st, s) if s and not st.get("done") else [],
            "history": st.get("history", [])[-30:]}


def describe(d, s, st, task):
    lines = ["Quy trình %s — bước: %s (%s)" % (d.get("name"), s.get("name"), s["key"]),
             "Mục tiêu: %s" % s.get("goal", "")]
    lines += ["- " + r for r in s.get("rules", [])]
    nxt = ", ".join(s.get("next", []))
    lines.append("Đi tiếp: bin/stage %s <%s>" % (task, nxt))
    if s.get("rework"):
        lines.append("Quay lại làm lại (tối đa %d lần): %s — đã quay lại: %s" % (
            s.get("max_rework", 2), ", ".join(s["rework"]),
            ", ".join("%s %d lần" % (k, st.get("rework", {}).get(k, 0)) for k in s["rework"])))
    miss = gate_missing(task, st, s)
    if s.get("gate"):
        lines.append("Cổng để đi tiếp: " + ("ĐÃ ĐẠT" if not miss else "còn thiếu:\n  * " + "\n  * ".join(miss)))
    return "\n".join(lines)


def log(task, text):
    try:
        with open(os.path.join(task, "log.txt"), "a", encoding="utf-8") as f:
            f.write("%s quy trình: %s\n" % (time.strftime("%H:%M:%S"), text))
    except OSError:
        pass


def enter(task, d, st, key, note="", rework=False):
    st.setdefault("history", []).append({"stage": key, "at": int(time.time()), "note": note, "rework": rework})
    st["stage"], st["entered"] = key, int(time.time())
    if key == "xong":
        st["done"] = True
    save_state(task, st)
    if key == "xong":
        log(task, "%s — hoàn tất%s" % (d.get("name"), (": " + note) if note else ""))
        return
    s = stage_of(d, key)
    log(task, "%s → %s%s%s" % (d.get("name"), s.get("name"), " (làm lại)" if rework else "", (": " + note) if note else ""))
    if s.get("buoc"):
        subprocess.run([os.path.join(ROOT, "bin", "progress"), task, str(s["buoc"]),
                        "%s: %s" % (d.get("name"), s.get("name"))], capture_output=True)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    task = os.path.abspath(argv.pop(0))
    if not os.path.isdir(task):
        print("Lỗi: không có thư mục task %s" % task, file=sys.stderr)
        return 1
    all_defs = defs()
    cmd = argv.pop(0) if argv else ""
    if cmd == "list":
        for k, d in all_defs.items():
            print("%-12s %s — %s\n             bước: %s" % (k, d.get("name"), d.get("desc", ""),
                                                          " → ".join(s.get("name", s["key"]) for s in d["stages"])))
        return 0
    st = load_state(task)
    if cmd == "start":
        key = argv[0] if argv else ""
        if key not in all_defs:
            print("Lỗi: không có quy trình '%s'. Có: %s" % (key, ", ".join(all_defs)), file=sys.stderr)
            return 1
        if st and not st.get("done") and "--force" not in argv:
            print("Lỗi: task đang theo quy trình '%s' (bước %s). Thêm --force để đổi quy trình." % (
                st.get("key"), st.get("stage")), file=sys.stderr)
            return 2
        d = all_defs[key]
        st = {"key": key, "name": d.get("name"), "started": int(time.time()), "rework": {}, "history": []}
        log(task, "bắt đầu %s" % d.get("name"))
        enter(task, d, st, d["stages"][0]["key"])
        print(describe(d, d["stages"][0], st, task))
        return 0
    if not st:
        print("Task chưa theo quy trình nào. Bắt đầu: bin/stage %s start <khoá> (xem: bin/stage %s list)" % (task, task))
        return 0 if not cmd else 1
    d = all_defs.get(st.get("key"))
    if not d:
        print("Lỗi: không còn định nghĩa quy trình '%s' trong config/workflows/" % st.get("key"), file=sys.stderr)
        return 1
    if st.get("done"):
        print("Quy trình %s đã hoàn tất." % d.get("name"))
        return 0 if not cmd else 1
    s = stage_of(d, st["stage"])
    if not cmd:
        print(describe(d, s, st, task))
        return 0
    note = " ".join(argv).strip()
    if cmd in (s.get("rework") or []):
        n = st.setdefault("rework", {}).get(cmd, 0)
        if n >= int(s.get("max_rework", 2)):
            print("TỪ CHỐI: đã quay lại bước '%s' %d lần (tối đa %d). Quản lý tự sửa ở bước này rồi cho kiểm tra lại."
                  % (cmd, n, int(s.get("max_rework", 2))), file=sys.stderr)
            return 2
        st["rework"][cmd] = n + 1
        enter(task, d, st, cmd, note, rework=True)
        print(describe(d, stage_of(d, cmd), st, task))
        return 0
    if cmd not in (s.get("next") or []):
        print("TỪ CHỐI: từ bước '%s' chỉ được đi tới: %s%s." % (
            s["key"], ", ".join(s.get("next") or []),
            (" (hoặc quay lại: %s)" % ", ".join(s["rework"])) if s.get("rework") else ""), file=sys.stderr)
        return 2
    miss = gate_missing(task, st, s)
    if miss:
        print("TỪ CHỐI: chưa qua cổng của bước '%s':\n  * %s" % (s.get("name"), "\n  * ".join(miss)), file=sys.stderr)
        return 2
    enter(task, d, st, cmd, note)
    if cmd == "xong":
        print("Quy trình %s hoàn tất. Nhớ bin/progress %s xong \"...\"." % (d.get("name"), task))
    else:
        print(describe(d, stage_of(d, cmd), st, task))
    return 0


if __name__ == "__main__":
    sys.exit(main())
