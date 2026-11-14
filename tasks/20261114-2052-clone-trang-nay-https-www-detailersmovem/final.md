# Kết quả: clone detailersmovement.com (toàn bộ trang + form)

- `site_orig/`: bản sao thật của 79 trang (trang chủ, dịch vụ, blog, career, contact, terms…) cùng 909 ảnh, CSS, JS, font tải từ trang gốc (147 MB, 0 file lỗi). Link nội bộ đã đổi sang đường dẫn tương đối.
- `server.py`: backend cục bộ. Chạy `python3 server.py` rồi mở http://127.0.0.1:8000. Form được trỏ về `/api/form`, lưu vào `submissions.jsonl`; xem tại `/api/submissions`.
- `mirror.py`: script crawl (chạy lại được, có resume).
- Làm bởi: quản lý tự chạy (worker không có quyền mạng/python).

## Chưa chắc / giới hạn
- Chưa mở thử trên trình duyệt; chưa chạy thử server.py.
- Backend WordPress/Elementor thật (CSDL, admin, email gửi form, plugin phía server) KHÔNG thể sao chép từ bên ngoài; chỉ dựng backend thay thế nhận form. Form không gửi email.
- Một số JS Elementor (animation, popup) có thể gọi admin-ajax gốc; vẫn còn vài link/metadata trỏ về domain gốc.
- Dùng làm bản mẫu/học; lưu ý bản quyền nội dung.
