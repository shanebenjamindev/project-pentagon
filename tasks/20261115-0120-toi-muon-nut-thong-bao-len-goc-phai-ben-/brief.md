# Đưa nút Thông báo lên góc phải trên

## Yêu cầu gốc (nguyên văn)

tôi muốn nút thông báo lên góc phải bên trên

Ảnh đính kèm (dùng công cụ Read để xem):
- /Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/tasks/20261115-0120-toi-muon-nut-thong-bao-len-goc-phai-ben-/attachments/img-20261115-012030-01-20d2d6.png

## Yêu cầu đã tối ưu
- Mục tiêu: nút "Thông báo" (icon chuông + số đếm chưa đọc) hiện đang nằm trong menu dọc bên trái (sidebar) trên màn hình rộng; chuyển nó lên thanh trên cùng (header), góc phải.
- Đầu ra mong muốn: nút chuông ở góc phải header, bấm vào mở trang /thong-bao; hiện badge số chưa đọc; trạng thái "đang ở trang này" được tô sáng. Mục Thông báo không còn trong sidebar.
- Ràng buộc: sửa trong web/index.html (một file). Không đổi API, không đổi đường dẫn /thong-bao, giữ nguyên các giao diện (theme). Điện thoại vẫn dùng được.
- Tiêu chí xong: nút chuông nằm bên phải header (cạnh nút đổi sáng/tối); sidebar không còn mục Thông báo; số đếm vẫn cập nhật (#nCount); không lỗi JS.
- Giả định: "góc phải bên trên" = thanh header trên cùng, bên phải. Chủ không yêu cầu đổi nội dung trang Thông báo.
