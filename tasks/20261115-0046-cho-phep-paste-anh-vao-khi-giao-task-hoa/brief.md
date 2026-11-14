# Paste ảnh khi giao task / chat quản lý

## Yêu cầu gốc (nguyên văn)

cho phép paste ảnh vào khi giao task hoặc chat quản lý

## Yêu cầu đã tối ưu
- Mục tiêu: trên web app Pentagon, chủ dán (Ctrl/⌘+V), kéo-thả hoặc chọn ảnh vào ô "giao task" (#newText) và ô chat quản lý (#msg); ảnh được gửi kèm để AI quản lý xem được.
- Đầu ra mong muốn:
  - Frontend (web/index.html): bắt paste/drop ảnh, hiện thumbnail xem trước có nút xoá, nút 📎 chọn ảnh; gửi kèm ảnh khi giao/gửi.
  - Backend (bin/pt_web.py, bin/pt_manager.py nếu cần): nhận ảnh base64 trong JSON, kiểm tra loại (png/jpeg/gif/webp) và kích thước, lưu vào `<task>/attachments/`, nối đường dẫn tuyệt đối của ảnh vào brief/tin nhắn để quản lý (Claude CLI) dùng Read xem ảnh.
  - Giới hạn body riêng cho endpoint có ảnh (≤ ~20MB, ≤ 8 ảnh); endpoint khác giữ 200KB.
  - Trang task xem được ảnh đính kèm.
- Ràng buộc: không thêm thư viện ngoài; giữ bảo mật hiện có (X-Pentagon, Origin, đăng nhập); tên file do server sinh; không phá luồng cũ khi không có ảnh.
- Tiêu chí xong: dán ảnh vào cả 2 ô → có preview → gửi → file nằm trong attachments/ và đường dẫn có trong brief.md / tin nhắn gửi quản lý; py_compile qua; review không còn lỗi nghiêm trọng.
- Giả định: chỉ hỗ trợ ảnh; ảnh nằm trong thư mục task nên xoá task là xoá ảnh.
