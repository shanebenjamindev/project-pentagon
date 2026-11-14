<!-- worker: codex-main (codex) | 2026-11-15 00:51:37 | 27s | quyền: đọc | thư mục: /Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a | model: gpt-6-luna@low · cỡ nho | vai trò: review | phiên: 01a1db2f-4568-7332-be70-00449ccec0b9 | hỏi tiếp:  -->
## Việc được giao

Review thay đổi trong web/index.html: kanban view được sửa để mỗi cột (.kcol) có scroll riêng qua .kbody thay vì cả trang cuộn. Xem CSS .kanban/.kcol/.kbody, hàm fitKanban (đặt ngay trước function setPart) và đoạn render kanban (tìm 'kbody'). Kiểm tra: cú pháp JS đúng (trích các <script> rồi node --check), layout grid đúng (cột cao bằng khung nhìn, card dài thì cột tự cuộn), giữ vị trí cuộn khi render lại, không hỏng các theme web/theme-*.css và chế độ mobile. Trả lời ngắn: OK hoặc liệt kê lỗi cụ thể kèm cách sửa.

## Trả lời

**CHƯA ĐẠT**

- **NÊN SỬA — khung Kanban không theo chiều cao viewport trên màn hình hẹp:** `.kanban` đặt `height` dựa trên viewport và `min-height:360px`, còn `.page` có padding dọc. Vì vậy trên điện thoại ngắn, cột có thể vượt khỏi màn hình thay vì vừa khung nhìn. Tính chiều cao theo không gian thực còn lại hoặc điều chỉnh quy tắc mobile.
- **NÊN SỬA — kiểm tra cú pháp chưa hoàn tất:** lệnh trích script rồi chạy `node --check` không chạy được do lỗi escape trong lệnh kiểm tra. Cần chạy lại bằng cách trích script đúng cách rồi kiểm tra từng đoạn.
- **GÓP Ý — giữ scroll chỉ dựa theo thứ tự cột:** `renderDH` khôi phục `scrollTop` theo chỉ số cột. Hiện thứ tự cố định nên hoạt động; nếu sau này cột được sắp xếp hoặc thay đổi, vị trí cuộn có thể gắn nhầm cột. Dùng khóa cột để lưu/khôi phục sẽ bền hơn.

Các `.kbody` có `overflow-y:auto` và `min-height:0`, phù hợp để cuộn riêng; `fitKanban()` cập nhật chiều cao khi resize. Các theme đã kiểm tra không ghi đè cấu trúc cuộn. **## Kết quả:** CHƯA ĐẠT; cần xử lý chiều cao trên mobile và hoàn tất kiểm tra cú pháp JS.