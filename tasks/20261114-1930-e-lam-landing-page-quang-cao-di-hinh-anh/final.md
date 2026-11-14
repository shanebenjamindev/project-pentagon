# Kết quả: Landing page quảng cáo Pentagon

## Đầu ra
- `site/index.html`: 50KB, một file tự chứa (CSS/JS inline, không tải gì từ mạng). Mở trực tiếp bằng trình duyệt.
- `site/img/`: ảnh do AI tự vẽ bằng SVG, không dùng ảnh stock.
  - `hero.svg`: AI quản lý màu tím nối tới các worker màu xanh.
  - `feature-rotate.svg`, `feature-size.svg`, `feature-safe.svg`, `feature-dashboard.svg`: mỗi ảnh minh hoạ một tính năng.
  - `og.svg` và `og.png`: ảnh hiện khi chia sẻ link lên mạng xã hội.
  - `favicon.svg`: biểu tượng trên tab trình duyệt.
  - `mark.png`: logo có sẵn.

## Nội dung trang
Trang có các mục:
- Hero có 2 nút "Bắt đầu ngay" và "Xem quy trình".
- 4 lợi ích: đỡ tốn công, tận dụng gói đã trả tiền, không lo hết hạn mức giữa chừng, theo dõi được mọi thứ.
- Sơ đồ cách hoạt động.
- 4 tính năng có ảnh, xếp so le trái/phải.
- 2 dải kêu gọi hành động.
- Quy trình 6 bước.
- Đội worker.
- Bắt đầu nhanh: 3 khối lệnh, mỗi khối có nút Sao chép.
- Bảng "chạy ở đâu".
- Hỏi đáp và footer.

Trang có chế độ sáng/tối (nhớ lựa chọn của người xem) và đổi bố cục theo chiều rộng màn hình, xuống tới 375px. Có thẻ meta để hiện ảnh xem trước khi chia sẻ link. Nội dung chỉ lấy từ README và bản yêu cầu landing page Pentagon trong task trước, không có số liệu, khách hàng, lời khen hay giá nào bị bịa ra.

## Hiệu ứng chuyển động (thêm theo yêu cầu sau)
- **Khi tải trang:** chữ ở đầu trang hiện lần lượt, ảnh lớn đầu trang lơ lửng nhẹ, nền màu trôi chậm, nút chính có vệt sáng lướt qua.
- **Khi cuộn:** các khối hiện dần và trượt lên, các khối cùng nhóm hiện so le. Ở mục tính năng, ảnh và chữ trượt vào từ hai phía.
- **Thanh điều hướng:** có thanh tiến trình đọc màu tím → xanh ở mép trên, đổ bóng khi đã cuộn, tự đánh dấu mục đang xem.
- **Rê chuột:** thẻ nổi lên, ảnh phóng nhẹ. Mũi tên trong sơ đồ có dòng chảy.
- **Ảnh động:**
  - Ở ảnh đầu trang, đường nối chạy, chấm dữ liệu di chuyển và vầng sáng quanh AI quản lý nhấp nháy.
  - Ở ảnh xoay vòng tài khoản, mũi tên xoay và thanh tiến độ chạy.
  - Ở ảnh dashboard, chấm "đang chạy" nhấp nháy và thanh tiến độ chạy.
- **An toàn:**
  - Người đã tắt chuyển động trong máy sẽ thấy trang tĩnh, đủ nội dung.
  - Khi JS không chạy hoặc bị lỗi, nội dung vẫn hiện đủ.
  - Khoảng trượt tối đa 32px.
- **Chưa xem trên trình duyệt.** Quản lý mới chỉ đọc mã.

## Ai làm gì
- **codex-main** (`-s vua`): vẽ bộ ảnh SVG.
- **claude-main** (`-s lon`): viết nội dung quảng cáo và dựng `index.html`. Lượt chạy bị dừng giữa chừng nhưng file đã viết xong.
- **claude-main** (`-s vua`): làm tiếp phần còn lại, kiểm tra thẻ meta và ảnh.
- **claude-2** (`-s vua`): thêm hiệu ứng chuyển động. claude-main hết hạn mức nên việc tự chuyển sang claude-2.
- **Quản lý**: đọc lại toàn bộ `index.html` (nội dung, ảnh, CSS cho điện thoại và chế độ tối) và không phải sửa gì.

## Chưa xong
1. **`og.png` còn lỗi**: mất chữ, chỉ một phần ảnh có nền tối. Lý do là ImageMagick không vẽ được chữ trong SVG. Ở chế độ chạy nền, các công cụ khác cũng không chạy được: Chrome thoát mã 134, qlmanage bị sandbox chặn, sips cần duyệt quyền. File `og.svg` thì đúng. Chủ chạy tay lệnh sau từ thư mục task:
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars --window-size=1200,630 --screenshot="$PWD/site/img/og.png" "file://$PWD/site/img/og.svg"
   ```
2. **Chưa chụp ảnh màn hình để xem trang thật**, cùng lý do. Mọi kiểm tra mới chỉ là đọc mã. Chủ mở `site/index.html` bằng trình duyệt để xem. Có thể chụp ảnh màn hình bằng lệnh trên, đổi `--window-size=375,9000` và đổi đường dẫn sang `site/index.html`.
3. **Thẻ `og:image` đang dùng đường dẫn tương đối** (`img/og.png`). Facebook, Zalo và X cần URL đầy đủ, nên khi đưa trang lên tên miền thật thì phải đổi thành `https://<tên-miền>/img/og.png`.
4. **Chưa có worker khác loại kiểm tra chéo trang.** Chỉ có quản lý tự đọc mã.
