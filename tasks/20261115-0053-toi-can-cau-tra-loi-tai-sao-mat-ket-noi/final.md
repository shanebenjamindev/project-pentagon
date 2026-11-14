# Vì sao báo "mất kết nối"

**Giả định:** "mất kết nối" là thông báo *"mất kết nối tới bin/dashboard — đang thử lại…"* trên web dashboard. Nếu bạn muốn nói về kết nối tới một AI worker, hãy cho tôi biết.

## Thông báo này phát ra ở đâu
- `web/index.html:1507`: khối `catch` của hàm `tick()` ghi thông báo này khi bất kỳ lỗi nào xảy ra.
- `web/index.html:1608`: `tick()` chạy mỗi 3 giây và gọi `/api/tasks`. Vì `catch` gộp mọi lỗi nên thông báo không phân biệt được nguyên nhân.
- Khi server sống lại, `tick()` tự thử lại; thông báo sẽ biến mất ở lần tải thành công kế tiếp.

## Nguyên nhân khả dĩ (xếp theo khả năng)
1. **Tiến trình dashboard bị dừng.** `bin/dashboard` chạy trên foreground trong một terminal. Ctrl+C, đóng cửa sổ terminal, Mac ngủ hoặc khởi động lại đều làm server tắt, nên trang không gọi được API. Các quản lý đang chạy nền vẫn tiếp tục (`pt_web.py`, lời in khi khởi động), nên task không mất, chỉ giao diện mất kết nối.
2. **Dashboard được khởi động lại làm mất phiên đăng nhập.** Phiên lưu trong bộ nhớ (`bin/pt_web.py:148-156`), nên restart là mất hết. Khi đó server trả 401 và `apiFetch` chuyển về `/login` (`web/index.html:705-706`). Người dùng sẽ thấy như bị đăng xuất, không phải thông báo mất kết nối. Phiên có hiệu lực 7 ngày nếu không restart (`pt_web.py:45`). Đổi hoặc đặt mật khẩu cũng xoá mọi phiên khác (`pt_web.py:150-152`).
3. **Cổng đã đổi.** Nếu cổng 8765 bị chiếm, `cmd_dashboard` thử 8766-8774 (`pt_web.py:852-857`). Tab cũ mở ở 8765 sẽ không kết nối được nữa. Dashboard in đúng địa chỉ khi khởi động.
4. **Truy cập sai địa chỉ (ít khả năng).** `host_ok` (`pt_web.py:483-488`) chỉ nhận `127.0.0.1:PORT` hoặc `localhost:PORT`. Truy cập qua IP LAN (điện thoại) chỉ được khi đã bật chia sẻ LAN, có mật khẩu và đúng IP nội bộ. Nếu không khớp, server từ chối và trang báo mất kết nối.

## Hiện tại
- Tiến trình `bin/tracker.py dashboard` (PID 78164) đang chạy, bắt đầu lúc 9:20PM. Vì vậy kết nối hiện tại không bị đứt.
- Không có file log của dashboard (chạy foreground, không ghi log), nên **không xác minh được** lần mất kết nối cụ thể nào do nguyên nhân nào.

## Cách xác minh
- Xem terminal đang chạy `bin/dashboard` có dòng báo dừng hoặc lỗi không.
- So thời điểm mất kết nối với giờ dashboard khởi động (9:20PM hôm nay). Nếu dashboard vừa được khởi động lại, nguyên nhân là 1 hoặc 2. Nếu dashboard không khởi động lại mà vẫn báo mất kết nối, cần kiểm tra thêm: máy có ngủ không, tab cũ có trỏ sai cổng không.

## Gợi ý cải thiện (chưa làm, chờ bạn quyết)
- Tách thông báo theo nguyên nhân (mất mạng / server tắt / hết phiên) thay vì một câu chung.
- Lưu phiên ra file để restart dashboard không đăng xuất.
- Chạy dashboard nền bằng `launchd` hoặc `nohup` để đóng terminal không làm mất giao diện.

## Ai làm gì
- Quản lý tự đọc code và kiểm tra tiến trình. Việc chỉ đọc nên không giao worker, không chạy kiểm tra chéo.
- Không sửa code, không commit.
