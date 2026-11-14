<!-- worker: claude-main (claude) | 2026-11-14 20:19:24 | 90s | quyền: sửa | thư mục: /Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/tasks/20261114-2017-lam-landing-page-quang-cao-dich-vu-xe/code | model: sonnet · cỡ vua -->
## Việc được giao

Tạo file index.html (HTML+CSS+JS thuần, 1 file, không thư viện ngoài, responsive, mobile-first) trong thư mục hiện tại: landing page tiếng Việt quảng cáo gara dịch vụ xe ô tô tên mẫu 'AutoCare Garage' (sửa chữa, bảo dưỡng, rửa/detailing, cứu hộ). Gồm: header dính + nút gọi, hero với CTA mạnh, dải số liệu, dịch vụ (6 thẻ), vì sao chọn chúng tôi, bảng giá 3 gói, quy trình 4 bước, đánh giá khách hàng, form đặt lịch (tên, SĐT, loại xe, dịch vụ, ngày; JS validate + thông báo thành công), FAQ accordion, footer có SĐT/địa chỉ giữ chỗ, nút gọi nổi trên mobile. Thiết kế hiện đại, đẹp, tông tối xanh/cam, dùng emoji/SVG thay ảnh. SĐT/địa chỉ/giá là dữ liệu mẫu dễ thay.

## Trả lời

Đã tạo `index.html` trong thư mục `code/`. Tôi chưa mở trang trên trình duyệt hay chạy thử JS, nên mới chỉ viết xong, chưa kiểm tra bằng cách chạy.

## Kết quả

**File:** `tasks/20261114-2017-lam-landing-page-quang-cao-dich-vu-xe/code/index.html`. Đây là một file duy nhất gồm HTML, CSS và JS thuần, không dùng thư viện hay ảnh ngoài.

**Các phần có trong trang:**
- **Header và hero:** header dính có nút gọi. Hero có hai nút: "Đặt lịch – giảm 10% lần đầu" và "Gọi cứu hộ ngay". Hình xe vẽ bằng SVG.
- **Dải số liệu:** bốn số liệu, ba số đếm tăng dần khi cuộn tới.
- **Dịch vụ, vì sao chọn, bảng giá, quy trình:** 6 thẻ dịch vụ, khối "vì sao chọn chúng tôi" kèm cam kết bảo hành 12 tháng, bảng giá 3 gói (Cơ bản 490K, Tiêu chuẩn 1.290K có nhãn "phổ biến nhất", Cao cấp 2.990K) và quy trình 4 bước.
- **Đánh giá:** 3 đánh giá khách hàng.
- **Form đặt lịch:** có tên, SĐT, loại xe, dịch vụ, ngày. JS kiểm tra từng trường (SĐT dạng `0xxxxxxxxx` hoặc `+84…`, ngày không ở quá khứ) và hiện lỗi ngay dưới ô nhập. Gửi thành công thì hiện thông báo kèm nút "Đặt lịch khác". Bấm "Chọn gói" ở bảng giá sẽ điền sẵn dịch vụ vào form.
- **FAQ, footer, nút gọi nổi:** FAQ dạng accordion, mỗi lần mở một mục. Footer có SĐT và địa chỉ giữ chỗ. Nút gọi nổi chỉ hiện trên mobile (dưới 760px).
- **Giao diện:** mobile-first, tông tối xanh và cam, tôn trọng `prefers-reduced-motion`.

**Giả định và lưu ý:**
- SĐT mẫu là `0900 000 000` (`tel:0900000000`), địa chỉ là "123 Đường Mẫu, Quận 1, TP. Hồ Chí Minh", email là `lienhe@autocare.example`. Tất cả giá cũng là dữ liệu mẫu. Muốn thay thì tìm và thay các chuỗi này trong file.
- Form chưa gửi dữ liệu đi đâu cả. Chỗ nối backend, Zalo hoặc Google Sheet có comment `TODO` ở cuối đoạn JS.