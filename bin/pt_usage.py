"""Thống kê usage của từng AI (tài khoản) cho web app — không tốn thêm lượt gọi nào.

Nguồn dữ liệu:
- Claude: mỗi lần chạy (worker qua bin/ask, hoặc AI quản lý) Claude Code báo rate_limit_event
  (% đã dùng của khung 5 giờ / 7 ngày, giờ làm mới) và token đã dùng. Pentagon ghi lại vào
  ~/.pentagon/usage/<tên>.json.
- Codex: đọc nhật ký phiên của chính Codex (<CODEX_HOME>/sessions/**/rollout-*.jsonl): % hạn mức, token.
- Gemini: chưa có nguồn — chỉ có số liệu Pentagon tự đếm (số việc, thời gian, lỗi).

Dòng lệnh nội bộ (bin/ask dùng):
  python3 bin/pt_usage.py claude-out <tên_worker> <file_stream_json>
      in phần trả lời cuối ra stdout và ghi lại usage của lần chạy.
"""
import glob
import json
import os
import sys
import time

DATA = os.environ.get("ORCH_DATA") or os.path.expanduser("~/.pentagon")
UDIR = os.path.join(DATA, "usage")


def _load(name):
    try:
        with open(os.path.join(UDIR, name + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save(name, d):
    os.makedirs(UDIR, exist_ok=True)
    tmp = os.path.join(UDIR, ".%s.%d.tmp" % (name, os.getpid()))
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, os.path.join(UDIR, name + ".json"))


def record_claude_events(name, events):
    """Ghi rate limit + token từ các sự kiện stream-json của một lần chạy Claude."""
    rate, tokens, cost, calls = None, 0, 0.0, 0
    for e in events:
        t = e.get("type")
        if t == "rate_limit_event":
            rate = e.get("rate_limit_info") or rate
        elif t == "result":
            calls += 1
            cost += float(e.get("total_cost_usd") or 0)
            for m in (e.get("modelUsage") or {}).values():
                tokens += sum(int(m.get(k) or 0) for k in ("inputTokens", "outputTokens",
                                                            "cacheReadInputTokens", "cacheCreationInputTokens"))
            if not e.get("modelUsage"):
                u = e.get("usage") or {}
                tokens += sum(int(u.get(k) or 0) for k in ("input_tokens", "output_tokens",
                                                           "cache_read_input_tokens", "cache_creation_input_tokens"))
    if rate is None and not calls:
        return
    d = _load(name)
    if rate is not None:
        d["rate"], d["rate_at"] = rate, int(time.time())
    day = time.strftime("%Y-%m-%d")
    days = d.setdefault("days", {})
    cur = days.setdefault(day, {"calls": 0, "tokens": 0, "cost": 0.0})
    cur["calls"] += calls
    cur["tokens"] += tokens
    cur["cost"] = round(cur["cost"] + cost, 4)
    for k in sorted(days)[:-14]:  # chỉ giữ 14 ngày
        days.pop(k, None)
    _save(name, d)


def read_events(path, offset=0):
    out = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            f.seek(offset)
            for line in f:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


def claude_out(name, path):
    """Cho bin/ask: in câu trả lời cuối (dạng text) từ stream-json, đồng thời ghi usage."""
    events = read_events(path)
    try:
        record_claude_events(name, events)
    except Exception:  # thống kê lỗi không được làm hỏng việc chính
        pass
    text = ""
    for e in events:
        if e.get("type") == "result":
            text = str(e.get("result") or "")
    if not text:  # không có result (bị ngắt): ghép các đoạn trả lời đã có, để bin/ask giữ phần làm dở
        parts = []
        for e in events:
            if e.get("type") == "assistant" and not e.get("parent_tool_use_id"):
                for b in (e.get("message") or {}).get("content") or []:
                    if b.get("type") == "text":
                        parts.append(b.get("text", ""))
        text = "\n".join(parts)
    if not events:  # không phải JSON (lỗi sớm): trả nguyên văn
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            pass
    sys.stdout.write(text)


def codex_usage(home):
    """Đọc % hạn mức và token hôm nay từ nhật ký phiên của Codex."""
    base = os.path.join(home or os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex"), "sessions")
    files = sorted(glob.glob(os.path.join(base, "*", "*", "*", "rollout-*.jsonl")), key=os.path.getmtime)
    if not files:
        return {}
    today = time.strftime("%Y/%m/%d")
    tokens, calls, rate, rate_at = 0, 0, None, 0
    for f in files[-200:]:
        last_tok, last_rate = 0, None
        for e in read_events(f):
            p = e.get("payload") or {}
            if p.get("type") == "token_count":
                info = p.get("info") or {}
                last_tok = int(((info.get("total_token_usage") or {}).get("total_tokens")) or last_tok)
                last_rate = p.get("rate_limits") or last_rate
        if today in f.replace(os.sep, "/"):
            tokens += last_tok
            calls += 1
        if last_rate:
            rate, rate_at = last_rate, int(os.path.getmtime(f))
    out = {"days": {time.strftime("%Y-%m-%d"): {"calls": calls, "tokens": tokens}}}
    if rate:
        wins = []
        for key in ("primary", "secondary"):
            w = rate.get(key)
            if w:
                wins.append({"label": _win_label(w.get("window_minutes")), "used": w.get("used_percent"),
                             "resets_at": w.get("resets_at")})
        out.update(windows=wins, plan=rate.get("plan_type"), limited=bool(rate.get("rate_limit_reached_type")),
                   rate_at=rate_at)
    return out


def _win_label(minutes):
    try:
        m = int(minutes)
    except (TypeError, ValueError):
        return "hạn mức"
    if m % 1440 == 0:
        return "%d ngày" % (m // 1440)
    if m % 60 == 0:
        return "%d giờ" % (m // 60)
    return "%d phút" % m


def claude_usage(name):
    d = _load(name)
    out = {"days": d.get("days", {})}
    r = d.get("rate")
    if r:
        wins = []
        uw = r.get("unifiedWindows") or {}
        for key, label in (("five_hour", "5 giờ"), ("seven_day", "7 ngày"), ("seven_day_opus", "7 ngày (Opus)")):
            w = uw.get(key)
            if w:
                u = w.get("utilization")
                wins.append({"label": label, "used": round(u * 100, 1) if isinstance(u, (int, float)) else None,
                             "resets_at": w.get("resetsAt"), "status": w.get("status")})
        if not wins and r.get("resetsAt"):
            wins.append({"label": r.get("rateLimitType", "hạn mức"), "used": None, "resets_at": r.get("resetsAt"),
                         "status": r.get("status")})
        out.update(windows=wins, limited=r.get("status") not in (None, "allowed", "allowed_warning"),
                   rate_at=d.get("rate_at", 0))
    return out


def apply_resets(u):
    """Đã qua giờ làm mới của một khung hạn mức mà chưa có lần chạy mới -> khung đó về 0% (thay vì giữ số cũ)."""
    now = time.time()
    any_reset = False
    for w in u.get("windows") or []:
        r = w.get("resets_at")
        try:
            r = float(r)
        except (TypeError, ValueError):
            continue
        if r and r <= now and (u.get("rate_at") or 0) < r:
            w["used"], w["reset"], w["status"] = 0, True, "allowed"
            any_reset = True
    if any_reset and u.get("limited"):
        u["limited"] = any(w.get("status") not in (None, "allowed", "allowed_warning") and not w.get("reset")
                           for w in u.get("windows") or [])
    return u


def usage_for(name, tool, home):
    try:
        if tool == "claude":
            return apply_resets(claude_usage(name))
        if tool == "codex":
            return apply_resets(codex_usage(home))
    except Exception as e:
        return {"error": str(e)}
    return {}


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "claude-out":
        claude_out(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)
