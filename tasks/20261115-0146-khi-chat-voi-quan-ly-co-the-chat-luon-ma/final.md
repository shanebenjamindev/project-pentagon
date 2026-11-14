# Kết quả: chat với quản lý ngay trong lúc đang chạy

## Đã làm
Trước đây tin chủ gửi lúc quản lý đang làm bị xếp hàng, phải đợi hết lượt (có khi >10 phút) quản lý mới đọc.
Giờ giống Claude Code: **cứ nhắn thêm, quản lý đọc ngay ở bước kế tiếp trong chính lượt đang chạy**, không ngắt
worker, không mở lượt song song.

- `bin/pt_manager.py`
  - `run_turn` chạy `claude -p --input-format stream-json` và giữ stdin mở; class `LiveTurn` nạp tin từ
    `manager/inbox.jsonl` vào lượt mỗi ~1 giây (dưới `inbox_lock`), ghi event "Quản lý đã nhận tin (giữa lượt)".
  - Lượt xong mà hàng chờ trống → đóng stdin; tin tới sau đó vẫn mở lượt mới như cũ (không mất, không trùng).
  - Tin đã nạp nhưng chưa chắc xử lý xong được lưu bền ở `manager/inflight.jsonl`: lượt lỗi / hết hạn mức /
    bấm Dừng / tiến trình chết → tin quay lại đầu hàng chờ. Lỗi quá 2 lần thì bỏ, có báo (tránh lặp vô hạn).
  - Đã Dừng (`inbox.paused`) thì không nạp gì. Đổi tài khoản khi hết hạn mức, auto_continue giữ nguyên.
  - Thêm `--permission-prompts none` để chế độ stream-json không treo chờ hỏi quyền.
- `bin/pt_usage.py`: một tiến trình giờ có thể ra nhiều `result`, mà chi phí/token trong `result` là số cộng dồn →
  lấy số lớn nhất thay vì cộng (tránh thống kê usage bị đếm lố).
- `web/index.html`: gợi ý "Cứ nhắn thêm — quản lý sẽ đọc ngay ở bước kế tiếp", toast "Đã gửi…", dải hàng chờ chỉ
  hiện khi tin thật sự còn chờ (đã Dừng hoặc lượt sắp xong).

## Kiểm tra
- Chạy thật với Claude (haiku): tin 2 gửi lúc đang chạy lệnh → được đọc ngay trong lượt, chỉ 1 `result`.
- Chạy thật: tin tới sát cuối lượt rồi đóng stdin → Claude vẫn xử lý nốt (2 `result`, thoát 0).
- Mô phỏng `run_turn` với claude giả (`work/exp/test_live.py`): 10/10 kiểm tra đạt (nạp giữa lượt, không trùng
  event, tin sau lượt mở lượt mới, inflight được xác nhận/trả lại, lỗi 2 lần thì bỏ).
- `python3 -m py_compile` OK.

## Ai làm gì
- claude-main (Claude, -r code, -s lon): thiết kế + viết phần chính, script thử.
- mark-1 (Codex, -r review): review 2 vòng — tìm ra 2 lỗi mất tin (lượt lỗi, bấm Dừng) và 1 khe hẹp.
- Quản lý: chạy thử thật, sửa 3 lỗi review bằng `inflight.jsonl`, sửa thống kê usage.

## Chưa chắc chắn / lưu ý
- Code mới áp dụng ngay cho các lượt quản lý mới. Phần chữ trên web và nút Dừng phiên bản mới chỉ có hiệu lực
  đầy đủ sau khi dashboard được khởi động lại (vd lần mở máy sau); trước đó chat giữa lượt vẫn chạy, chỉ là toast
  còn ghi "Đã xếp hàng".
- Trường hợp hiếm: tin tới đúng lúc trả lời cuối của một lượt không dùng công cụ mà lượt sau lại lỗi → tin được trả
  về hàng chờ và có thể bị đọc 2 lần (có ghi chú "có thể bạn đã thấy tin này" cho quản lý).
- Chưa commit git.
