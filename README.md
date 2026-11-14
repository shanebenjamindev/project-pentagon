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
Mỗi trang có địa chỉ riêng:

| Trang | Địa chỉ | Dùng để |
|---|---|---|
| Phòng Điều hành | `/dieu-hanh` | Tổng quan và danh sách task |
| Chi tiết task | `/task/<id>` | Theo dõi và thao tác trên một task |
| Giao task | `/giao` | Giao task mới |
| Văn phòng làm việc | `/van-phong` | Xem các AI đang làm gì |
| Agent | `/agent` | Quản lý agent đang chạy (dừng từng cái), hỏi tiếp subagent đã xong |
| Thông báo | `/thong-bao` | Task xong / cần bạn trả lời / bị dừng / hết hạn mức |
| Quản lý nhân viên | `/nhan-vien` | Thêm, sửa, đăng nhập tài khoản AI, xếp theo phòng ban |
| Thùng rác | `/thung-rac` | Task đã xoá |
| Cài đặt | `/cai-dat` | Giao diện, thông báo, mật khẩu, xem trên điện thoại; quyền và model của AI quản lý, model theo cỡ việc, vai trò subagent |

**Phòng Điều hành**: số task đang làm / chờ bạn / worker đang chạy / hoàn thành, ô tìm kiếm, bộ lọc,
và bảng task với các nút **Mở / Sửa / Xoá**.
- **CRUD task**:
  - Tạo: trang Giao task.
  - Xem: trang chi tiết.
  - Sửa: tiêu đề và yêu cầu (`brief.md`); quản lý đọc lại ở lượt sau.
  - Đánh dấu xong, huỷ, mở lại.
  - Xoá: task vào Thùng rác và khôi phục được. Ở Thùng rác có thể xoá vĩnh viễn.
- **Giao task** (`/giao`): mọi dropdown mặc định là **“Để quản lý tự chọn”**.
  - **Giao cho AI**: có chấm màu trước mỗi tên.
    - 🟢 rảnh
    - 🟡 đang vướng task: chọn AI này thì task **pending** và tự bắt đầu khi AI đó rảnh
    - 🔴 chưa đăng nhập hoặc chưa cài
  - **Cách giao việc**: quản lý tự chọn, một worker làm lần lượt, hoặc song song.
  - **Duyệt kế hoạch**: quản lý tự chọn, chờ bạn duyệt, hoặc làm luôn.
- **Trò chuyện với AI quản lý** của từng task: thấy từng bước nó làm, trả lời câu hỏi, bấm “Đồng ý, tiến hành” khi nó chờ duyệt,
  nhắn thêm yêu cầu sửa. Task tạo từ Claude Code cũng nhắn tiếp được (quản lý web sẽ đọc lại task rồi làm tiếp).
- **Dừng** quản lý, **huỷ** một worker đang chạy. Đổi AI làm việc hoặc cách giao việc giữa chừng, áp dụng từ lượt sau.
- Nếu lượt của quản lý kết thúc khi worker còn chạy, worker bị dừng. Khi đó phần dở được lưu vào `results/dang-do-*.txt`,
  và quản lý tự được gọi lại để giao lại phần đó (tối đa 2 lần).
- Theo dõi: bước hiện tại trong 6 bước, việc con nào xong, worker nào đang chạy và chạy bao lâu, kết quả từng worker,
  nhật ký, yêu cầu và kết quả cuối. Tab trình duyệt hiện số task đang chờ bạn, ví dụ “(1) Pentagon”.

**Quản lý nhân viên** (`/nhan-vien`): mỗi tài khoản AI là một **nhân viên**, xếp theo **phòng ban**:
Phòng Claude, Phòng Codex, Phòng Gemini.
- **Tuyển nhân viên**: thêm một tài khoản mới (tên, phòng ban, vai trò, model), rồi **đăng nhập ngay trên web**.
  - Trình duyệt trên máy tự mở trang đăng nhập; trang web hiện link dự phòng và ô dán mã nếu cần.
  - Gemini cũng đăng nhập trên web: bấm “Mở trang đăng nhập Google”, đăng nhập, rồi dán mã Google hiện ra vào ô trên thẻ nhân viên.
  - Không cần chạy lệnh nào để đăng nhập. `bin/login <tên>` vẫn dùng được nếu bạn thích terminal.
