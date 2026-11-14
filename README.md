# Pentagon — 1 người giao việc, 1 AI quản lý, nhiều AI làm

Dùng **gói thuê bao** (Claude Pro/Team, ChatGPT Plus/Team, Google AI Pro…) qua các CLI chính chủ,
**không cần API key**. Claude Code là AI quản lý: nhận task, tối ưu yêu cầu, chia việc,
giao cho các AI worker (nhiều tài khoản Claude, Codex, Gemini), kiểm tra và tổng hợp.

```
Bạn ──/giao task──▶ Claude Code (quản lý, đọc CLAUDE.md)
                      ├─ tối ưu yêu cầu → tasks/<id>/brief.md
                      ├─ chia việc      → tasks/<id>/plan.md
                      ├─ bin/ask claude ─▶ claude-main → claude-2 → … (tự chuyển khi hết hạn mức)
                      ├─ bin/ask codex  ─▶ codex-main  → codex-2  → …
                      ├─ bin/ask gemini ─▶ gemini-main → …
                      └─ kiểm tra, tổng hợp → tasks/<id>/final.md
```

## Bắt đầu

```bash
cd ~/Documents/PERSONAL/Pentagon
bin/setup              # kiểm tra mọi thứ đã sẵn sàng chưa
claude                 # mở AI quản lý
```
Trong Claude Code gõ: `/giao <mô tả task>`. Hoặc mở thư mục này trong tab Code của app Claude rồi gõ y như vậy.

## Nên chạy ở đâu

Pentagon chạy **trên máy của bạn**: `bin/ask` gọi các CLI `claude`, `codex`, `gemini` đã cài và đăng nhập trên máy,
rồi ghi kết quả vào `tasks/`. Vì vậy chỉ dùng được các bản Claude Code chạy local:

| Cách mở | Dùng được? | Hợp với |
|---|---|---|
| VSCode (extension Claude Code) | ✅ | Vừa giao task vừa xem/sửa file trong `tasks/` |
| App Claude desktop → tab **Code** | ✅ | Giao task nhanh, đọc kết quả |
| Terminal: `claude` | ✅ | Nhẹ nhất, hợp task dài |
| claude.ai/code (web) | ❌ | Chạy trên cloud, không có CLI và tài khoản của bạn |
| Chat trên claude.ai | ❌ | Không chạy được lệnh |

Máy phải bật suốt lúc task đang chạy (mỗi việc của worker có thể mất vài phút).

## Cài trên máy mới

Yêu cầu: macOS hoặc Linux (Windows: chạy trong **WSL**), Node.js/npm, các gói thuê bao đã có.

1. Copy cả thư mục `Pentagon/` sang máy mới (USB, AirDrop, hoặc `git clone` nếu đã đưa lên repo private).
   Script không gắn cứng đường dẫn nào, đặt thư mục ở đâu cũng được.
2. Chạy:
   ```bash
   cd Pentagon
   bash bin/setup --all   # cài CLI còn thiếu + đăng nhập từng worker (mở trình duyệt)
   bin/setup              # chạy lại để kiểm tra: mọi dòng phải là [ok]
   ```
   `bin/setup` không có tuỳ chọn chỉ kiểm tra và in lệnh cần chạy cho từng việc còn thiếu;
   `--install` chỉ cài CLI, `--login` chỉ đăng nhập.

Lưu ý:
- **Không copy thư mục đăng nhập** (`~/.claude`, `~/.codex`, `~/.pentagon/accounts/…`) sang máy khác.
  Token trên macOS thường nằm trong Keychain nên copy cũng không dùng được — cứ đăng nhập lại.
- Tài khoản phụ (claude-2, codex-2…) cũng phải `bin/login <tên>` lại trên máy mới.
- Model riêng của từng worker (vd `gpt-6-luna` cho Codex) nằm trong `workers.conf`, đi theo thư mục, không cần cấu hình thêm.
- Dùng **nhiều máy cùng lúc** được, nhưng chung hạn mức gói thuê bao. Thư mục `tasks/` mỗi máy riêng —
  muốn chung lịch sử thì đồng bộ dự án qua git (repo **private**) hoặc iCloud/Dropbox.
  Muốn giữ `tasks/` riêng từng máy: bỏ dấu `#` dòng `tasks/` trong `.gitignore`.

