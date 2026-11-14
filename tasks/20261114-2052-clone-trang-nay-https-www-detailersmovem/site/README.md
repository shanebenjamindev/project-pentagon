# Detailers Movement — trang chủ tĩnh

Bản dựng lại trang chủ từ nội dung công khai có thể đọc được tại https://www.detailersmovement.com/. Mã nguồn nằm trong `index.html`, `css/styles.css`, `js/main.js`; trang dùng đường dẫn tương đối và chạy cục bộ bằng cách mở `index.html` hoặc qua một web server tĩnh.

## Giới hạn của bản sao

- Môi trường không phân giải được tên miền khi dùng `curl` (`Could not resolve host`). Vì vậy HTML/CSS/JS và ảnh gốc của website không thể tải xuống trực tiếp.
- Nội dung và thứ tự các phần được dựng lại theo văn bản trang chủ có thể đọc từ trình duyệt web. Ảnh hero, ảnh khách hàng, logo đối tác, ảnh đội ngũ và video portfolio đã được thay bằng đồ họa CSS/nhãn chữ tự dựng; màu, khoảng cách và font là ước lượng, không phải trích xuất chính xác từ CSS gốc.
- Trang không phụ thuộc vào thư viện ngoài; font dùng Manrope/DM Sans nếu có sẵn trên máy và tự rơi về Arial sans-serif.
- Biểu mẫu liên hệ và đăng ký nhận tin chỉ hiển thị thông báo demo, không gửi dữ liệu.

## Cấu trúc

- `index.html` — trang chủ và nội dung
- `css/styles.css` — bố cục, màu sắc và breakpoint responsive
- `js/main.js` — menu di động và phản hồi form tĩnh
- `img/` — thư mục dành cho ảnh cục bộ (ảnh gốc chưa tải được)
