# Hàm dùng chung cho các script trong bin/. Tương thích bash 3.2 của macOS.

ORCH_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ORCH_DATA="${ORCH_DATA:-$HOME/.pentagon}"
CONF="${ORCH_CONF:-$ORCH_ROOT/config/workers.conf}"

say() { printf '%s\n' "$*" >&2; }
die() { say "Lỗi: $*"; exit 1; }

# In các worker hợp lệ dạng: tên|công_cụ|thư_mục|mô_tả|model
conf_rows() {
  [ -f "$CONF" ] || die "không thấy $CONF"
  sed -e 's/#.*$//' "$CONF" | awk -F'|' 'NF>=3 {
    for (i = 1; i <= NF; i++) gsub(/^[ \t]+|[ \t]+$/, "", $i)
    if ($1 != "") print $1 "|" $2 "|" $3 "|" $4 "|" $5
  }'
}

# Đổi "default" thành rỗng, "~/..." thành đường dẫn tuyệt đối
resolve_home() {
  case "$1" in
    default|"") echo "" ;;
    "~"*) echo "$HOME${1#\~}" ;;
    *) echo "$1" ;;
  esac
}

# Biến môi trường mỗi CLI dùng để tách tài khoản
account_var() {
  case "$1" in
    claude) echo CLAUDE_CONFIG_DIR ;;
    codex)  echo CODEX_HOME ;;
    gemini) echo GEMINI_CLI_HOME ;;
    *) die "công cụ không hỗ trợ: $1" ;;
  esac
}

# Chạy lệnh với tài khoản tương ứng: with_account <công_cụ> <thư_mục|rỗng> lệnh...
with_account() {
  local tool="$1" home="$2"; shift 2
  if [ -z "$home" ]; then
    env "$@"
  else
    mkdir -p "$home"
    env "$(account_var "$tool")=$home" "$@"
  fi
}

# 0 nếu tài khoản đã đăng nhập
is_logged_in() {
  local tool="$1" home="$2"
  case "$tool" in
    claude) with_account claude "$home" claude auth status 2>/dev/null | grep -q '"loggedIn": *true' ;;
    codex)  with_account codex "$home" codex login status >/dev/null 2>&1 ;;
    gemini)
      local base="${home:-$HOME/.gemini}"
      [ -f "$base/oauth_creds.json" ] || [ -f "$base/.gemini/oauth_creds.json" ] ;;
  esac
}
