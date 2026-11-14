# Chat với quản lý ngay trong lúc đang chạy (như Claude)

## Yêu cầu gốc (nguyên văn)

khi chat với quản lý có thể chat luôn mà không làm sai luồng, như claude ấy

## Yêu cầu đã tối ưu
- Mục tiêu: trên web, khi quản lý ĐANG chạy một lượt, chủ gõ tin nhắn thì quản lý nhận được NGAY trong lượt đó
  (ở bước kế tiếp, giống gõ thêm khi Claude Code đang làm), không phải đợi hết lượt (có thể >10 phút) mới đọc,
  và không làm hỏng lượt đang chạy (không dừng worker, không mở lượt song song, thứ tự hội thoại đúng).
- Hiện trạng: `bin/pt_manager.py` chạy `claude -p` với stdin là một tin duy nhất; tin gửi lúc bận bị ghi vào
  `manager/inbox.jsonl` và chỉ được gộp thành lượt mới khi lượt hiện tại kết thúc (`drain_inbox`).
- Đầu ra: sửa `bin/pt_manager.py` (run_turn dùng `--input-format stream-json`, giữ stdin mở, có luồng nạp tin từ
  inbox vào stdin trong lúc chạy; đóng stdin an toàn khi lượt xong và hàng chờ trống) và chữ hiển thị trên
  `web/index.html` ("đã xếp hàng" → "đã gửi, quản lý đọc ở bước kế tiếp"); giữ nguyên Dừng / Xoá hàng chờ /
  đổi tài khoản khi hết hạn mức.
- Ràng buộc: không phá luồng cũ (task tạo từ terminal, --resume, chuyển tài khoản, hết hạn mức, auto_continue);
  không mất tin khi có tranh chấp (tin tới đúng lúc lượt kết thúc → vẫn được xử lý, đúng 1 lần).
- Tiêu chí xong: thử thật bằng `claude -p --input-format stream-json` cho thấy tin gửi giữa lượt được đọc trước
  khi lượt kết thúc; code qua review chéo; `python3 -m py_compile` OK.
- Giả định: "sai luồng" = tin bị xếp hàng/đọc trễ hoặc làm rối lượt đang chạy. Tin có chọn model riêng vẫn nạp
  ngay (model không đổi giữa lượt được — chỉ áp dụng cho lượt sau).
