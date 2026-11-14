<!-- worker: codex-main (codex) | 2026-11-15 00:53:31 | 96s | quyền: sửa | thư mục: /Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a | model: gpt-6-luna@medium · cỡ vua | vai trò: code | phiên: 01a1db2f-f546-7e72-bdaf-63f314f875be | hỏi tiếp:  -->
## Việc được giao

Bạn vừa cài tính năng đính kèm ảnh (paste/drop/📎) cho /api/giao và /api/send trong bin/pt_web.py, bin/pt_manager.py, web/index.html. Review đã chỉ ra các lỗi sau, hãy sửa hết (đọc review đầy đủ ở tasks/20261115-0046-cho-phep-paste-anh-vao-khi-giao-task-hoa/results/claude-3-005142.md):
NGHIÊM TRỌNG:
1. Giới hạn body 30MB mâu thuẫn 8×5MB base64 (~53MB): nâng giới hạn cho 2 endpoint lên ~56MB, thêm cap tổng ảnh gốc 40MB ở backend; frontend kiểm tra tổng ≤ 40MB và báo toast.
2. /api/send gọi save_images trước khi kiểm tra id: phải kiểm tra isinstance(tid,str) và tid thuộc task_ids() TRƯỚC khi decode/lưu ảnh (404 nếu sai); trong save_images thêm kiểm tra realpath nằm trong realpath(TASKS)+os.sep.
NÊN SỬA:
3. Tên file thêm hậu tố ngẫu nhiên secrets.token_hex(3) và mở file bằng mode 'xb'.
4. Kiểm tra đăng nhập TRƯỚC khi đọc body lớn: với request chưa đăng nhập (khi có mật khẩu) giữ giới hạn 200KB; chỉ cho body lớn sau khi xác thực. Không phá luồng /api/login. Trong decode_images kiểm tra độ dài chuỗi base64 (> ~7MB thì từ chối) trước khi b64decode.
5. Nếu pt_manager.send ném lỗi sau khi đã lưu ảnh thì xoá các file vừa lưu.
6. Frontend chỉ nhận image/png, image/jpeg, image/gif, image/webp; ảnh khác báo toast và bỏ qua.
7. Khi paste mà clipboard có cả text, không preventDefault (để text vẫn dán), chỉ thêm ảnh.
NHỎ: body.get('images') or []; gom logic ghi ảnh vào một hàm chung trong pt_manager (pt_web chỉ gọi); trong new_task kiểm tra assignee trước khi tạo thư mục/ghi ảnh.
Sau đó chạy python3 -m py_compile bin/pt_web.py bin/pt_manager.py và smoke test nhanh (script tạm, xoá sau) cho: PNG hợp lệ, sai mime, base64 hỏng, tid '../x' bị từ chối. Không commit git. Báo lại ngắn gọn từng mục đã sửa thế nào.

## Trả lời

Đã sửa các mục được giao:

- Nâng giới hạn body `/api/giao` và `/api/send` lên 56 MiB, giới hạn tổng ảnh gốc ở backend và frontend ở 40 MiB. Frontend báo toast khi vượt mức.
- Với mật khẩu đang bật, request chưa đăng nhập bị giới hạn 200 KB trước khi đọc body lớn; `/api/login` vẫn dùng giới hạn này.
- Giới hạn chuỗi base64 trước khi giải mã; `/api/send` xác thực `id` là chuỗi thuộc `task_ids()` trước khi xử lý ảnh. Hàm ghi ảnh kiểm tra `realpath` nằm trong thư mục tasks.
- Tên ảnh có hậu tố ngẫu nhiên và file được tạo bằng chế độ `xb`. Ghi ảnh được gom vào `pt_manager`; nếu `send` lỗi thì xoá ảnh vừa ghi.
- `new_task` kiểm tra assignee trước khi tạo task. Backend dùng `body.get("images") or []`.
- Frontend chỉ nhận PNG, JPEG, GIF, WebP; paste ảnh không chặn thao tác dán văn bản.

Đã chạy `python3 -m py_compile bin/pt_web.py bin/pt_manager.py` và smoke test tạm: PNG hợp lệ được nhận; MIME sai, base64 hỏng và `tid="../x"` bị từ chối. Không commit.

**Các file đã sửa:** [bin/pt_web.py](/Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/bin/pt_web.py), [bin/pt_manager.py](/Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/bin/pt_manager.py), [web/index.html](/Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/web/index.html)

## Kết quả

Đã hoàn tất các sửa đổi và kiểm tra được yêu cầu.