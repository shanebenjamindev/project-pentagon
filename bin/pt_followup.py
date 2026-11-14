"""Hỏi tiếp một subagent về kết quả nó đã làm, KHÔNG làm rối phiên của nó.

- Claude: chạy trên BẢN SAO của phiên cũ (claude --resume <phiên> --fork-session): subagent nhớ đầy đủ việc đã làm,
  còn phiên gốc và file kết quả gốc giữ nguyên.
- Codex / kết quả cũ chưa ghi mã phiên: chạy phiên mới, kèm việc đã giao + câu trả lời cũ làm ngữ cảnh.
- Luôn chỉ được đọc (không sửa file). Câu trả lời lưu thành results/<worker>-<giờ>.md có trường "hỏi tiếp: <file gốc>".
"""
import os
import re
import shlex
import time

import tracker
from tracker import ROOT, TASKS, read

DATA = os.environ.get("ORCH_DATA") or os.path.expanduser("~/.pentagon")
QUESTION_RE = re.compile(r"## Câu hỏi tiếp\n(.*?)\n\n\(Chỉ trả lời", re.S)


def question_of(text):
    m = QUESTION_RE.search(text or "")
    return m.group(1).strip() if m else ""


def _sections(text):
    task = re.search(r"## Việc được giao\n\n(.*?)\n\n## Trả lời\n", text, re.S)
    ans = text.split("\n## Trả lời\n", 1)
    return (task.group(1).strip() if task else ""), (ans[1].strip() if len(ans) > 1 else text)


def start(tid, rel, question):
    import pt_manager  # dùng chung hàm chạy tách hẳn khỏi dashboard
    question = (question or "").strip()
    if not question:
        raise RuntimeError("câu hỏi đang trống")
    if tid not in tracker.task_ids():
        raise RuntimeError("không có task")
    items = {r["file"]: r for r in tracker.list_results(os.path.join(TASKS, tid))}
    item = items.get(rel)
    if not item or not item.get("worker"):
        raise RuntimeError("không có kết quả này")
    root = item.get("followup_of") or rel  # hỏi tiếp trên một câu hỏi tiếp: vẫn bám kết quả gốc
    root_item = items.get(root, item)
    text = read(os.path.join(TASKS, tid, root)) or ""
    task_text, answer = _sections(text)
    # nếu đang hỏi tiếp trên một câu trả lời hỏi tiếp, đưa cả câu trả lời đó vào ngữ cảnh
    extra = ""
    if rel != root:
        t2 = read(os.path.join(TASKS, tid, rel)) or ""
        extra = "\n\n## Câu hỏi tiếp trước đó\n%s\n\n## Trả lời khi đó\n%s" % (question_of(t2), _sections(t2)[1][:6000])
    prompt = ("Đây là câu HỎI TIẾP về một phần việc đã làm xong. Không làm lại việc cũ, không sửa file nào.\n\n"
              "## Việc đã giao khi đó\n%s\n\n## Câu trả lời khi đó\n%s%s\n\n## Câu hỏi tiếp\n%s\n\n"
              "(Chỉ trả lời câu hỏi tiếp ở trên, ngắn gọn và cụ thể.)" % (
                  task_text[:6000], answer[:12000], extra, question))
    pdir = os.path.join(TASKS, tid, "prompts")
    os.makedirs(pdir, exist_ok=True)
    pf = os.path.join(pdir, "hoi-tiep-%d.txt" % int(time.time() * 1000))
    with open(pf, "w", encoding="utf-8") as f:
        f.write(prompt)

    worker = root_item["worker"]
    names = [r[0] for r in pt_manager.conf_rows(pt_manager.WORKERS)]
    target = worker if worker in names else root_item.get("tool") or "claude"
    wd = root_item.get("wd") or ""
    if not wd or not os.path.isdir(wd):
        wd = os.path.join(DATA, "workspace")
    cmd = [os.path.join(ROOT, "bin", "ask"), target, "-t", os.path.join(TASKS, tid), "-C", wd,
           "--followup-of", root, "-s", "nho"]
    if root_item.get("role"):
        cmd += ["-r", root_item["role"]]
    if root_item.get("tool") == "claude" and root_item.get("session") and target == worker:
        cmd += ["--fork", root_item["session"]]
    cmd.append("-")
    log = os.path.join(DATA, "hoi-tiep.log")
    os.makedirs(DATA, exist_ok=True)
    shell = "exec %s < %s" % (shlex.join(cmd), shlex.quote(pf))
    return pt_manager.spawn_detached(["/bin/sh", "-c", shell], log)


def agents_view():
    """Màn quản lý agent: mọi quản lý + subagent đang chạy, và các kết quả vừa xong (để hỏi tiếp)."""
    running, recent = [], []
    now = time.time()
    for tid in tracker.task_ids():
        tdir = os.path.join(TASKS, tid)
        if now - tracker.newest_mtime(tdir) > 3 * 86400:
            continue
        t = tracker.summary(tid)
        m = t["manager"]
        if m["running"] or m["pending"]:
            running.append({"kind": "manager", "name": "AI quản lý", "task": tid, "title": t["title"],
                            "role": "điều phối", "summary": "Bước %d/6 · %s" % (t["step"], t["step_label"]),
                            "started": m["started"], "model": m["model"], "account": m["account"],
                            "pid": m["pid"], "pending": m["pending"]})
        for r in t["running"]:
            running.append({"kind": "worker", "name": r.get("worker", "?"), "task": tid, "title": t["title"],
                            "role": r.get("role", ""), "followup": r.get("followup", ""),
                            "summary": r.get("summary", ""), "started": r["started"], "model": r.get("model", ""),
                            "pid": r.get("pid"), "perm": r.get("perm", "")})
        for r in tracker.list_results(tdir):
            if r.get("worker"):
                recent.append(dict(r, task=tid, title=t["title"]))
    recent.sort(key=lambda r: r["mtime"], reverse=True)
    return {"now": int(now), "running": running, "recent": recent[:40]}
