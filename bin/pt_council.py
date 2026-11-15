"""Hội đồng: hai AI khác loại (mặc định Codex + Claude) cùng bàn một vấn đề khó, tối đa vài vòng, rồi chốt.

- Vòng 1: mỗi thành viên trả lời ĐỘC LẬP (không thấy ý của bên kia).
- Vòng 2..N: mỗi bên đọc câu trả lời mới nhất của bên kia, nhận chỗ đúng, phản biện chỗ sai, viết lại câu trả lời
  tốt nhất và kết bằng "KẾT LUẬN: ĐỒNG Ý" hoặc "KẾT LUẬN: CHƯA ĐỒNG Ý — <điểm còn bất đồng>".
  Cả hai cùng ĐỒNG Ý trong một vòng → chốt. Hết số vòng mà chưa thống nhất → báo rõ hai quan điểm và chỗ bất đồng.
- Mỗi lượt gọi đi qua bin/ask (vai trò hoi-dong, chỉ đọc), nên vẫn tự xoay tài khoản khi hết hạn mức,
  hiện trên dashboard và được tính vào trang Thống kê. Hai thành viên chạy song song trong mỗi vòng.
- Biên bản lưu ở <task>/hoi-dong/<thời điểm>.md; stdout in kết luận cho AI quản lý đọc.

Dòng lệnh (bin/council là lớp vỏ):
  bin/council [-t thư_mục_task] [-C thư_mục_đọc] [-s nho|vua|lon|sieu] [--vong N] [--thanh-vien codex,claude] "vấn đề"
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASK = os.path.join(ROOT, "bin", "ask")
TOOLS = ("codex", "claude", "gemini")
NAMES = {"codex": "Codex", "claude": "Claude", "gemini": "Gemini"}
MAX_EMBED = 15000          # độ dài tối đa câu trả lời của bên kia chép vào lời nhắn vòng sau
AGREE_RE = re.compile(r"^\W*KẾT LUẬN\W*:?\s*ĐỒNG\s*Ý\b", re.I | re.M)
DISAGREE_RE = re.compile(r"^\W*KẾT LUẬN\W*:?\s*CHƯA\s*ĐỒNG\s*Ý", re.I | re.M)


def clip(text, n=MAX_EMBED):
    text = (text or "").strip()
    return text if len(text) <= n else text[:n] + "\n…(cắt bớt %d ký tự)" % (len(text) - n)


def agreed(text):
    """Dòng KẾT LUẬN cuối cùng trong câu trả lời là ĐỒNG Ý (không phải CHƯA ĐỒNG Ý)."""
    last = None
    for m in re.finditer(r"^\W*KẾT LUẬN\W*:?.*$", text or "", re.I | re.M):
        last = m.group(0)
    return bool(last and AGREE_RE.match(last) and not DISAGREE_RE.match(last))


def ask(tool, prompt, args):
    cmd = [ASK, tool, "-r", "hoi-dong", "-s", args.s]
    if args.C:
        cmd += ["-C", args.C]
    if args.t:
        cmd += ["-t", args.t]
    cmd += ["-"]
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        return 124, "", "quá thời gian"
    return r.returncode, r.stdout.strip(), r.stderr.strip()[-600:]


def prompt_round(k, n, me, other, question, mine, theirs):
    head = ("[HỘI ĐỒNG — vòng %d/%d] Bạn (%s) là thành viên hội đồng cùng %s. Hai bên trả lời cùng một vấn đề rồi bàn "
            "tiếp để thống nhất. Bạn CHỈ ĐỌC, không sửa file.\n\nVẤN ĐỀ:\n%s\n" % (k, n, NAMES[me], NAMES[other], question))
    if k == 1:
        return head + ("\nĐây là vòng ĐỘC LẬP: bạn chưa thấy ý của bên kia. Trả lời đầy đủ, dùng được ngay; nêu lập luận "
                       "chính, phương án bạn chọn và rủi ro. Đọc file trong thư mục làm việc nếu cần để trả lời đúng.\n"
                       "Dòng cuối: QUAN ĐIỂM: <tóm tắt quan điểm của bạn trong 1 câu>")
    return head + ("\nCÂU TRẢ LỜI GẦN NHẤT CỦA BẠN:\n<<<\n%s\n>>>\n\nCÂU TRẢ LỜI GẦN NHẤT CỦA %s:\n<<<\n%s\n>>>\n\n"
                   "Việc của bạn ở vòng này:\n"
                   "1. Đọc kỹ ý của %s: điểm nào đúng thì nhận và đưa vào; điểm nào sai hoặc thiếu thì phản biện có lý do "
                   "(dẫn chứng từ file nếu có). Đừng chiều theo chỉ để cho xong — chỉ đổi ý khi có lý do.\n"
                   "2. Viết lại CÂU TRẢ LỜI TỐT NHẤT của bạn, đầy đủ (không chỉ ghi phần khác biệt).\n"
                   "3. Dòng CUỐI CÙNG phải là đúng một trong hai:\n"
                   "KẾT LUẬN: ĐỒNG Ý   (hai bên đã thống nhất các điểm chính; khác biệt nhỏ về cách diễn đạt vẫn là đồng ý)\n"
                   "KẾT LUẬN: CHƯA ĐỒNG Ý — <điểm chính còn bất đồng>"
                   % (clip(mine), NAMES[other].upper(), clip(theirs), NAMES[other]))


def pick_members(spec):
    out = []
    for m in (spec or "codex,claude").split(","):
        m = m.strip().lower()
        if m not in TOOLS:
            raise SystemExit("Lỗi: thành viên phải là codex, claude hoặc gemini (nhận được %r)" % m)
        out.append(m)
    if len(out) != 2:
        raise SystemExit("Lỗi: hội đồng cần đúng 2 thành viên, vd --thanh-vien codex,claude")
    return out


def run(args):
    members = pick_members(args.thanh_vien)
    n = max(2, min(5, args.vong))
    answers = {0: [], 1: []}      # câu trả lời từng vòng của mỗi ghế
    notes = []
    tried = {0: [members[0]], 1: [members[1]]}

    def seat_call(i, k, results):
        other = members[1 - i]
        mine = answers[i][-1] if answers[i] else ""
        theirs = answers[1 - i][-1] if answers[1 - i] else ""
        while True:
            me = members[i]
            rc, out, err = ask(me, prompt_round(k, n, me, other, args.question, mine, theirs), args)
            if rc == 0 and out:
                results[i] = out
                return
            # hết hạn mức / lỗi: thay bằng công cụ khác chưa dùng ở ghế này (ưu tiên khác loại với bên kia)
            nxt = [t for t in TOOLS if t not in tried[i] and t != other] + [t for t in TOOLS if t not in tried[i]]
            notes.append("Vòng %d: %s không trả lời được (%s)%s" % (
                k, NAMES[me], "hết hạn mức" if rc == 75 else (err.splitlines()[-1] if err else "mã %d" % rc),
                ", thay bằng %s" % NAMES[nxt[0]] if nxt else ""))
            if not nxt:
                results[i] = None
                return
            members[i] = nxt[0]
            tried[i].append(nxt[0])

    outcome, rounds = "chua", 0
    for k in range(1, n + 1):
        results = {}
        ths = [threading.Thread(target=seat_call, args=(i, k, results)) for i in (0, 1)]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        if results.get(0) is None or results.get(1) is None:
            outcome = "loi"
            for i in (0, 1):
                if results.get(i):
                    answers[i].append(results[i])
            rounds = k
            break
        answers[0].append(results[0])
        answers[1].append(results[1])
        rounds = k
        if k >= 2 and agreed(results[0]) and agreed(results[1]):
            outcome = "dong-y"
            break
    return members, answers, rounds, n, outcome, notes


def minutes(args, members, answers, rounds, n, outcome, notes):
    title = {"dong-y": "ĐỒNG THUẬN sau %d vòng" % rounds, "chua": "CHƯA THỐNG NHẤT sau %d vòng" % rounds,
             "loi": "DỪNG GIỮA CHỪNG ở vòng %d (thành viên không trả lời được)" % rounds}[outcome]
    lines = ["# Họp hội đồng: %s" % title, "",
             "- Thành viên: %s và %s" % (NAMES[members[0]], NAMES[members[1]]),
             "- Thời gian: %s · tối đa %d vòng · cỡ việc: %s" % (
                 datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), n, args.s)]
    lines += ["- " + x for x in notes]
    lines += ["", "## Vấn đề", "", args.question.strip(), ""]
    if outcome == "dong-y":
        lines += ["## Kết luận chung (bản của %s, hai bên đã đồng ý)" % NAMES[members[0]], "", answers[0][-1], ""]
    else:
        for i in (0, 1):
            if answers[i]:
                lines += ["## Quan điểm cuối của %s" % NAMES[members[i]], "", answers[i][-1], ""]
    lines += ["## Diễn biến từng vòng", ""]
    for k in range(rounds):
        for i in (0, 1):
            if k < len(answers[i]):
                lines += ["### Vòng %d — %s" % (k + 1, NAMES[members[i]]), "", answers[i][k], ""]
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(prog="bin/council", description=__doc__.split("\n\n")[0])
    p.add_argument("-t", help="thư mục task: lưu biên bản vào <task>/hoi-dong/ và từng lượt vào results/")
    p.add_argument("-C", help="thư mục thành viên được đọc (mặc định: thư mục task nếu có)")
    p.add_argument("-s", default="lon", help="cỡ việc cho model: nho | vua | lon | sieu (mặc định lon)")
    p.add_argument("--vong", type=int, default=3, help="số vòng tối đa (2-5, mặc định 3)")
    p.add_argument("--thanh-vien", dest="thanh_vien", default="codex,claude", help="2 công cụ, vd codex,claude")
    p.add_argument("--timeout", type=int, default=1500, help="giây tối đa cho mỗi lượt trả lời")
    p.add_argument("question", nargs="*", help='vấn đề cần bàn (hoặc "-" để đọc từ stdin)')
    args = p.parse_args(argv)
    q = " ".join(args.question).strip()
    args.question = sys.stdin.read() if q in ("", "-") else q
    if not args.question.strip():
        p.error("chưa có vấn đề cần bàn")
    if args.t:
        args.t = os.path.abspath(args.t)
        args.C = args.C or args.t
    members, answers, rounds, n, outcome, notes = run(args)
    text = minutes(args, members, answers, rounds, n, outcome, notes)
    path = ""
    if args.t:
        d = os.path.join(args.t, "hoi-dong")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        with open(os.path.join(args.t, "log.txt"), "a", encoding="utf-8") as f:
            f.write("%s hội đồng %s+%s: %s -> hoi-dong/%s\n" % (
                datetime.datetime.now().strftime("%H:%M:%S"), members[0], members[1],
                text.splitlines()[0].replace("# Họp hội đồng: ", ""), os.path.basename(path)))
    # stdout: cho AI quản lý — kết luận trước, diễn biến chi tiết nằm trong biên bản
    cut = text.find("## Diễn biến từng vòng")
    sys.stdout.write((text[:cut] if cut > 0 else text).rstrip() + "\n")
    if path:
        sys.stdout.write("\nBiên bản đầy đủ: %s\n" % path)
    return 0 if outcome != "loi" else 1


if __name__ == "__main__":
    sys.exit(main())
