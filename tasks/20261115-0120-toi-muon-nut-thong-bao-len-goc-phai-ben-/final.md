# Kết quả: thông báo dạng bảng nổi dưới chuông

## Đã làm (web/index.html)
- Bấm chuông (góc phải header) mở bảng thông báo nổi ngay dưới chuông, không chuyển trang. Bấm lại, bấm ra ngoài hoặc Esc để đóng.
- Bảng có tiêu đề, nút "Đánh dấu đã đọc", danh sách 30 thông báo mới nhất (chấm xanh = chưa đọc), và "Xem tất cả" mở trang /thong-bao.
- Bấm một thông báo: đánh dấu đã đọc, cập nhật số trên chuông, đóng bảng và mở task (kết quả nếu là "xong").
- Màu, viền, bo góc lấy từ biến theme (--panel, --line, --radius, --soft, --accent), nên đi theo giao diện đang chọn.
- Điện thoại: bảng rộng tối đa 100vw-24px, neo phải.

## Ai làm
- Quản lý sửa file.
- claude-main (vai review, cỡ nho) kiểm tra chéo: báo bóng đổ dùng biến --shadow không có ở 3/4 theme (đã sửa: bóng cố định), đánh dấu đọc chưa cập nhật ngay (đã sửa), Esc chưa trả focus (đã sửa). Góp ý vẽ lại danh sách mỗi lượt poll chưa sửa (ảnh hưởng nhỏ).

## Chưa chắc chắn
- Chưa mở trình duyệt xem bảng trên từng theme và trên điện thoại; mới kiểm tra bằng đọc mã và cú pháp JS.
- Trang /thong-bao vẫn còn (qua "Xem tất cả").
