# Kết quả (lần 2 — theo phản hồi "giao diện như WordPress")

Sửa `web/index.html`:
- Màn hình > 900px: bố cục kiểu WordPress admin — thanh trên cùng (header) full chiều ngang, dính trên đầu;
  menu dọc nền tối (#1d2327) cố định bên trái, nằm ngay dưới header (JS đo chiều cao header → biến `--hh`).
- Mỗi mục menu có icon SVG + chữ; hover xanh nhạt; mục đang mở nền màu accent + mũi tên nhỏ bên phải như WP.
- Nút "Thu gọn menu" ở đáy: thu menu chỉ còn icon (52px), nhớ trạng thái trong localStorage.
- Nội dung trang dịch sang phải theo độ rộng menu (`--sw`), không còn đẩy header như bản trước (nguyên nhân lỗi UI).
- Kiểu menu được ép (!important) để đồng nhất trên mọi theme (cổ điển, quân sự, siêu anh hùng, apple).
- ≤ 900px (điện thoại/tablet): giữ nav ngang cũ, ẩn icon.

Chưa kiểm tra được bằng trình duyệt (không có quyền chạy Chrome headless; dashboard cần đăng nhập).