- Mỗi nhân viên có:
  - trạng thái (🟢 rảnh, 🟡 đang làm, 🔴 chưa đăng nhập) và usage;
  - nút **Đăng nhập lại / Đăng xuất / Sửa / ↑↓**, để đổi thứ tự ưu tiên trong phòng;
  - nút **Cho tạm nghỉ**, để nhân viên không nhận việc;
  - nút **Cho nghỉ việc**, để bỏ khỏi danh sách và có thể xoá luôn thông tin đăng nhập đã lưu.
- Mọi thay đổi được ghi vào `config/workers.conf`. Nhân viên tạm nghỉ được ghi thành dòng `#tắt: …`.

**Văn phòng làm việc**: mỗi AI là một nhân viên ngồi một bàn.
- **Ban điều hành**: các AI quản lý đang chạy, mỗi cái thuộc task nào, đang ở bước nào, dùng model và tài khoản nào.
- **Nhân viên**: từng worker đang làm việc gì (bấm vào để mở task), rảnh hay bận, có hết hạn mức không.
- **Usage**: % hạn mức gói thuê bao đã dùng, kèm giờ làm mới. Claude có khung 5 giờ và 7 ngày; Codex là hạn mức của gói.
  Có thêm số lần gọi và token trong ngày, cùng số việc xong và số lỗi Pentagon tự đếm.
  Số liệu lấy từ chính các lần chạy, không tốn thêm lượt gọi. Claude được cập nhật sau mỗi lần chạy;
  Codex đọc từ `~/.codex/sessions`; Gemini chưa có nguồn số liệu.

### Subagent theo vai trò và hỏi tiếp
- Quản lý giao việc cho subagent kèm **vai trò** (`bin/ask -r …`, định nghĩa trong `config/roles/*.md`, sửa được ở Cài đặt):
  **Lập trình** (`code`), **Viết nội dung** (`viet`), **Tra cứu** (`tra-cuu`), **Kiểm tra** (`review`).
  Tra cứu và Kiểm tra luôn chỉ được đọc. Làm xong việc quan trọng, quản lý giao một subagent Kiểm tra (khác loại) soát lại.
- Mỗi kết quả lưu kèm **mã phiên** của subagent.
- **Hỏi tiếp** (trang Agent hoặc tab Kết quả của task):
  - Claude chạy trên **bản sao phiên** (`--fork-session`), nên phiên gốc và kết quả gốc giữ nguyên.
  - Codex chạy phiên mới, kèm việc và câu trả lời cũ làm ngữ cảnh.
  - Câu trả lời hiện ngay dưới báo cáo gốc, thành chuỗi hỏi–đáp.

### Model theo cỡ task
AI quản lý tự phân loại task là **nhỏ / vừa / lớn** để chọn model; bảng chọn nằm ở `config/models.conf` (sửa trên web: Cài đặt → Model theo cỡ việc):

| | Nhỏ | Vừa | Lớn |
|---|---|---|---|
| AI quản lý | haiku | sonnet | opus |
| Worker claude | haiku | sonnet | opus |
| Worker codex | gpt-6-luna, suy nghĩ ít | gpt-6-luna, vừa | gpt-6-luna, nhiều |

- Mỗi việc con, quản lý gọi `bin/ask … -s nho|vua|lon` theo độ khó của chính việc đó.
- **Chọn theo từng tin nhắn, không chốt cứng.** Dưới ô nhắn cho quản lý có 3 ô chọn:
  - **Quản lý dùng**: Tự động hoặc model cụ thể.
    - Tự động: quản lý xem yêu cầu mới lớn hay nhỏ rồi chọn model cho lượt đó. Câu ngắn kiểu "tiếp tục / đồng ý" thì giữ model đang dùng.
    - Hoặc chọn Nhỏ / Vừa / Lớn hay đúng tên model.
  - **Giao cho**: quản lý tự chọn, hoặc chỉ định một nhân viên (kèm trạng thái rảnh / bận) làm việc của lượt này.
  - **Model nhân viên**: model cho nhân viên vừa chọn. Danh sách lấy từ bảng model của phòng ban đó.
  - Mọi lựa chọn đều được ghi vào khung trao đổi.
