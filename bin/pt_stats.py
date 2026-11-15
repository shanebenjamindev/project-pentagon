"""Thống kê token cho trang Thống kê trên web: cái gì tốn token nhất (task, nhân viên, model, vai trò, lần chạy).

Nguồn (không tốn thêm lượt gọi AI nào, đọc được cả task cũ):
- AI quản lý: tasks/<id>/manager/stream.jsonl — mỗi lượt là một tiến trình Claude (bắt đầu bằng sự kiện
  system/init); event `result` có modelUsage (số CỘNG DỒN trong tiến trình → lấy số lớn nhất theo từng model).
  Lượt bị ngắt (không có result) thì cộng usage của từng tin trả lời (bỏ trùng theo id tin).
- Nhân viên Claude: dòng đầu file kết quả có "phiên: <id>" → <thư mục tài khoản>/projects/*/<id>.jsonl
  (cộng usage từng tin trả lời; bỏ trùng theo id tin vì phiên "hỏi tiếp" là bản sao chép lại lịch sử phiên gốc).
- Nhân viên Codex: <CODEX_HOME>/sessions/**/rollout-*<id>.jsonl → total_token_usage cuối cùng.
- Gemini: chưa có nguồn → chỉ đếm số lần chạy ("chưa rõ token").
"""
import datetime
import glob
import json
import os
import re
import threading
import time

from tracker import ROOT, TASKS, read, task_ids

WORKERS = os.environ.get("ORCH_CONF") or os.path.join(ROOT, "config", "workers.conf")
FIELDS = ("inp", "cw", "cr", "out")   # vào (mới) · ghi cache · đọc cache · ra
_cache = {}
_lock = threading.Lock()


def _zero():
    return {k: 0 for k in FIELDS}


def _add(a, b):
    for k in FIELDS:
        a[k] += b.get(k, 0)
    return a


def _total(u):
    return sum(u.get(k, 0) for k in FIELDS)


