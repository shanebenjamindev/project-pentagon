# Kết quả: làm UI đồng đều

## Đã sửa (web/index.html, web/theme-sieu-anh-hung.css, web/theme-apple.css)
1. **Lề trang:** nội dung giờ cân giữa vùng bên phải menu dọc, lề trái bằng lề phải (biến `--gut`, lề tối thiểu `--page-x` 24px). Khi thu gọn menu vẫn đúng.
2. **Hai cột:** "Trao đổi với AI quản lý" và "Nhật ký" rộng bằng nhau (1fr:1fr), đáy thẳng hàng, nhật ký cuộn bên trong. Các khối "Worker đang chạy", "Kế hoạch", "Yêu cầu" trải hết bề ngang ở bên dưới. Màn ≤1250px vẫn 1 cột.
3. **Chiều cao điều khiển:** nút, chip, chuông, ô chọn và ô nhập trên cùng một hàng giờ cao bằng nhau (`--ctl-h` / `--ctl-h-sm`), áp cho cả thanh header.
4. **Font theo vai trò:** chữ phụ cạnh tiêu đề thẻ, dòng "Cỡ hiện tại…" và các nhãn "Giao việc"/"AI làm" dùng chung một kiểu chữ. Nút "Giao task" giờ giống các nút khác.
5. **Khung chat:** tin của quản lý trải đủ hai lề; tin của chủ nằm bên phải, bỏ gradient chói (giao diện Siêu anh hùng). Khoảng đệm đều nhau. Vùng cuộn có viền nên không còn sát thanh "Quản lý đang làm".
6. **Thanh tab và khoảng cách dọc:** khung thanh tab ôm vừa các tab. Khoảng cách giữa thanh bước, dòng tóm tắt, thanh tab và lưới cùng là 16px (`--sect`).
- File theme đổi `?v=5` để trình duyệt tải lại CSS.

## Ai làm
- claude-main (claude, cỡ lớn, vai trò code): sửa CSS.
- mark-1 (codex, cỡ vừa, vai trò review): review chéo. Không có lỗi nghiêm trọng, đánh giá **ĐẠT**.

## Chưa chắc chắn
- **Chưa kiểm tra bằng mắt.** Không ai chụp được ảnh trình duyệt vì chạy Chrome headless cần quyền duyệt. Người sửa cũng không mở được ảnh của chủ, nên làm theo mô tả của quản lý.
- **Bố cục hai cột phụ thuộc thứ tự markup** (`display:contents`, `:first-child`). Nếu sau này đổi cấu trúc `#tabProgress` thì bố cục sẽ lệch. Review gợi ý chuyển sang dùng class riêng.
- **Chữ phụ cạnh tiêu đề thẻ giờ viết hoa.** Ở trang Cài đặt, dòng phụ dài có thể trông nặng.
- **Chỉ sửa 2 giao diện.** Task khác (0128) đã xoá giao diện Quân sự và Cổ điển, nên chỉ còn Siêu anh hùng và Apple.
- **Chưa commit.** `web/index.html` còn chứa thay đổi của task nút thông báo. Trạng thái trước khi sửa lưu ở `truoc-khi-sua.patch`.
