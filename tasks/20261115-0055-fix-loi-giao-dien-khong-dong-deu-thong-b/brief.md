# Sửa UI: giao diện lệch, toast góc phải, lỗi kết nối, ảnh báo quá dài

## Yêu cầu gốc (nguyên văn)

fix lỗi giao diện không đồng đều, thông báo cho lên góc phải, lỗi kết nối gì kìa, có ảnh vào thì báo nội dung quá dài là sai logic tạo task

## Yêu cầu đã tối ưu
- Mục tiêu: sửa 4 lỗi của web dashboard Pentagon (web/index.html, bin/pt_web.py, web/theme-*.css).
  1. Giao diện không đồng đều: chuẩn hoá khoảng cách, độ rộng khung trang, tiêu đề, thẻ, nút giữa các trang (Điều hành, Văn phòng, Agents, Nhân viên, Thông báo, Cài đặt, chi tiết task) và giữa các theme.
  2. Thông báo (toast) chuyển lên góc trên bên phải, xếp chồng được nhiều cái, tự ẩn, hợp mọi theme.
  3. "Lỗi kết nối": dòng "mất kết nối tới bin/dashboard" hiện sai. Nguyên nhân quản lý tìm được: dashboard (PID 78164) chạy từ 21:20 bằng code Python CŨ, còn index.html được đọc lại từ đĩa nên gọi API mới → mọi lỗi bị gộp thành "mất kết nối". Sửa: tách thông báo theo nguyên nhân (server tắt / lỗi HTTP / hết phiên); lỗi của phần trang con không bị ghi thành mất kết nối; server báo "đang chạy code cũ, cần khởi động lại" khi file .py/.html đổi sau lúc khởi động.
  4. Có ảnh thì báo "nội dung quá dài": cũng do server cũ (giới hạn body 200 KB). Sửa thêm phía client: thu nhỏ/nén ảnh trước khi gửi; lỗi 413 báo rõ là ảnh quá lớn.
- Đầu ra: code đã sửa trong worktree, không commit.
- Ràng buộc: một codex worker khác đang sửa cùng file (hàng chờ tin nhắn) → sửa từng chỗ nhỏ, đọc lại file trước khi sửa, không đụng logic inbox/queue.
- Tiêu chí xong: py_compile ok; test hiện có chạy qua; toast ở góc phải; ảnh 3–5 MB giao được; "mất kết nối" chỉ hiện khi server thật sự không trả lời.
- Giả định: "không đồng đều" = khoảng cách/kích thước lệch giữa các trang và theme (chủ không gửi ảnh chụp). Sau khi sửa, chủ phải khởi động lại bin/dashboard để server nạp code mới.
