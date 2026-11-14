# Sửa lỗi nav dọc trên giao diện

## Yêu cầu gốc (nguyên văn)

kiểm tra giao diện hiện tại nav lỗi rồi

## Yêu cầu đã tối ưu
- Mục tiêu: tìm và sửa lỗi hiển thị menu dọc (nav kiểu WordPress) vừa làm ở task 20261115-0042.
- Đầu ra: sửa `web/index.html` để menu dọc cố định bên trái hiển thị đúng trên mọi theme (cổ điển, quân sự, siêu anh hùng, apple).
- Ràng buộc: không đổi bố cục mobile (≤900px); giữ hiệu ứng kính mờ của header nếu được.
- Tiêu chí xong: menu dọc cao hết màn hình, dưới header, không bị cắt trên theme mặc định và Apple; có review chéo.
- Giả định: "nav lỗi" = menu dọc không hiện/bị kẹt trên màn hình rộng (theme mặc định là siêu anh hùng).
