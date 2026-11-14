# Làm tiếp phiên "Pentagon task tracking display"

## Yêu cầu gốc (nguyên văn)

tiếp tục công việc đang dở trong Phapsubenjamin claude

(lượt 2) task tên Pentagon task tracking display ở claude benjamin ấy

## Yêu cầu đã tối ưu
- Bối cảnh: phiên Claude Code "Pentagon task tracking display" (session dac182a8, worktree `pentagon-task-tracking-861c0a`,
  nhánh `claude/pentagon-task-tracking-861c0a`) bị đứt lúc ~21:25 ngày 14/11 vì hết hạn mức 5 giờ. Còn dở:
  1. Chủ đã "ok": đưa 3 phần cấu hình còn sửa bằng file lên trang **Cài đặt** (`/cai-dat`):
     quyền AI quản lý (`config/manager.conf`: model + allow), bảng model theo cỡ (`config/models.conf`),
     vai trò subagent (`config/roles/*.md`). Kế hoạch 4 bước cũ: đọc/ghi cấu hình → API có kiểm tra dữ liệu →
     3 thẻ trong Cài đặt → chạy thử trên bản sao cấu hình + giao diện. Mới làm bước đọc file.
  2. Lỗi chủ báo kèm ảnh: "khi ấn để xem thì mất" — Phòng Điều hành, ô tìm task bị điền sẵn "pentagon" nên mất hết task.
  3. Toàn bộ thay đổi từ commit 401c5d5 chưa commit.
- Đầu ra: tính năng 1 chạy được trên web; lỗi 2 được sửa; báo cáo; (commit chỉ khi chủ bảo).
- Ràng buộc: nguyên tắc "mọi thứ làm trên giao diện"; không khởi động lại dashboard đang chạy (quản lý đang chạy trong đó);
  thử trên cổng khác với bản sao cấu hình.
- Tiêu chí xong: đọc/sửa/lưu được 3 phần cấu hình trên trang Cài đặt, dữ liệu sai bị chặn, file cấu hình ghi đúng định dạng
  mà bin/ask, bin/pt_manager.py đang đọc; lỗi ô tìm kiếm hết.
- Giả định: không commit khi chủ chưa yêu cầu.
