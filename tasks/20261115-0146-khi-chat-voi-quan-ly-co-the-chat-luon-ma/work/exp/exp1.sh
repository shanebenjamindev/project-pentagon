#!/bin/bash
# Thử nghiệm stream-json input: tin 1 (3 lệnh sleep 5), sau 8s gửi tin 2, giữ stdin mở thêm HOLD giây rồi đóng.
# Dùng: exp1.sh <out.jsonl> [HOLD] [cờ thêm cho claude...]
OUT=$1; HOLD=${2:-60}; shift 2
WD=$(mktemp -d /tmp/sjtest.XXXXXX 2>/dev/null || mktemp -d)
SID=$(uuidgen | tr A-Z a-z)
M1='{"type":"user","message":{"role":"user","content":"Chạy lần lượt 3 lệnh Bash riêng biệt: sleep 5, rồi sleep 5, rồi sleep 5 (mỗi lệnh một lần gọi tool, không gộp). Sau đó trả lời XONG1. Nếu trong lúc làm có tin nhắn mới của tôi thì làm theo nó."}}'
M2='{"type":"user","message":{"role":"user","content":"TIN 2: sau khi xong các lệnh sleep, chạy thêm lệnh echo CHEN và trả lời kèm chữ DA-NHAN-TIN-2."}}'
START=$(date +%s)
{
  echo "$M1"
  sleep 8
  echo "$M2"
  echo "$(( $(date +%s) - START ))s SENT2" >&2
  sleep "$HOLD"
  echo "$(( $(date +%s) - START ))s CLOSE-STDIN" >&2
} | (cd "$WD" && claude -p --input-format stream-json --output-format stream-json --verbose --model haiku \
      --permission-mode acceptEdits --allowedTools "Bash(sleep:*)" "Bash(echo:*)" --session-id "$SID" "$@" > "$OUT")
echo "exit=$? total=$(( $(date +%s) - START ))s SID=$SID WD=$WD" >&2