def _cached(path, fn):
    """Kết quả đọc file, lưu theo (mtime, size) để mỗi lần mở trang không phải đọc lại file lớn."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    key = (st.st_mtime_ns, st.st_size)
    with _lock:
        hit = _cache.get(path)
    if hit and hit[0] == key:
        return hit[1]
    val = fn(path)
    with _lock:
        _cache[path] = (key, val)
    return val


def _lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("{"):
                    try:
                        yield json.loads(line)
                    except ValueError:
                        pass
    except OSError:
        return


def pretty_model(m):
    m = (m or "").strip()
    g = re.match(r"claude-(opus|sonnet|haiku|fable)-(\d+)-(\d+)", m)
    if g:
        return "%s %s.%s" % (g.group(1).capitalize(), g.group(2), g.group(3))
    return m or "không rõ"


def _claude_usage(u):
    return {"inp": int(u.get("input_tokens") or 0), "cw": int(u.get("cache_creation_input_tokens") or 0),
            "cr": int(u.get("cache_read_input_tokens") or 0), "out": int(u.get("output_tokens") or 0)}


# ---- AI quản lý
def _parse_manager(path):
    """Trả danh sách lượt: {ts, models: {model: usage}}."""
    turns, cur, ts = [], None, 0

    def close():
        if cur is None:
            return
        models = {}
        if cur["mu"]:
            for m, u in cur["mu"].items():
                models[m] = u
        else:
            for m, u in cur["msgs"].values():
                _add(models.setdefault(m, _zero()), u)
        if any(_total(u) for u in models.values()):
            turns.append({"ts": cur["ts"] or ts, "models": models})

    for e in _lines(path):
        t = e.get("type")
        if t in ("pentagon_owner", "pentagon_event") and e.get("ts"):
            ts = int(e["ts"])
            if cur is not None and not cur["ts"]:
                cur["ts"] = ts
        elif t == "system" and e.get("subtype") == "init":
            close()
            cur = {"ts": ts, "mu": {}, "msgs": {}}
        elif cur is None:
            continue
        elif t == "result":
            for m, u in (e.get("modelUsage") or {}).items():
                v = {"inp": int(u.get("inputTokens") or 0), "cw": int(u.get("cacheCreationInputTokens") or 0),
                     "cr": int(u.get("cacheReadInputTokens") or 0), "out": int(u.get("outputTokens") or 0)}
                old = cur["mu"].setdefault(m, _zero())
                for k in FIELDS:
                    old[k] = max(old[k], v[k])
        elif t == "assistant":
            msg = e.get("message") or {}
            if msg.get("usage"):
                cur["msgs"][msg.get("id") or id(msg)] = (msg.get("model") or "", _claude_usage(msg["usage"]))
    close()
    if turns and not turns[0]["ts"]:
        turns[0]["ts"] = int(os.path.getmtime(path))
    return turns


# ---- nhân viên
HEAD_RE = re.compile(r"^<!-- worker: (\S+) \((\w+)\) \| (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \| (\d+)s \|(.*?)-->", re.S)


def parse_head(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            line = f.readline()
    except OSError:
        return None
    m = HEAD_RE.match(line)
    if not m:
        return None
    meta = {}
    for part in m.group(5).split(" | "):
        if ":" in part:
            k, v = part.split(":", 1)
            meta[k.strip()] = v.strip()
    try:
        ts = int(time.mktime(time.strptime(m.group(3), "%Y-%m-%d %H:%M:%S")))
    except ValueError:
        ts = int(os.path.getmtime(path))
    return {"worker": m.group(1), "tool": m.group(2), "ts": ts, "secs": int(m.group(4)),
            "model": meta.get("model", ""), "role": meta.get("vai trò", ""), "session": meta.get("phiên", ""),
            "followup": bool(meta.get("hỏi tiếp"))}


def _homes():
    out = {}
    for line in (read(WORKERS) or "").splitlines():
        cells = [c.strip() for c in line.split("#", 1)[0].split("|")]
        if len(cells) >= 3 and cells[0]:
            h = cells[2]
            out[cells[0]] = (cells[1], "" if h in ("", "default") else os.path.expanduser(h))
    return out


def _all_homes(tool):
    base = os.path.expanduser("~/.claude" if tool == "claude" else "~/.codex")
    return [base] + sorted(glob.glob(os.path.expanduser("~/.pentagon/accounts/*")))


def _claude_msgs(path):
    """{id tin: (model, usage)} của một file phiên Claude."""
    msgs = {}
    for e in _lines(path):
        if e.get("type") == "assistant":
            msg = e.get("message") or {}
            if msg.get("usage") and msg.get("id"):
                msgs[msg["id"]] = (msg.get("model") or "", _claude_usage(msg["usage"]))
    return msgs


def _codex_usage(path):
    last, model = None, ""
    for e in _lines(path):
        p = e.get("payload") or {}
        if p.get("type") == "token_count":
            last = ((p.get("info") or {}).get("total_token_usage")) or last
        elif e.get("type") == "turn_context" and p.get("model"):
            model = p["model"]
    if not last:
        return None
    inp, cached = int(last.get("input_tokens") or 0), int(last.get("cached_input_tokens") or 0)
    return model, {"inp": max(0, inp - cached), "cw": int(last.get("cache_write_input_tokens") or 0),
                   "cr": cached, "out": int(last.get("output_tokens") or 0)}


def _find(patterns):
    for p in patterns:
        hits = glob.glob(p)
        if hits:
            return hits
    return []


def _worker_usage(head, homes, seen):
    """(model, usage) của một lần chạy nhân viên, hoặc None nếu không có số liệu."""
    sid = re.sub(r"[^0-9A-Za-z-]", "", head["session"] or "")
    if not sid:
        return None
    tool, home = homes.get(head["worker"], (head["tool"], None))
    if head["tool"] == "claude":
        roots = [home or os.path.expanduser("~/.claude")] if home is not None else _all_homes("claude")
        files = _find([os.path.join(r, "projects", "*", sid + ".jsonl") for r in roots])
        if not files:
            return None
        files += glob.glob(os.path.join(os.path.dirname(files[0]), sid, "subagents", "*.jsonl"))
        models = {}
        for f in files:
            for mid, (m, u) in (_cached(f, _claude_msgs) or {}).items():
                if mid in seen:   # phiên hỏi tiếp chép lại tin của phiên gốc: không đếm hai lần
                    continue
                seen.add(mid)
                _add(models.setdefault(m, _zero()), u)
        if not models:
            return None
        top = max(models, key=lambda k: _total(models[k]))
        u = _zero()
        for v in models.values():
            _add(u, v)
        return top, u
    if head["tool"] == "codex":
        roots = [home or os.path.expanduser("~/.codex")] if home is not None else _all_homes("codex")
        files = _find([os.path.join(r, "sessions", "*", "*", "*", "rollout-*%s.jsonl" % sid) for r in roots])
        if not files:
            return None
        r = _cached(files[0], _codex_usage)
        if not r:
            return None
        model = r[0] or head["model"].split("·")[0].strip()
        effort = re.search(r"@(\w+)", head["model"] or "")
        return (model + ("@" + effort.group(1) if effort and "@" not in model else "")), r[1]
    return None


# ---- tổng hợp
def _since(days):
    if not days:
        return 0
    start = datetime.datetime.combine(datetime.date.today(), datetime.time()) - datetime.timedelta(days=days - 1)
    return int(start.timestamp())


def stats(days=7):
    since, homes = _since(days), _homes()
    tot, runs_unknown = _zero(), 0
    by_task, by_who, by_model, by_role, by_day, runs = {}, {}, {}, {}, {}, []

    def bump(table, key, u, **extra):
        row = table.setdefault(key, dict(_zero(), runs=0, **extra))
        _add(row, u)
        row["runs"] += 1
        return row

    for tid in task_ids():
        tdir = os.path.join(TASKS, tid)
        brief = read(os.path.join(tdir, "brief.md")) or ""
        m = re.search(r"^#\s+(.+)$", brief, re.M)
        title = m.group(1).strip() if m else tid
        account = (read(os.path.join(tdir, "manager", "account")) or "").strip() or "quản lý"
        trow = None

        def task_row():
            return by_task.setdefault(tid, dict(_zero(), id=tid, title=title, mgr=0, wrk=0, runs=0))

        for turn in _cached(os.path.join(tdir, "manager", "stream.jsonl"), _parse_manager) or []:
            if turn["ts"] < since:
                continue
            for model, u in turn["models"].items():
                if not _total(u):
                    continue
                trow = task_row()
                _add(trow, u)
                trow["mgr"] += _total(u)
                trow["runs"] += 1
                _add(tot, u)
                bump(by_who, account, u, name=account, mgr=0, wrk=0)["mgr"] += _total(u)
                bump(by_model, pretty_model(model), u, name=pretty_model(model))
                bump(by_role, "quan-ly", u, name="quan-ly")
                day = time.strftime("%Y-%m-%d", time.localtime(turn["ts"]))
                d = by_day.setdefault(day, {"day": day, "mgr": 0, "wrk": 0})
                d["mgr"] += _total(u)
                runs.append(dict(u, task=tid, title=title, who=account, kind="manager", model=pretty_model(model),
                                 role="quan-ly", ts=turn["ts"], secs=None, file=""))
        seen = set()
        for f in sorted(glob.glob(os.path.join(tdir, "results", "*.md"))):
            head = parse_head(f)
            if not head or head["ts"] < since:
                continue
            got = _worker_usage(head, homes, seen)
            if not got:
                runs_unknown += 1
                continue
            model, u = got
            if not _total(u):
                continue
            trow = task_row()
            _add(trow, u)
            trow["wrk"] += _total(u)
            trow["runs"] += 1
            _add(tot, u)
            bump(by_who, head["worker"], u, name=head["worker"], mgr=0, wrk=0)["wrk"] += _total(u)
            bump(by_model, pretty_model(model), u, name=pretty_model(model))
            role = "hoi-tiep" if head["followup"] else (head["role"] or "khac")
            bump(by_role, role, u, name=role)
            day = time.strftime("%Y-%m-%d", time.localtime(head["ts"]))
            d = by_day.setdefault(day, {"day": day, "mgr": 0, "wrk": 0})
            d["wrk"] += _total(u)
            runs.append(dict(u, task=tid, title=title, who=head["worker"], kind="worker", model=pretty_model(model),
                             role=role, ts=head["ts"], secs=head["secs"], file=os.path.basename(f)))

    def rows(table):
        out = list(table.values())
        for r in out:
            r["total"] = _total(r)
        return sorted(out, key=lambda r: -r["total"])

    for r in runs:
        r["total"] = _total(r)
    runs.sort(key=lambda r: -r["total"])
    return {"days": days, "since": since, "totals": dict(tot, total=_total(tot), runs=len(runs), unknown=runs_unknown),
            "tasks": rows(by_task), "who": rows(by_who), "models": rows(by_model), "roles": rows(by_role),
            "runs": runs[:200], "by_day": sorted(by_day.values(), key=lambda d: d["day"])}


if __name__ == "__main__":
    import sys
    d = stats(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    print(json.dumps({k: d[k] for k in ("totals",)}, ensure_ascii=False))
    for k in ("tasks", "who", "models", "roles"):
        print(k, [(r.get("title") or r.get("name"), r["total"]) for r in d[k][:5]])
    print("runs", [(r["who"], r["title"][:30], r["model"], r["total"]) for r in d["runs"][:5]])
