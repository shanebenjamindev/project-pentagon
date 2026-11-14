# Kết quả: làm tiếp phiên "Pentagon task tracking display"

Phiên cũ (Claude, tài khoản Phapsubenjamin) đứt lúc ~21:25 ngày 14/11 vì hết hạn mức 5 giờ, ngay sau khi chủ "ok" việc đưa cấu hình lên trang Cài đặt, và chủ vừa báo lỗi "khi ấn để xem thì mất".

## Đã làm
1. **Lỗi "ấn để xem thì mất"** (quản lý tự sửa, `web/index.html`): trang có ô "mật khẩu hiện tại" nên trình duyệt tưởng là form đăng nhập
   và tự điền tên đăng nhập `pentagon` vào ô tìm task → Phòng Điều hành lọc mất hết task.
   Sửa: thêm ô tên đăng nhập ẩn cho form mật khẩu, tắt tự điền ở ô tìm, và bỏ qua mọi giá trị bị điền vào khi ô chưa được bấm vào.
2. **3 thẻ mới trong trang Cài đặt** (claude-main viết, codex-main chạy thử + sửa):
   - Quyền AI quản lý (`config/manager.conf`): bật/tắt theo nhóm, danh sách quyền xoá/thêm được, chọn model quản lý. Tách quyền có dấu cách đúng (không còn lỗi `-I`).
   - Bảng model theo cỡ (`config/models.conf`): sửa từng ô Nhỏ/Vừa/Lớn, có kiểm tra giá trị.
   - Vai trò subagent (`config/roles/`): xem/sửa/thêm/xoá; review và tra-cuu khoá ở chỉ đọc; 4 vai trò mặc định không xoá được; chặn đường dẫn lạ.
   - API: `GET /api/config`, `POST /api/config/manager | models | roles/save | roles/delete` (cần đăng nhập như các API khác). README đã cập nhật.
   - File sửa: `bin/pt_manager.py`, `bin/pt_web.py`, `web/index.html`, `README.md`. File cấu hình thật không bị đụng.

## Kiểm tra
- Codex: biên dịch 7 module Python, import, `node --check` JS: đạt. Thử lưu/đọc cả 3 phần trên bản sao bằng gọi hàm trực tiếp: đạt;
  dữ liệu sai bị chặn; `tier_spec` đọc đúng. Codex sửa thêm 2 lỗi: cho đổi review/tra-cuu sang quyền sửa, và symlink thư mục roles.
- Quản lý: soát kiểm tra đăng nhập của API mới, xác nhận đã dọn bản thử.

## Chưa chắc
- **Chưa thử qua trình duyệt/HTTP thật** (sandbox của worker không mở được cổng): chưa xem bố cục 3 thẻ ở 4 giao diện / điện thoại.
- Dashboard 8765 vẫn chạy mã cũ: cần khởi động lại một lần để có API mới (thẻ sẽ báo "máy chủ còn chạy bản cũ" cho đến lúc đó).
- Vai trò được sửa file ghi là `quyền: theo việc` (bin/ask hiểu đúng: chỉ `đọc` mới khoá).
- Mọi thay đổi từ commit 401c5d5 vẫn **chưa commit**.
