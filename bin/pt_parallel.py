"""Chạy song song nhiều việc con, mỗi việc một nhân viên, rồi in kết quả theo đúng thứ tự.

- Mỗi việc đi qua bin/ask (vẫn tự đổi tài khoản khi hết hạn mức, hiện trên dashboard, tính vào Thống kê).
- Gọi theo tên phòng ban (claude / codex / gemini): mỗi việc được giao cho MỘT TÀI KHOẢN KHÁC NHAU — ưu tiên tài khoản
  đang rảnh và chưa chạm hạn mức — để tận dụng nhiều gói thuê bao cùng lúc thay vì dồn vào một tài khoản.
- Tối đa --toi-da việc chạy cùng lúc (mặc định 3); việc còn lại chờ tới lượt.

Đầu vào: danh sách việc dạng JSON (file -f hoặc stdin), mỗi việc:
  {"ten": "nhãn ngắn", "ai": "claude|codex|gemini|<tên nhân viên>", "viec": "nội dung việc (đủ ngữ cảnh)",
   "r": "vai trò (code/viet/tra-cuu/review…)", "s": "nho|vua|lon|sieu", "w": true/false, "C": "thư mục làm việc"}

  bin/parallel -t <thư_mục_task> [--toi-da 3] -f viec.json
Mã thoát: 0 = mọi việc xong · 1 = có việc lỗi · 75 = mọi việc đều hết hạn mức.
"""
import argparse
import datetime
import glob
import json
import os
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASK = os.path.join(ROOT, "bin", "ask")
CONF = os.environ.get("ORCH_CONF") or os.path.join(ROOT, "config", "workers.conf")
DATA = os.environ.get("ORCH_DATA") or os.path.expanduser("~/.pentagon")
TOOLS = ("claude", "codex", "gemini")
SHOW = 6000   # in tối đa bấy nhiêu ký tự mỗi kết quả; bản đầy đủ nằm trong results/


def accounts():
    """[(tên, công cụ)] theo thứ tự trong workers.conf (dòng có # là đang tắt)."""
    out = []
    try:
        lines = open(CONF, encoding="utf-8").read().splitlines()
    except OSError:
        return out
    for line in lines:
        cells = [c.strip() for c in line.split("#", 1)[0].split("|")]
        if len(cells) >= 3 and cells[0]:
            out.append((cells[0], cells[1]))
    return out


def busy_accounts():
    """Tài khoản đang có việc ở bất kỳ task nào (file đánh dấu tasks/*/running/*)."""
    busy = set()
    for f in glob.glob(os.path.join(ROOT, "tasks", "*", "running", "*")):
        try:
            for line in open(f, encoding="utf-8", errors="replace"):
                if line.startswith("worker="):
                    busy.add(line.split("=", 1)[1].strip())
        except OSError:
            pass
    return busy


def blocked(name):
    try:
        return bool(open(os.path.join(DATA, "usage", name + ".blocked"), encoding="utf-8").read().strip())
    except OSError:
        return False


def assign(jobs):
    """Chọn tài khoản cho từng việc: việc gọi theo phòng ban được rải ra các tài khoản khác nhau."""
    acc = accounts()
    names = {n for n, _ in acc}
    busy, used = busy_accounts(), {}
    for j in jobs:
        ai = j["ai"]
        if ai in names or ai not in TOOLS:
            j["acc"] = ai
            continue
        pool = [n for n, t in acc if t == ai]
        if not pool:
            j["acc"] = ai          # bin/ask sẽ báo lỗi rõ ràng
            continue
        # rảnh & chưa chạm hạn mức trước, rồi ít việc trong lô này nhất, rồi theo thứ tự trong workers.conf
        order = {n: k for k, n in enumerate(pool)}
        pool.sort(key=lambda n: (n in busy, blocked(n), used.get(n, 0), order[n]))
        j["acc"] = pool[0]
        used[pool[0]] = used.get(pool[0], 0) + 1


def load_jobs(path):
    raw = sys.stdin.read() if path in (None, "-") else open(path, encoding="utf-8").read()
    try:
        jobs = json.loads(raw)
    except ValueError as e:
        raise SystemExit("Lỗi: danh sách việc không phải JSON hợp lệ: %s" % e)
    if isinstance(jobs, dict):
        jobs = jobs.get("viec") or jobs.get("jobs") or []
    if not isinstance(jobs, list) or not jobs:
        raise SystemExit("Lỗi: cần một danh sách việc (mảng JSON) có ít nhất 1 việc")
    if len(jobs) > 12:
        raise SystemExit("Lỗi: tối đa 12 việc mỗi lần (chia thành nhiều lô)")
    out = []
    for i, j in enumerate(jobs, 1):
        if not isinstance(j, dict) or not str(j.get("viec") or j.get("prompt") or "").strip():
            raise SystemExit("Lỗi: việc thứ %d thiếu nội dung (\"viec\")" % i)
        out.append({"i": i, "ten": str(j.get("ten") or "việc %d" % i)[:60], "ai": str(j.get("ai") or "claude").strip(),
                    "viec": str(j.get("viec") or j.get("prompt")), "r": str(j.get("r") or "").strip(),
                    "s": str(j.get("s") or "").strip(), "w": bool(j.get("w")), "C": str(j.get("C") or "").strip()})
    return out


