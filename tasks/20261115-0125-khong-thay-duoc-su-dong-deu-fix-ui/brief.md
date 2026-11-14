# Làm UI đồng đều (lề, cột, cỡ nút, font)

## Yêu cầu gốc (nguyên văn)

không thấy được sự đồng đều, fix ui

Ảnh đính kèm (dùng công cụ Read để xem):
- /Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/tasks/20261115-0125-khong-thay-duoc-su-dong-deu-fix-ui/attachments/img-20261115-012523-01-d86120.jpg

## Yêu cầu đã tối ưu
- **Mục tiêu:** giao diện web Pentagon (ảnh: trang chi tiết task, giao diện "Siêu anh hùng" tối, màn hình rộng, menu dọc bên trái) trông đều đặn, cân đối.
- **Các chỗ lệch quan sát được trong ảnh:**
  1. Nội dung trang dồn trái: lề trái (sát menu dọc) ~28px nhưng lề phải ~190px; nút trên thanh trên chạy tới mép phải còn nút SỬA/XOÁ dừng sớm hơn.
  2. Hai cột "Trao đổi với AI quản lý" và "Nhật ký" rộng khác nhau, đáy không thẳng hàng.
  3. Chiều cao điều khiển không đều: ô chọn "Quản lý tự chọn" cao hơn nút; chip "6 RẢNH", chuông, nút SÁNG/ĐĂNG XUẤT, nút SỬA… mỗi thứ một cỡ.
  4. Font lẫn lộn trong cùng vai trò: chữ phụ "mới nhất ở trên" kiểu mono thường, dòng "Cỡ hiện tại…" chữ thường không dấu đồng bộ, số liệu header mono…
  5. Khung chat: bong bóng quản lý hẹp hơn khung và lệch; thanh "Quản lý đang làm" che nội dung cuộn; bong bóng của chủ gradient chói, khác hẳn phong cách phần còn lại.
  6. Thanh tab "Kết quả công việc / Tiến độ" bọc trong khung trải ngang trống; nhịp khoảng cách dọc giữa các khối (thanh bước, dòng tóm tắt, tab, lưới 2 cột) không đều.
- **Đầu ra:** sửa CSS (và HTML nếu cần) trong `web/index.html` + các file `web/theme-*.css`.
- **Ràng buộc:** giữ nguyên chức năng và JS; giữ bản sắc từng giao diện (Cổ điển, Apple, Quân sự, Siêu anh hùng); không vỡ trên điện thoại (≤700px); ưu tiên sửa bằng biến dùng chung (`--page-max`, `--ctl-h`, `--gap`…) để mọi trang/giao diện cùng đều; không xoá các thay đổi chưa commit của task "nút thông báo lên góc phải" (đang nằm trong web/index.html).
- **Tiêu chí xong:** 6 điểm trên được xử lý; lề trái/phải nội dung bằng nhau; hai cột đều và thẳng đáy; mọi nút/ô chọn cùng hàng cao bằng nhau; review chéo không còn lỗi nghiêm trọng.
- **Giả định:** "đồng đều" = cân đối lề, kích thước và kiểu chữ thống nhất; áp cho mọi trang chứ không chỉ trang trong ảnh, trọng tâm là trang chi tiết task.
