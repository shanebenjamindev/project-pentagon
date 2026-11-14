# Chuyển form "Giao task mới" thành popup

## Yêu cầu gốc (nguyên văn)

phần giao task nên là dạng popup

## Yêu cầu đã tối ưu
- Mục tiêu: trên dashboard web (web/index.html), form "Giao task mới" hiện là trang riêng (`/giao`). Đổi thành popup (modal) mở ngay trên trang hiện tại khi bấm "+ Giao task", giống modal "Sửa task" và "Sửa nhân viên" đang có.
- Đầu ra mong muốn: chỉ sửa `web/index.html` (và `web/*.css` nếu cần). Nút "+ Giao task" mở modal `#giaoModal` gồm đúng các trường hiện có: textarea nội dung, "Giao cho AI", "Cách giao việc", "Duyệt kế hoạch", chú thích rảnh/bận, nút Huỷ và "Giao task". Giao thành công thì đóng modal rồi chuyển sang trang task mới (như hiện tại).
- Ràng buộc:
  - Giữ nguyên hành vi: Ctrl/⌘+Enter để giao; Esc hoặc bấm nền ngoài để đóng; focus vào textarea khi mở; dropdown chọn worker hoạt động trong modal; nút đang gửi bị disable.
  - Đường dẫn `/giao` vẫn hoạt động: mở modal trên trang Điều hành thay vì trang riêng.
  - Không đổi backend (`bin/pt_web.py`) và API `/api/giao`.
  - Dùng lại class `.modal` / `.box` đã có; hoạt động ở giao diện sáng/tối và trên điện thoại.
- Tiêu chí xong: bấm "+ Giao task" mở popup; giao được task; đóng được bằng Huỷ/Esc/bấm nền; không lỗi JS (đọc lại code `<script>`); không đổi phần khác của trang.
- Giả định: "popup" = modal overlay như các modal sẵn có. Bỏ section `data-page="giao"` và nhánh `R.page==="giao"`, thay bằng modal; `/giao` mở modal.
