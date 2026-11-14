# tôi muốn 1 hình ảnh con mèo

## Yêu cầu gốc (nguyên văn)

tôi muốn 1 hình ảnh con mèo

## Yêu cầu đã tối ưu
- Mục tiêu: Có 1 hình ảnh minh hoạ một con mèo, dùng được ngay.
- Đầu ra mong muốn: `results/cat.svg` (bản vector) và `results/cat.png` nếu convert được. Con mèo đơn giản, rõ ràng, nền trắng.
- Ràng buộc: Hệ thống hiện không có công cụ tạo ảnh AI (Gemini đang tắt), nên ảnh được vẽ bằng code SVG. Không dùng ảnh bản quyền từ internet.
- Tiêu chí xong: `cat.svg` hợp lệ, mở trình duyệt hiển thị đúng con mèo. Có `cat.png` nếu convert được.
- Giả định:
  - Chủ muốn ảnh minh hoạ (vẽ), không phải ảnh chụp thật. Nếu muốn ảnh chụp/ảnh AI thật, cần bật worker tạo ảnh (vd Gemini gói trả phí).
  - Kích thước 1024x1024, phong cách flat, đơn giản.
