# Kết quả: sửa giao diện, toast, lỗi kết nối, lỗi ảnh "nội dung quá dài"

## Nguyên nhân gốc của "lỗi kết nối" và "nội dung quá dài"
Dashboard (PID 78164) chạy từ 21:20 nên vẫn dùng code Python **cũ**. index.html thì được đọc lại từ đĩa mỗi lần tải, nên trang gọi tới các API mới mà server cũ chưa có. Server trả 404, và trang gộp mọi lỗi thành "mất kết nối". Server cũ cũng chỉ nhận body tối đa 200 KB, nên giao task kèm ảnh bị báo "nội dung quá dài".
→ **Chủ cần tắt và chạy lại `bin/dashboard`** thì phần sửa phía server mới có hiệu lực.

## Đã sửa
1. **Toast lên góc trên bên phải:** hiện ngay dưới header, xếp chồng tối đa 4 cái, tự ẩn sau 4 giây (lỗi: 6 giây, màu đỏ), bấm vào để tắt.
2. **Thông báo kết nối:**
   - Chỉ báo "mất kết nối" khi thật sự không gọi được server.
   - Server trả lỗi thì ghi rõ "server trả lỗi <mã> ở <api>".
   - Lỗi vẽ trang thì báo riêng.
   - Server mới tự nhận ra file .py đã đổi sau lúc khởi động và hiện dải vàng "Dashboard đang chạy code cũ — hãy chạy lại bin/dashboard". Trang cũng tự đoán ra trường hợp này khi API trả 404.
3. **Ảnh:**
   - Ảnh được thu nhỏ/nén trước khi gửi (cạnh dài tối đa 2000px, JPEG 0.85; ảnh có nền trong suốt giữ PNG; GIF giữ nguyên).
   - Lỗi 413 giờ báo rõ là ảnh quá lớn kèm giới hạn.
   - Server đọc hết body trước khi trả 413 để trình duyệt nhận đúng mã lỗi, không bị lỗi mạng.
   - Sửa thêm lỗi chọn nhiều ảnh cùng lúc chỉ giữ được ảnh đầu.
4. **Giao diện đồng đều:**
   - Thêm biến CSS chung cho khoảng cách, bo góc, padding, chiều cao nút/ô nhập.
   - Mọi trang dùng chung kiểu tiêu đề, khoảng cách và độ rộng tối đa.
   - Thẻ, nút và ô nhập cùng kích thước ở cả 3 theme. Theme đổi lên `?v=3` để trình duyệt tải CSS mới.

## Ai làm gì
- **claude-3** (code, cỡ lớn): sửa cả 4 mục.
- **mark-1/codex** (review): tìm thấy 1 lỗi: thông báo 404 không bật cảnh báo code cũ. Quản lý đã tự sửa (`pollNotifications` dùng `getJSON`).
- **codex** (chạy kiểm tra): `py_compile` đạt, `tests/test_inbox_smoke.py` 10/10 OK, `node --check` các script inline đạt.

## Chưa chắc chắn
- Chưa xem bằng trình duyệt thật và chưa thử server ở cổng phụ (sandbox chặn mở cổng). Cần chủ khởi động lại dashboard rồi xem thử.
- "Không đồng đều" được hiểu là khoảng cách và kích thước lệch giữa các trang. Nếu chủ muốn nói chỗ khác, gửi ảnh chụp.
- Có một worker khác (hàng chờ tin nhắn) đang sửa cùng các file này. Test sau cùng vẫn đạt.