## Thêm tài khoản (bao nhiêu cũng được)

1. Mở `config/workers.conf`, thêm một dòng (hoặc bỏ dấu `#` ở dòng mẫu):
   ```
   claude-2 | claude | ~/.pentagon/accounts/claude-2 | Tài khoản Claude thứ 2 |
   ```
2. Đăng nhập tài khoản đó (mở trình duyệt, chọn đúng tài khoản):
   ```bash
   bin/login claude-2
   ```
3. Kiểm tra: `bin/workers`.

Mỗi tài khoản lưu đăng nhập trong thư mục riêng (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `GEMINI_CLI_HOME`),
nên các tài khoản không đè lên nhau. Thứ tự dòng trong file là thứ tự ưu tiên khi xoay vòng.
Chỉ dùng các tài khoản là của bạn hoặc các ghế (seat) trong gói Team của bạn.

## Gọi worker trực tiếp

```bash
bin/ask codex "Viết hàm Python kiểm tra số nguyên tố, kèm test"
bin/ask claude-2 -t tasks/<id> "Review đoạn code trong results/codex-main-*.md"
bin/ask codex -w -C ~/du-an-cua-toi "Sửa lỗi trong file app.py"   # -w: cho phép sửa file
echo "nội dung dài..." | bin/ask claude -
```
Mặc định worker **chỉ được đọc**. Phải thêm `-w` thì worker mới sửa được file trong thư mục `-C`.

## Cấu trúc

| Đường dẫn | Vai trò |
|---|---|
| `CLAUDE.md` | Vai trò và quy trình 6 bước của AI quản lý |
| `.claude/commands/giao.md` | Lệnh `/giao` |
| `.claude/agents/worker.md` | Agent con chuyển việc tới worker (cho phép chạy song song) |
| `config/workers.conf` | Danh sách worker và tài khoản |
| `bin/ask` | Giao việc cho worker, tự chuyển tài khoản khi lỗi hoặc hết hạn mức |
| `bin/setup` | Dựng dự án trên máy: kiểm tra công cụ, cài CLI, đăng nhập worker |
| `bin/login`, `bin/workers`, `bin/new-task` | Đăng nhập, xem trạng thái, tạo task |
| `tasks/<id>/` | `brief.md`, `plan.md`, `results/`, `log.txt`, `final.md` của từng task |
| `~/.pentagon/` | Thư mục tài khoản phụ và thư mục làm việc mặc định của worker (ngoài dự án) |
| `docs/quy-trinh-pentagon.xlsx` | Bảng quy trình chi tiết (bản đã tải lên Google Sheet "Quy trình Pentagon") |
| `docs/build_sheet.py` | Script Python (openpyxl) tạo lại file .xlsx trên |

## Tình trạng hiện tại

- **Claude** (tài khoản Team): chạy tốt.
- **Codex** (tài khoản ChatGPT): chạy tốt với model `gpt-6-luna`. Model `gpt-6.1-sol` trong `~/.codex/config.toml`
  không dùng được với tài khoản ChatGPT, nên `workers.conf` chỉ định model riêng.
- **Gemini**: đang tắt. Tài khoản Google hiện tại là gói miễn phí, và Google đã ngừng cho Gemini CLI dùng gói này.
  Bật lại khi có tài khoản Google AI Pro/Ultra hoặc Workspace (xem ghi chú trong `workers.conf`).

## Bớt hộp thoại xin phép (tuỳ chọn)

Claude Code sẽ hỏi bạn trước khi chạy `bin/ask`. Muốn cho chạy tự động thì tự tạo `.claude/settings.json`:
```json
{
  "permissions": {
    "allow": ["Bash(bin/ask:*)", "Bash(bin/workers)", "Bash(bin/new-task:*)"]
  }
}
```
