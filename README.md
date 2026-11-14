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

## Web app: giao task, theo dõi, thao tác

```bash
bin/dashboard --open   # http://127.0.0.1:8765 — để cửa sổ terminal này chạy suốt
```
Web có hai khu (tab trên cùng):

**Phòng Điều hành**, nơi bạn làm mọi thứ mà không cần mở Claude Code:
- **Giao task** (nút “+ Giao task”):
  - Chọn **cách giao việc**: *một worker làm* (mặc định, làm lần lượt, không song song) hoặc *song song*.
  - Chọn **duyệt kế hoạch**: để quản lý tự quyết, chờ bạn duyệt, hoặc làm luôn.
- **Trò chuyện với AI quản lý** của từng task: thấy từng bước nó làm, trả lời câu hỏi, bấm “Đồng ý, tiến hành” khi nó chờ duyệt,
  nhắn thêm yêu cầu sửa. Task tạo từ Claude Code cũng nhắn tiếp được (quản lý web sẽ đọc lại task rồi làm tiếp).
- **Dừng** quản lý, **huỷ** một worker đang chạy, **huỷ task**, đánh dấu xong.
- Theo dõi: bước hiện tại trong 6 bước, việc con nào xong, worker nào đang chạy và chạy bao lâu, kết quả từng worker,
  nhật ký, yêu cầu và kết quả cuối. Tab trình duyệt hiện số task đang chờ bạn, ví dụ “(1) Pentagon”.

**Văn phòng làm việc**: mỗi AI là một nhân viên ngồi một bàn.
- **Ban điều hành**: các AI quản lý đang chạy, mỗi cái thuộc task nào, đang ở bước nào, dùng model và tài khoản nào.
- **Nhân viên**: từng worker đang làm việc gì (bấm vào để mở task), rảnh hay bận, có hết hạn mức không.
- **Usage**: % hạn mức gói thuê bao đã dùng, kèm giờ làm mới. Claude có khung 5 giờ và 7 ngày; Codex là hạn mức của gói.
  Có thêm số lần gọi và token trong ngày, cùng số việc xong và số lỗi Pentagon tự đếm.
  Số liệu lấy từ chính các lần chạy, không tốn thêm lượt gọi. Claude được cập nhật sau mỗi lần chạy;
  Codex đọc từ `~/.codex/sessions`; Gemini chưa có nguồn số liệu.

### Model theo cỡ task
AI quản lý tự phân loại task là **nhỏ / vừa / lớn** để chọn model; bảng chọn nằm ở `config/models.conf`:

| | Nhỏ | Vừa | Lớn |
|---|---|---|---|
| AI quản lý | haiku | sonnet | opus |
| Worker claude | haiku | sonnet | opus |
| Worker codex | gpt-6-luna, suy nghĩ ít | gpt-6-luna, vừa | gpt-6-luna, nhiều |

- Mỗi việc con, quản lý gọi `bin/ask … -s nho|vua|lon` theo độ khó của chính việc đó.
- Làm giữa chừng mà thấy cỡ sai, quản lý tự đổi bằng `bin/manager size`; model đổi theo từ lượt sau.

### Hết hạn mức giữa chừng
- **Worker**: `bin/ask` tự chuyển sang tài khoản kế tiếp cùng công cụ. Phần trả lời dở được lưu vào `results/dang-do-*.txt`
  và giao cho tài khoản sau kèm lời dặn **làm tiếp, không làm lại**. Nếu worker có quyền sửa file, nó được dặn kiểm tra
  các file đã sửa dở. Gọi theo tên tài khoản (vd `claude-2`) cũng tự chuyển.
- **AI quản lý**: phiên Claude được chép sang tài khoản Claude kế tiếp trong `workers.conf`, và quản lý làm tiếp **đúng phiên đó**,
  nên vẫn nhớ mọi thứ đã làm.
- **Hết sạch tài khoản**: task chuyển sang “chờ”, phần đã làm được giữ nguyên, và quản lý tự làm tiếp đúng giờ hạn mức được làm mới.
  Cần để `bin/dashboard` chạy; trên web cũng có nút “Thử ngay”.

Quản lý chạy nền bằng Claude Code (tài khoản Claude mặc định trên máy), mỗi task một phiên riêng nên nó nhớ ngữ cảnh
giữa các lần bạn nhắn. Đóng trình duyệt hay tắt `bin/dashboard` không làm dừng quản lý đang chạy.
Khi chạy nền, quản lý chỉ được dùng một số lệnh an toàn (bin/ask, bin/progress, đọc/ghi file trong dự án…);
muốn cho thêm quyền (vd chạy test python) hay đổi model: sửa `config/manager.conf`.
Không có web thì dùng dòng lệnh tương đương: `bin/manager new|send|stop|kill-worker` (xem `bin/manager --help`).

Bảo mật:
- Web chỉ nghe trên `127.0.0.1`, nên máy khác không vào được.
- Web chặn các yêu cầu đến từ trang web lạ.
- Muốn có trang đăng nhập: chạy `bin/dashboard --set-password`. Mật khẩu chỉ lưu dạng băm trong `config/auth.conf`,
  file này không lên git. Tắt đăng nhập: `bin/dashboard --clear-password`.
- Đừng mở cổng này ra mạng ngoài.

Xem nhanh trong terminal:

```bash
bin/status             # danh sách task ngay trong terminal
bin/status -w          # tự làm mới liên tục (Ctrl+C để thoát)
bin/status latest      # chi tiết task mới nhất (hoặc bin/status <một phần id>)
```
Cần `python3` (có sẵn trên macOS khi cài Xcode CLT).

Dữ liệu đến từ: `bin/progress` (AI quản lý ghi bước hiện tại vào `tasks/<id>/status`),
`bin/ask -t` (ghi worker đang chạy vào `tasks/<id>/running/` và nhật ký vào `log.txt`), và `plan.md`.

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
| `bin/progress` | AI quản lý ghi task đang ở bước nào |
| `bin/status`, `bin/tracker.py` | Xem tiến độ trong terminal |
| `bin/dashboard`, `bin/pt_web.py`, `web/index.html` | Web app: giao task, trò chuyện với quản lý, theo dõi, dừng/huỷ |
| `bin/manager`, `bin/pt_manager.py`, `config/manager.conf` | Chạy AI quản lý nền cho từng task (web app dùng cái này), tự đổi tài khoản khi hết hạn mức |
| `config/models.conf` | Bảng model theo cỡ việc (nhỏ/vừa/lớn) cho quản lý và từng công cụ |
| `bin/pt_usage.py` | Thống kê usage từng tài khoản (lưu ở `~/.pentagon/usage/`) |
| `web/` | Trang web app, trang đăng nhập, logo |
| `tasks/<id>/` | `brief.md`, `plan.md`, `status`, `results/`, `running/`, `log.txt`, `final.md`, `manager/` (phiên quản lý web), `prompts/` |
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
    "allow": ["Bash(bin/ask:*)", "Bash(bin/workers)", "Bash(bin/new-task:*)", "Bash(bin/progress:*)", "Bash(bin/status:*)"]
  }
}
```
