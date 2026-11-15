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
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from email.utils import parsedate_to_datetime
import urllib.error
import urllib.request
from datetime import datetime

DATA = os.environ.get("ORCH_DATA") or os.path.expanduser("~/.pentagon")
UDIR = os.path.join(DATA, "usage")
_LIVE_LOCK = threading.Lock()
_LIVE_THREADS = set()
_LIVE_RETRY = {}


def live_windows(response):
    """Chuyển API OAuth usage sang định dạng cửa sổ của Pentagon."""
    windows = []
    for key, label in (("five_hour", "5 giờ"), ("seven_day", "7 ngày"),
                       ("seven_day_opus", "7 ngày (Opus)"),
                       ("seven_day_sonnet", "7 ngày (Sonnet)")):
        w = response.get(key)
        if not isinstance(w, dict):
            continue
        used = w.get("utilization")
        try:
            resets_at = datetime.fromisoformat(w["resets_at"].replace("Z", "+00:00")).timestamp()
        except (KeyError, TypeError, ValueError, OverflowError):
            resets_at = None
        windows.append({"label": label, "used": used if isinstance(used, (int, float)) else None,
                        "resets_at": resets_at, "status": "rejected" if isinstance(used, (int, float)) and used >= 100 else "allowed"})
    return windows


def _credential_path(home):
    return os.path.join(home or os.path.expanduser("~/.claude"), ".credentials.json")


def _oauth_credentials(home):
    """Đọc token từ file hoặc Keychain; tuyệt đối không đưa token vào thông báo lỗi."""
    def usable(oauth):
        if not isinstance(oauth, dict) or not oauth.get("accessToken"):
            return False
        try:
            return not oauth.get("expiresAt") or float(oauth["expiresAt"]) >= time.time() * 1000
        except (TypeError, ValueError):
            return True
    try:
        with open(_credential_path(home), encoding="utf-8") as f:
            oauth = (json.load(f).get("claudeAiOauth") or {})
        if usable(oauth):
            return oauth
    except (OSError, ValueError, AttributeError):
        pass
    default_home = os.path.abspath(os.path.expanduser("~/.claude"))
    actual_home = os.path.abspath(home or default_home)
    service_names = ["Claude Code-credentials"]
    if actual_home != default_home:
        suffix = hashlib.sha256(actual_home.encode()).hexdigest()[:8]
        service_names = ["Claude Code-credentials-" + suffix, "Claude Code-credentials"]
    for service in service_names:
        try:
            raw = subprocess.run(["security", "find-generic-password", "-a", os.environ.get("USER", ""),
                                  "-w", "-s", service], capture_output=True, text=True,
                                 timeout=5, check=True).stdout
            oauth = (json.loads(raw).get("claudeAiOauth") or {})
            if usable(oauth):
                return oauth
        except (OSError, subprocess.SubprocessError, ValueError, AttributeError):
            continue
    return None


