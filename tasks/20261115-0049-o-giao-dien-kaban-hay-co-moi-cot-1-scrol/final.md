# Kanban: mỗi cột cuộn riêng — xong

## Đã sửa (web/index.html)
- `.kanban` cao vừa khung nhìn (biến `--kh`, tính bằng `fitKanban()` khi render và khi đổi cỡ cửa sổ; tối thiểu 280px) → trang không còn cuộn dài theo cột dài nhất.
- Mỗi cột: tiêu đề cố định, danh sách thẻ nằm trong `.kbody` có `overflow-y:auto` → mỗi cột có thanh cuộn riêng.
- Khi dashboard tự làm mới, vị trí cuộn từng cột được giữ nguyên.
- Màn hình hẹp vẫn cuộn ngang giữa các cột như cũ; các theme không bị ảnh hưởng.

## Ai làm
- Quản lý (claude) tự sửa (việc nhỏ).
- codex-main review (-r review, -s nho): góp ý chiều cao tối thiểu trên mobile → đã hạ 360→280px; kiểm tra cú pháp JS: 4 script, không lỗi.

## Chưa chắc
- Chưa xem trực tiếp trên trình duyệt; cần tải lại trang dashboard (Ctrl/Cmd+Shift+R) để thấy.
