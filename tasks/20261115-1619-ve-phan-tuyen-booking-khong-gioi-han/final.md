# Blog tuyển BOOKING không giới hạn — Denhaag Bar (vòng 2)

## Kết quả
- **Màu và font:** trang blog dựng lại theo đúng nhận diện trong marketing plan:
  - navy `#031725` làm nền chính, trắng ngà `#f5f5f2`, đỏ rượu `#b20c2b` cho nút và điểm nhấn;
  - font Barlow Condensed cho tiêu đề, Be Vietnam Pro cho chữ thường;
  - các phần nền navy và nền trắng ngà xen kẽ nhau. Không còn đen + vàng.
- **Ảnh:** tăng từ 5 lên 15 ảnh, mỗi mục lớn có ảnh minh hoạ cạnh bên, thêm gallery 8 ảnh.
- **Hero:** đổi thành ảnh biển hiệu DEN HAAG BAR phát sáng trong hẻm đêm. Có bản ngang cho máy tính và bản dọc cho điện thoại, đã cắt bỏ tấm standee "399K". Sửa lỗi khoảng đen trống đầu trang.
- **Retouch:** cả 15 ảnh làm cùng một kiểu chỉnh màu: nâng vùng tối, khử nhiễu, làm nét, vùng tối ngả navy, vùng sáng ấm, tăng độ bão hoà, tối nhẹ ở viền. Khung hình cắt từ video được phóng to cho đủ nét. Ảnh so sánh trước/sau nằm ở `ref/retouch-compare/`.
- **Thông tin quán:** lấy từ fanpage: tên Denhaag Bar, TP.HCM, quán bar/cà phê ban đêm. Link fanpage đã gắn vào bài và nút liên hệ.
- **Số liệu:** giữ nguyên như vòng 1: 25% hoa hồng trên bill trước thuế; thưởng 2/3/4/5 triệu; ví dụ 7/14/30 triệu. Bài ghi rõ thu nhập ví dụ không phải cam kết.

## Ai làm phần nào
- claude-3: chọn ảnh, dựng lại trang HTML và bản markdown.
- codex (mark-1): xuất kho ảnh và khung hình video, retouch 2 lần, làm hero, dọn ảnh cũ không dùng.
- Quản lý: lấy màu và font từ HTML của marketing plan, lấy thông tin từ fanpage, chọn ảnh hero, duyệt ảnh retouch.

## Chưa chắc chắn / chủ cần làm
- Chưa chụp được màn hình để kiểm tra giao diện thật: trình duyệt Chrome chạy ngầm bị chặn trong môi trường của worker. Anh mở `blog/index.html` bằng trình duyệt để xem, cả trên điện thoại.
- Vẫn cần điền `[SĐT/ZALO]` và `[ĐỊA CHỈ]`. Nút liên hệ đang trỏ tạm về fanpage.
- Ảnh biển hiệu ở mục "Cách ứng tuyển" vẫn còn tấm standee "399K unlimited drinks", dễ bị nhầm với mức thu nhập. Anh muốn bỏ thì em đổi ảnh khác.
- Một số ảnh có khách và nhân viên. Nên hỏi họ có đồng ý xuất hiện trong quảng cáo không.

## Sản phẩm
- `blog/index.html`
- `blog/images/`
- `blog/blog.md`
- `blog/ads-copy.md`