def fetch_live_usage(name, home):
    """Lấy số liệu từ Anthropic; không refresh token OAuth."""
    oauth = _oauth_credentials(home)
    if not oauth:
        return None, "không tìm thấy thông tin đăng nhập Claude", None
    token = oauth.get("accessToken")
    if not token:
        return None, "không tìm thấy thông tin đăng nhập Claude", None
    req = urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers={
        "Authorization": "Bearer " + token, "anthropic-beta": "oauth-2025-04-20",
        "Content-Type": "application/json", "User-Agent": "pentagon-usage/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        windows = live_windows(payload)
        return {"windows": windows, "limited": any(
            isinstance(w.get("used"), (int, float)) and w["used"] >= 100 for w in windows),
            "rate_at": int(time.time()), "source": "live"}, None, None
    except urllib.error.HTTPError as e:
        retry = None
        if e.code == 429:
            try:
                header = e.headers.get("Retry-After")
                try:
                    retry = max(0, int(header))
                except ValueError:
                    retry = max(0, int(parsedate_to_datetime(header).timestamp() - time.time()))
            except (TypeError, ValueError, AttributeError, OverflowError):
                pass
        return None, "Anthropic trả về lỗi HTTP %d" % e.code, retry
    except (urllib.error.URLError, TimeoutError, OSError):
        return None, "không kết nối được Anthropic", None
    except (ValueError, UnicodeError):
        return None, "phản hồi usage không hợp lệ", None


def _live_path(name):
    return os.path.join(UDIR, name + ".live.json")


def _read_live(name):
    try:
        with open(_live_path(name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _refresh_live(name, home, force=False):
    try:
        os.makedirs(UDIR, exist_ok=True)
    except OSError:
        if not force:
            return _read_live(name)
        data, error, _ = fetch_live_usage(name, home)
        return dict(data or {}, live_error=error or "không lưu được cache usage")
    lock_path = _live_path(name) + ".lock"
    fd = None
    for _ in range(2):
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(lock_path) > 30:
                    os.unlink(lock_path)
                    continue
            except OSError:
                continue
            old = _read_live(name)
            return dict(old, live_error="usage đang được cập nhật (lock còn mới)") if force else old
        except OSError:
            old = _read_live(name)
            return dict(old, live_error="không lấy được khóa cập nhật usage") if force else old
    if fd is None:
        old = _read_live(name)
        return dict(old, live_error="không lấy được khóa cập nhật usage") if force else old
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        old = _read_live(name)
        now = time.time()
        if not force and (now - old.get("attempt_at", 0) < 60 or now < old.get("retry_after", 0)):
            return old
        data, error, retry_hint = fetch_live_usage(name, home)
        updated = dict(old)
        updated["attempt_at"] = int(now)
        if data:
            updated.update(data)
            updated["live_error"] = ""
            updated.pop("retry_after", None)
        else:
            updated["live_error"] = error or "không lấy được số liệu"
            delay = (900 if error and ("đăng nhập" in error or "token" in error) else
                     300 if error and "HTTP 401" in error else
                     (retry_hint if retry_hint is not None else 300) if error and "HTTP 429" in error else 60)
            updated["retry_after"] = int(now + delay)
        tmp = lock_path + ".%d.tmp" % os.getpid()
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(updated, f, ensure_ascii=False)
            os.replace(tmp, _live_path(name))
        except OSError:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            if data:
                updated["live_error"] = "không lưu được cache usage"
            return updated
        return updated
    finally:
        try:
            os.unlink(lock_path)
        except OSError:
            pass


def _schedule_live(name, home):
    with _LIVE_LOCK:
        now = time.time()
        if name in _LIVE_THREADS or _LIVE_RETRY.get(name, 0) > now:
            return
        _LIVE_THREADS.add(name)
        _LIVE_RETRY[name] = now + 60
    def work():
        try:
            result = _refresh_live(name, home)
            if "HTTP 429" in str(result.get("live_error", "")):
                with _LIVE_LOCK:
                    _LIVE_RETRY[name] = time.time() + 300
        finally:
            with _LIVE_LOCK:
                _LIVE_THREADS.discard(name)
    threading.Thread(target=work, name="usage-" + name, daemon=True).start()


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
    # Một lần chạy (stdin stream-json) có thể ra nhiều event result; total_cost_usd và modelUsage là số CỘNG DỒN
    # trong cả tiến trình → lấy số lớn nhất, không cộng. `usage` là số của riêng từng lượt → cộng.
    rate, cost, calls, mu_tokens, turn_tokens = None, 0.0, 0, 0, 0
    for e in events:
        t = e.get("type")
        if t == "rate_limit_event":
            rate = e.get("rate_limit_info") or rate
        elif t == "result":
            calls += 1
            cost = max(cost, float(e.get("total_cost_usd") or 0))
            mu = sum(sum(int(m.get(k) or 0) for k in ("inputTokens", "outputTokens",
                                                     "cacheReadInputTokens", "cacheCreationInputTokens"))
                     for m in (e.get("modelUsage") or {}).values())
            mu_tokens = max(mu_tokens, mu)
            u = e.get("usage") or {}
            turn_tokens += sum(int(u.get(k) or 0) for k in ("input_tokens", "output_tokens",
                                                            "cache_read_input_tokens", "cache_creation_input_tokens"))
    tokens = mu_tokens or turn_tokens
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


def _merge_running_claude(name, out):
    """Gộp usage mới nhất từ stream Claude còn đang được bin/ask ghi."""
    today = time.strftime("%Y-%m-%d")
    running_tokens = 0
    latest_rate = None
    for path in glob.glob(os.path.join(UDIR, name + ".*.stream.jsonl")):
        # Stream được đặt tên <worker>.<pid>.stream.jsonl. Bỏ stream mồ côi
        # nếu đã cũ hoặc tiến trình ghi nó không còn chạy.
        basename = os.path.basename(path)
        pid_text = basename[len(name) + 1:-len(".stream.jsonl")]
        try:
            pid = int(pid_text)
            if time.time() - os.path.getmtime(path) > 600:
                continue
        except (OSError, ValueError):
            continue
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        except PermissionError:
            pass
        except OSError:
            continue
        events = read_events(path)
        if not events:
            continue
        # Khi đang chạy chưa có result cuối; usage của các message assistant là
        # từng lượt API. Nếu đã có result thì ưu tiên cách tính chuẩn hiện có.
        has_result = any(e.get("type") == "result" for e in events)
        if has_result:
            for e in events:
                if e.get("type") == "rate_limit_event":
                    latest_rate = e.get("rate_limit_info") or latest_rate
            mu_tokens, turn_tokens = 0, 0
            for e in events:
                if e.get("type") != "result":
                    continue
                mu = sum(sum(int(m.get(k) or 0) for k in (
                    "inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens"))
                    for m in (e.get("modelUsage") or {}).values())
                mu_tokens = max(mu_tokens, mu)
                u = e.get("usage") or {}
                turn_tokens += sum(int(u.get(k) or 0) for k in (
                    "input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
            running_tokens += mu_tokens or turn_tokens
        else:
            seen_messages = set()
            for e in events:
                if e.get("type") == "rate_limit_event":
                    latest_rate = e.get("rate_limit_info") or latest_rate
                elif e.get("type") == "assistant":
                    message = e.get("message") or {}
                    message_id = message.get("id")
                    if message_id is not None:
                        if message_id in seen_messages:
                            continue
                        seen_messages.add(message_id)
                    u = message.get("usage") or {}
                    running_tokens += sum(int(u.get(k) or 0) for k in (
                        "input_tokens", "output_tokens", "cache_read_input_tokens",
                        "cache_creation_input_tokens"))
    if running_tokens:
        day = out.setdefault("days", {}).setdefault(today, {"calls": 0, "tokens": 0})
        day["tokens"] = int(day.get("tokens") or 0) + running_tokens
    if latest_rate:
        wins = []
        uw = latest_rate.get("unifiedWindows") or {}
        for key, label in (("five_hour", "5 giờ"), ("seven_day", "7 ngày"),
                           ("seven_day_opus", "7 ngày (Opus)")):
            w = uw.get(key)
            if w:
                u = w.get("utilization")
                wins.append({"label": label, "used": round(u * 100, 1) if isinstance(u, (int, float)) else None,
                             "resets_at": w.get("resetsAt"), "status": w.get("status")})
        if wins:
            out.update(windows=wins, limited=latest_rate.get("status") not in (None, "allowed", "allowed_warning"),
                       rate_at=int(time.time()))
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
            out = _merge_running_claude(name, claude_usage(name))
            cached = _read_live(name)
            live_fresh = time.time() - cached.get("rate_at", 0) <= 180
            if cached.get("windows") and (live_fresh or cached.get("rate_at", 0) >= out.get("rate_at", 0)):
                out.update(windows=cached["windows"], limited=cached.get("limited", False),
                           rate_at=cached["rate_at"], source="live")
            if cached.get("live_error"):
                out["live_error"] = cached["live_error"]
            # Dữ liệu cũ vẫn trả ngay; luồng nền tự cập nhật cache dùng chung.
            if time.time() - cached.get("attempt_at", 0) >= 60:
                _schedule_live(name, home)
            return apply_resets(out)
        if tool == "codex":
            return apply_resets(codex_usage(home))
    except Exception as e:
        return {"error": str(e)}
    return {}


def _configured_home(name):
    path = os.environ.get("ORCH_CONF") or os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "workers.conf")
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                cells = [c.strip() for c in line.split("#", 1)[0].split("|")]
                if len(cells) >= 3 and cells[0] == name and cells[1] == "claude":
                    return "" if cells[2] in ("", "default") else os.path.expanduser(cells[2])
    except OSError:
        pass
    return None


def _test_live_windows():
    got = live_windows({"five_hour": {"utilization": 99.0, "resets_at": "2026-11-15T22:30:00+00:00"},
                        "seven_day": None, "seven_day_opus": {"utilization": 100,
                        "resets_at": "2026-11-21T02:00:00Z"}})
    assert len(got) == 2 and got[0]["used"] == 99.0 and got[0]["used"] < 100
    assert got[0]["resets_at"] == datetime.fromisoformat("2026-11-15T22:30:00+00:00").timestamp()
    assert got[1]["label"] == "7 ngày (Opus)" and got[1]["status"] == "rejected"


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "claude-out":
        claude_out(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3 and sys.argv[1] == "live":
        home = _configured_home(sys.argv[2])
        if home is None:
            print(json.dumps({"error": "không tìm thấy worker Claude trong workers.conf"}, ensure_ascii=False))
            sys.exit(1)
        cached = _refresh_live(sys.argv[2], home, force=True)
        result = {k: cached[k] for k in ("windows", "limited", "rate_at", "source", "live_error") if k in cached}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1 if cached.get("live_error") else 0)
    elif len(sys.argv) == 2 and sys.argv[1] == "test-live":
        _test_live_windows()
        print("live_windows: OK")
    else:
        print(__doc__)
        sys.exit(1)