def run_job(j, args):
    cmd = [ASK, j["acc"]]
    for flag, key in (("-r", "r"), ("-s", "s"), ("-C", "C")):
        if j[key]:
            cmd += [flag, j[key]]
    if j["w"]:
        cmd.append("-w")
    if args.t:
        cmd += ["-t", args.t]
    cmd.append("-")
    start = time.time()
    try:
        r = subprocess.run(cmd, input=j["viec"], capture_output=True, text=True)
        j["rc"], j["out"], j["err"] = r.returncode, r.stdout.strip(), r.stderr.strip()
    except OSError as e:
        j["rc"], j["out"], j["err"] = 1, "", str(e)
    j["secs"] = int(time.time() - start)
    who = [l for l in j["err"].splitlines() if l.startswith("[ask]") and "xong" in l]
    j["who"] = who[-1].split()[1] if who else j["acc"]


def main(argv=None):
    p = argparse.ArgumentParser(prog="bin/parallel", description=__doc__.split("\n\n")[0])
    p.add_argument("-t", help="thư mục task (lưu kết quả từng việc vào results/)")
    p.add_argument("-f", help="file JSON danh sách việc (mặc định đọc từ stdin)")
    p.add_argument("--toi-da", dest="max", type=int, default=3, help="số việc chạy cùng lúc (1-6, mặc định 3)")
    args = p.parse_args(argv)
    if args.t:
        args.t = os.path.abspath(args.t)
    jobs = load_jobs(args.f)
    assign(jobs)
    writers = {}
    for j in jobs:
        if j["w"]:
            writers.setdefault(os.path.realpath(j["C"] or "."), []).append(j["ten"])
    for d, names in writers.items():
        if len(names) > 1:
            print("[parallel] Lưu ý: %d việc cùng được sửa file trong %s (%s) — mỗi việc phải sửa file khác nhau."
                  % (len(names), d, ", ".join(names)), file=sys.stderr)
    n = max(1, min(6, args.max))
    print("[parallel] %d việc, tối đa %d việc cùng lúc: %s" % (
        len(jobs), n, " · ".join("%s → %s" % (j["ten"], j["acc"]) for j in jobs)), file=sys.stderr, flush=True)
    if args.t:
        with open(os.path.join(args.t, "log.txt"), "a", encoding="utf-8") as f:
            f.write("%s song song %d việc (tối đa %d cùng lúc): %s\n" % (
                datetime.datetime.now().strftime("%H:%M:%S"), len(jobs), n,
                ", ".join("%s→%s" % (j["ten"], j["acc"]) for j in jobs)))
    gate = threading.Semaphore(n)

    def worker(j):
        with gate:
            run_job(j, args)
            print("[parallel] %s: %s (%ss)" % (j["ten"], "xong" if j["rc"] == 0 else "LỖI mã %d" % j["rc"], j["secs"]),
                  file=sys.stderr, flush=True)

    ths = [threading.Thread(target=worker, args=(j,)) for j in jobs]
    for th in ths:
        th.start()
        time.sleep(0.3)   # giãn nhẹ để các tài khoản không khởi động cùng một tích tắc
    for th in ths:
        th.join()
    ok = [j for j in jobs if j["rc"] == 0]
    for j in jobs:
        state = "xong" if j["rc"] == 0 else ("HẾT HẠN MỨC mọi tài khoản" if j["rc"] == 75 else "LỖI (mã %d)" % j["rc"])
        print("\n===== Việc %d/%d: %s — %s — %s, %ss =====" % (j["i"], len(jobs), j["ten"], j["who"], state, j["secs"]))
        if j["rc"] == 0:
            out = j["out"]
            print(out if len(out) <= SHOW else out[:SHOW] + "\n…(cắt bớt — bản đầy đủ trong results/ của task)")
        else:
            print("\n".join(j["err"].splitlines()[-6:]) or "(không có thông báo lỗi)")
    print("\n===== Tổng: %d/%d việc xong =====" % (len(ok), len(jobs)))
    if len(ok) == len(jobs):
        return 0
    return 75 if all(j["rc"] == 75 for j in jobs if j["rc"] != 0) and not ok else 1


if __name__ == "__main__":
    sys.exit(main())
