<!-- worker: claude-main (claude) | 2026-11-15 01:26:32 | 52s | quyền: đọc | thư mục: /Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/web | model: haiku · cỡ nho | vai trò: review | phiên: fc6be49d-ded3-4161-9ff4-d505cf683102 | hỏi tiếp:  -->
## Việc được giao

Kiểm tra (chỉ đọc, KHÔNG sửa) web/index.html: chuông Thông báo trong header giờ là nút (#notiBtn) mở một bảng nổi (#notiPanel) ngay dưới chuông, kiểu Facebook, không chuyển trang. Kiểm tra: (1) notiWrap/notiBtn/notiPanel có đúng cấu trúc, id trùng lặp không; (2) hàm setNotiOpen, renderNotiPanel, các listener click/Escape có logic đúng không: bấm chuông mở/đóng, bấm ngoài đóng, bấm một thông báo đánh dấu đọc và mở task, bấm Xem tất cả đóng bảng; (3) pollNotifications gọi renderNotiPanel khi bảng đang mở; (4) CSS .notipanel dùng biến theme (--panel, --line, --radius, --shadow, --soft, --accent), không cố định màu; bảng không bị che bởi header hay sidebar trên desktop (min-width 901px), không tràn trên điện thoại (max-width 700px). Trả lời tiếng Việt, ngắn: liệt kê lỗi cụ thể kèm số dòng, hoặc ghi KHÔNG CÓ LỖI.

## Trả lời

**Kiểm tra `web/index.html`: chuông Thông báo (#notiBtn) và bảng nổi (#notiPanel)**

**NGHIÊM TRỌNG:** Không có.

**NÊN SỬA:**
1. **Biến `--shadow` không được định nghĩa ở đâu cả**, dòng 300 (`.notipanel`) dùng `box-shadow:var(--shadow),0 12px 32px rgba(0,0,0,.18)`. `--shadow` chỉ có trong `theme-apple.css`. Không có trong `index.html`, `theme-quan-su.css` hay `theme-sieu-anh-hung.css`. Ở ba giao diện đó, biến không xác định làm cả khai báo `box-shadow` mất hiệu lực, nên bảng không có bóng đổ. Cách sửa: thêm `--shadow` vào `:root` của `index.html` và vào hai file theme còn thiếu, hoặc bỏ `var(--shadow),` khỏi dòng 300 và dùng bóng cố định.
2. **Bóng cố định `rgba(0,0,0,.18)` ở dòng 300** không theo theme. Nếu muốn đúng yêu cầu "không cố định màu", nên đưa vào biến cùng với `--shadow`.

**GÓP Ý:**
3. **Đánh dấu đọc khi bấm một thông báo (dòng 1375–1381)**: `post(...)` không được chờ và `NOTI` không được cập nhật tại chỗ. Khi mở lại bảng trước lần poll kế tiếp, mục vẫn có nền "chưa đọc" và số trên chuông vẫn còn. Nên đánh dấu `n.read=true` trong `NOTI` rồi cập nhật `#nCount`.
4. **Bảng được vẽ lại mỗi lần poll khi đang mở (dòng 1358 gọi `renderNotiPanel`)**: `innerHTML` thay toàn bộ danh sách. Nếu poll rơi đúng lúc người dùng đang bấm, lượt bấm có thể bị hụt, và vị trí cuộn có thể bị reset. Nên so sánh dữ liệu trước khi vẽ lại, hoặc chỉ vẽ lại khi `NOTI.items` thay đổi.
5. **Bấm Escape hoặc bấm ngoài đóng bảng nhưng không trả focus về chuông**: nên gọi `$("#notiBtn").focus()` trong `setNotiOpen(false)` khi đóng bằng Escape.

**Đã kiểm tra và đúng:**
- **Cấu trúc và id (dòng 498–504):** `notiWrap`, `notiBtn`, `notiPanel`, `notiList`, `notiAll`, `nCount`, `nPanelRead` đều xuất hiện đúng một lần. Không có id trùng.
- **`setNotiOpen` (dòng 1368–1371):** bật/tắt `hidden`, `aria-expanded`, class `open`, và vẽ lại khi mở.
- **Listener (dòng 1372–1383):**
  - Bấm chuông: `stopPropagation` và toggle, đúng.
  - Bấm ngoài: kiểm tra `closest("#notiWrap")`, đúng.
  - Bấm một thông báo: đánh dấu đọc, đóng bảng, mở task (kèm `/ket-qua` nếu là `xong`), đúng.
  - Bấm "Xem tất cả": đóng bảng rồi để `data-link` điều hướng, đúng.
  - Escape: đóng bảng, đúng.
- **`pollNotifications` (dòng 1358):** gọi `renderNotiPanel` khi bảng đang mở, đúng. `tick` gọi `pollNotifications`, và `act` gọi `tick`, nên nút "Đánh dấu đã đọc" cũng cập nhật bảng.
- **Bố cục desktop (≥901px):** header là sticky với `z-index:7`, lớn hơn `.nav` (`z-index:6`). Bảng nằm trong header nên không bị sidebar che. Bảng neo bên phải chuông nên không bị menu trái che.
- **Bố cục điện thoại (≤700px):** `.notiwrap` có `margin-left:auto`, bảng rộng `min(380px, 100vw-24px)` và neo `right:0`, nên không tràn khỏi màn hình.
- **Biến theme:** `--panel`, `--line`, `--radius`, `--soft`, `--accent` có trong `index.html` và cả ba theme. Riêng `--shadow` là lỗi như mục 1.

**Kết quả:** **ĐẠT**, không có lỗi nghiêm trọng. Có một mục NÊN SỬA (biến `--shadow` không định nghĩa ở 3/4 nguồn, làm bảng mất bóng đổ ở các theme đó). Các mục còn lại là góp ý. Tôi chỉ đọc, không sửa file nào.