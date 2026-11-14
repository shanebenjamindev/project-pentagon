# Thử nghiệm `claude -p --input-format stream-json` (stdin giữ mở)

## Tình trạng: CHƯA CHẠY ĐƯỢC trong phiên worker

Phiên worker này bị chặn quyền chạy lệnh: `python3 …`, `bash script.sh`, `bin/workers`, kể cả
`python3 -m py_compile` đều báo "This command requires approval" (chạy không tương tác, không có ai duyệt).
Ghi file vào `/tmp` cũng bị từ chối. Vì vậy tôi **không có số liệu đo thật**: các mục dưới đây là
kịch bản đã chuẩn bị sẵn và hành vi **dự kiến**, code đã viết để đúng với **cả hai** khả năng.

## Script đã chuẩn bị (trong `work/exp/` của task này)

| File | Việc |
|---|---|
| `exp1.sh <out.jsonl> [HOLD]` | Thử nghiệm thật (haiku, thư mục tạm bằng `mktemp -d`): tin 1 = 3 lệnh `sleep 5` lần lượt; sau 8s gửi tin 2 dạng `{"type":"user","message":{"role":"user","content":"…"}}`; giữ stdin thêm HOLD giây rồi đóng. Xem `out.jsonl` để biết tin 2 vào trước hay sau `result` đầu tiên, đếm số `result`. Thêm cờ ở cuối, vd `--replay-user-messages`, hoặc thay `--session-id` bằng `--resume <sid>` (chạy lần 2 với SID in ra ở lần 1). |
| `exp1.py` | Bản Python của cùng thử nghiệm: gửi tin 2 ngay khi thấy `tool_use` đầu tiên, đóng stdin sau `CLOSE_AFTER` event result, in dòng thời gian. Biến môi trường: `CLOSE_AFTER`, `SEND2`, `MODE` (`--session-id`/`--resume`), `SID`. |
| `test_live.py <repo>` | Mô phỏng `run_turn` thật với một `claude` giả (đọc stdin, 3 bước × 1,5s, đọc tin mới giữa các bước), task giả trong thư mục tạm, không gọi API. In OK/FAIL cho: tin 2 vào giữa lượt, inbox trống sau khi nạp, có event "giữa lượt", `pentagon_owner` không trùng, tin gửi sau khi đóng stdin vẫn được `drain_inbox` mở lượt mới, cờ `live` đã xoá, claude giả thoát do EOF. |

Lệnh đề nghị (chủ hoặc quản lý chạy):
```bash
python3 -m py_compile bin/*.py
python3 -I tasks/20261115-0146-khi-chat-voi-quan-ly-co-the-chat-luon-ma/work/exp/test_live.py "$PWD"
bash tasks/20261115-0146-khi-chat-voi-quan-ly-co-the-chat-luon-ma/work/exp/exp1.sh /tmp/out1.jsonl 60
bash tasks/20261115-0146-khi-chat-voi-quan-ly-co-the-chat-luon-ma/work/exp/exp1.sh /tmp/out2.jsonl 60 --replay-user-messages
```

## Câu hỏi cần trả lời và hành vi dự kiến (chưa xác nhận)

| Câu hỏi | Dự kiến | Code xử lý thế nào |
|---|---|---|
| Tin 2 vào giữa lượt hay thành lượt riêng? | Claude Code bản mới đưa tin xếp hàng vào giữa lượt ở ranh giới tool (như gõ thêm trong chế độ tương tác); bản cũ xử lý thành lượt riêng sau `result` của tin 1. | Đúng với cả hai: tin đã ghi vào stdin luôn được claude xử lý (giữa lượt hoặc lượt nối tiếp trong cùng tiến trình). |
| Khi nào tiến trình thoát? | Chỉ khi stdin bị đóng (EOF) **và** đã xử lý xong mọi tin đã nhận. Stdin còn mở thì chờ mãi sau `result`. | Đóng stdin khi gặp `result` mà hàng chờ trống / `result` lỗi; thêm lưới an toàn: 30 phút không có event nào thì đóng stdin. |
| Số event `result`? | Một `result` cho mỗi lượt; chèn giữa lượt thì 1, lượt riêng thì 2. | `chat()` hiện mỗi `result` thành "Hết lượt · …" — 2 dòng nếu tách lượt, không rối. `scan_limit` lấy `result` cuối. |
| Cần `--replay-user-messages`? | Không. Cờ này chỉ in lại tin user ra stdout để xác nhận. | Không dùng: tin của chủ đã có `pentagon_owner`; `chat()` bỏ qua event `user` nên có dùng cũng không bị trùng. |
| `--resume` / `--session-id` chạy cùng stream-json input? | Có (Agent SDK dùng đúng tổ hợp này). | Giữ nguyên logic `--resume`/`--session-id` cũ. |
| Hỏi quyền khi chạy chế độ stream-json | Chế độ stream-json input là chế độ SDK; mặc định `--permission-prompts host` có thể gửi `control_request` chờ host trả lời → **có thể treo**. | Thêm `--permission-prompts none` (từ chối luôn, giống chế độ text cũ). Cờ có trong `claude --help` của máy này. |

**Cần xác nhận bằng `exp1.sh`** trước khi dùng thật, nhất là: (1) đóng stdin khi claude còn tin chưa xử lý
thì claude vẫn làm nốt (không bỏ tin); (2) `--permission-prompts none` được chấp nhận cùng `--input-format stream-json`.