- Quản lý cũng tự đổi được cỡ giữa chừng bằng `bin/manager size`.

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
muốn cho thêm quyền (vd chạy test python) hay đổi model: vào **Cài đặt → Quyền của AI quản lý** (lưu vào `config/manager.conf`).

**Cài đặt → AI quản lý và nhân viên** (không cần sửa file; áp dụng từ lượt sau của quản lý / lần gọi worker sau):
- **Quyền của AI quản lý**: công tắc theo nhóm (Tải trang web, Tìm trên mạng, Chạy Python, Node/npm, Git, curl/wget,
  Chuyển đổi ảnh…), danh sách mọi quyền đang có (bỏ từng quyền bằng ×), ô thêm quyền riêng theo cú pháp `--allowedTools`
  của Claude Code (vd `Bash(ffmpeg:*)`, `WebFetch(domain:example.com)`; dấu cách chỉ được nằm trong ngoặc), và chọn model mặc định.
- **Model theo cỡ việc**: sửa trực tiếp bảng `config/models.conf` (AI quản lý, Claude, Codex, Gemini × nhỏ/vừa/lớn).
  Ô là tên model, có thể thêm `@low|medium|high|xhigh|max`; `-` = không đổi. Ô sai được tô đỏ và không lưu được.
- **Vai trò subagent**: xem, sửa, thêm, xoá vai trò trong `config/roles/` (tên hiển thị, mô tả, quyền chỉ đọc / được sửa file,
  lời dặn). Kiểm tra và Tra cứu luôn chỉ đọc; 4 vai trò mặc định không xoá được. Quản lý được báo danh sách vai trò mới ở mỗi lượt.
- Các dòng chú thích `#` trong file được giữ nguyên khi lưu; file được ghi an toàn (ghi file tạm rồi thay).
Không có web thì dùng dòng lệnh tương đương: `bin/manager new|send|stop|kill-worker` (xem `bin/manager --help`).

Bảo mật:
- Web chỉ nghe trên `127.0.0.1`, nên máy khác không vào được.
- Web chặn các yêu cầu đến từ trang web lạ.
- Muốn có trang đăng nhập: vào **⚙ Cài đặt** trên web → đặt mật khẩu. Đổi hoặc tắt cũng ở đó (cần mật khẩu hiện tại).
  Mật khẩu chỉ lưu dạng băm trong `config/auth.conf`, file này không lên git.
- **Xem trên điện thoại** (Cài đặt → Xem trên điện thoại):
  - Bật lên thì trang mở thêm cho mạng Wi-Fi nội bộ, kèm địa chỉ và mã QR để quét.
  - Bắt buộc phải đặt mật khẩu trước; điện thoại vào phải đăng nhập.
  - Chỉ bật/tắt được trên chính máy Mac. Tắt mật khẩu thì truy cập từ điện thoại tự đóng.
  - Kết nối trong Wi-Fi nhà không mã hoá (http), nên chỉ dùng ở mạng tin cậy.
- Đừng mở cổng này ra Internet.

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
- Tài khoản phụ (claude-2, codex-2…) cũng phải đăng nhập lại trên máy mới: trang Nhân viên → “Đăng nhập”.
- Model riêng của từng worker (vd `gpt-6-luna` cho Codex) nằm trong `workers.conf`, đi theo thư mục, không cần cấu hình thêm.
- Dùng **nhiều máy cùng lúc** được, nhưng chung hạn mức gói thuê bao. Thư mục `tasks/` mỗi máy riêng —
  muốn chung lịch sử thì đồng bộ dự án qua git (repo **private**) hoặc iCloud/Dropbox.
  Muốn giữ `tasks/` riêng từng máy: bỏ dấu `#` dòng `tasks/` trong `.gitignore`.

## Thêm tài khoản (bao nhiêu cũng được)

Cách dễ nhất: trang **Quản lý nhân viên** trên web → “+ Tuyển nhân viên”. Hoặc làm tay:

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
| `bin/pt_accounts.py` | Quản lý nhân viên: thêm/sửa/bật tắt/xếp thứ tự/xoá tài khoản, đăng nhập trên web |
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
