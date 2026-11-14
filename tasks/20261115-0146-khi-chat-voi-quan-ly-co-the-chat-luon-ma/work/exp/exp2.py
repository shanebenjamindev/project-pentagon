"""Thử nghiệm 2: tin 2 tới sát lúc lượt 1 kết thúc (sau câu trả lời, trước result) rồi đóng stdin NGAY.
Câu hỏi: claude có xử lý nốt tin 2 (ra result thứ 2) trước khi thoát không?"""
import json, os, subprocess, tempfile, time, uuid

wd = tempfile.mkdtemp(prefix="sjtest2-")
cmd = ["claude", "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose", "--model", "haiku",
       "--permission-prompts", "none", "--session-id", str(uuid.uuid4())]
p = subprocess.Popen(cmd, cwd=wd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
t0 = time.time()


def msg(t):
    return json.dumps({"type": "user", "message": {"role": "user", "content": t}}) + "\n"


p.stdin.write(msg("Trả lời đúng một từ: MOT"))
p.stdin.flush()
sent = False
results = []
for line in p.stdout:
    try:
        e = json.loads(line)
    except ValueError:
        continue
    if e.get("type") == "assistant" and not sent:
        p.stdin.write(msg("Trả lời đúng một từ: HAI"))
        p.stdin.flush()
        p.stdin.close()
        sent = True
        print("%5.1f >>> sent msg2 + closed stdin" % (time.time() - t0), flush=True)
    if e.get("type") == "result":
        results.append(e.get("result"))
        print("%5.1f result %s err=%s cost=%s usage=%s" % (time.time() - t0, e.get("result"), e.get("is_error"),
              e.get("total_cost_usd"), json.dumps(e.get("modelUsage"))[:300]), flush=True)
p.wait()
print("exit", p.returncode, "results", results)
