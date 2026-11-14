# Kết quả: Paste ảnh khi giao task / chat quản lý

## Đã làm
- **Frontend (web/index.html):** ô giao task và ô chat quản lý nhận ảnh bằng dán (Ctrl/⌘+V), kéo-thả hoặc nút 📎. Ảnh hiện thành thumbnail, mỗi ảnh có nút xoá. Chỉ nhận PNG/JPEG/GIF/WebP, tối đa 8 ảnh, mỗi ảnh ≤ 5MB, tổng ≤ 40MB. Dán từ nguồn vừa có chữ vừa có ảnh thì chữ vẫn được dán. Gửi được khi chỉ có ảnh, khi đó nội dung là "Xem ảnh đính kèm".
- **Backend (bin/pt_web.py, bin/pt_manager.py):**
  - Kiểm tra MIME, base64 và magic bytes, rồi lưu ảnh vào `<task>/attachments/` với tên do server sinh có hậu tố ngẫu nhiên.
  - Nối đường dẫn tuyệt đối của ảnh vào brief.md (khi giao task) hoặc vào tin nhắn (khi chat), để quản lý dùng Read xem ảnh.
  - Giới hạn body 56MB chỉ áp dụng cho `/api/giao` và `/api/send`, và chỉ khi đã đăng nhập. Các trường hợp khác vẫn 200KB.
  - Kiểm tra id task trước khi ghi file và chặn path traversal. Nếu gửi lỗi thì xoá ảnh vừa ghi.
- **Xem ảnh:** ảnh trong `attachments/` tự hiện trong mục sản phẩm của trang task, qua luồng `/files` sẵn có.

## Ai làm
- codex-main: cài đặt, rồi sửa theo review.
- claude-3: review lần 1, kết luận CHƯA ĐẠT với 2 lỗi nghiêm trọng (giới hạn dung lượng, path traversal) và 5 mục nên sửa. Codex đã sửa hết.
- Quản lý: đọc lại các đoạn code chính.

## Chưa chắc chắn
- Chưa thử trực tiếp trên trình duyệt. Cần khởi động lại `bin/dashboard` để chạy code mới.
- Chưa review lại lần 2 sau khi sửa. Quản lý chỉ đọc lại các điểm chính: thứ tự kiểm tra đăng nhập/giới hạn body và kiểm tra id ở /api/send.
