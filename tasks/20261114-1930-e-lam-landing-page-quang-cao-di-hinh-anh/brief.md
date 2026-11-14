# Landing page quảng cáo (ảnh tự tạo)

## Yêu cầu gốc (nguyên văn)

ê làm landing page quảng cáo đi, hình ảnh tự gen

## Yêu cầu đã tối ưu
- Mục tiêu: một landing page quảng cáo hấp dẫn, thuyết phục người xem dùng thử sản phẩm.
- Sản phẩm (GIẢ ĐỊNH, chờ chủ xác nhận): **Pentagon** — hệ thống "1 người giao việc, 1 AI quản lý, nhiều AI làm"
  (nội dung lấy từ README.md và `tasks/20261114-1803-.../landing/PROMPT.txt`).
- Đầu ra mong muốn: thư mục `site/` trong task này gồm `index.html` (tự chứa CSS/JS, không CDN) + thư mục `img/`
  chứa các ảnh minh hoạ do AI tự tạo (hero, 3–5 ảnh minh hoạ tính năng, ảnh chia sẻ mạng xã hội og:image 1200x630).
- Hình ảnh "tự gen": không dùng ảnh stock/ảnh có bản quyền. Ưu tiên ảnh do công cụ tạo ảnh của worker sinh ra;
  nếu worker không có công cụ tạo ảnh thì vẽ minh hoạ bằng SVG (vector, nhẹ, sắc nét mọi màn hình).
- Ràng buộc: tiếng Việt có dấu; responsive 375px → màn rộng; sáng/tối; không bịa số liệu, khách hàng, lời chứng thực, giá.
- Tiêu chí xong: mở `site/index.html` trực tiếp bằng trình duyệt là chạy, mọi ảnh hiển thị, không lỗi console,
  không cuộn ngang ở 375px, có CTA rõ ràng ("Bắt đầu" → khối lệnh cài đặt).
- Giả định: sản phẩm là Pentagon; phong cách hiện đại, công nghệ, màu theo web app Pentagon (tím = quản lý, xanh = worker).
