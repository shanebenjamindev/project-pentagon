<!-- worker: codex-main (codex) | 2026-11-15 00:50:26 | 185s | quyền: sửa | thư mục: /Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a | model: gpt-6-luna@medium · cỡ vua | vai trò: code | phiên: 01a1db2b-c7f4-7662-bb89-27e801bb7982 | hỏi tiếp:  -->
## Việc được giao

Repo Pentagon (Python stdlib server bin/pt_web.py + bin/pt_manager.py, frontend 1 file web/index.html, không framework). Cài tính năng: cho phép DÁN ẢNH (Ctrl/Cmd+V), kéo-thả, hoặc chọn ảnh (nút 📎) vào ô giao task (#newText, gửi qua POST /api/giao, xem quanh dòng 1563 index.html) và ô chat quản lý (#msg, gửi qua POST /api/send, quanh dòng 970).

Yêu cầu:
1. Frontend: bắt paste/drop ảnh trên 2 textarea; hiện hàng thumbnail xem trước, mỗi ảnh có nút x xoá; nút 📎 mở input file accept=image/*. Khi gửi, thêm vào body JSON trường images: [{name, data}] với data là dataURL base64. Gửi xong thì xoá danh sách ảnh. Cho phép gửi khi chỉ có ảnh mà text rỗng (nếu backend hiện chặn text rỗng thì dùng text mặc định 'Xem ảnh đính kèm'). Giới hạn client: tối đa 8 ảnh, mỗi ảnh ≤ 5MB, báo toast nếu vượt. Style dùng biến CSS sẵn có (var(--line), var(--panel)...) để hợp các theme.
2. Backend pt_web.py do_POST: hiện giới hạn body 200000 byte — nâng lên ~30MB CHỈ cho /api/giao và /api/send, các path khác giữ 200KB (xác định path trước khi đọc body). Viết hàm lưu ảnh: kiểm tra dataURL có mime image/png|jpeg|gif|webp, decode base64 (validate=True), kiểm tra magic bytes khớp loại, ≤ 5MB/ảnh, ≤ 8 ảnh; tên file do server sinh (vd img-YYYYmmdd-HHMMSS-N.png), lưu vào <thư mục task>/attachments/. Ảnh sai thì trả lỗi 400 tiếng Việt.
   - /api/send: lưu ảnh vào attachments của task đó, rồi nối vào cuối message một đoạn: '\n\nẢnh đính kèm (dùng công cụ Read để xem):\n- <đường dẫn tuyệt đối>' trước khi gọi pt_manager.send.
   - /api/giao: task chưa tồn tại lúc nhận request. Cách làm: giải mã/validate ảnh trước, rồi sửa pt_manager.new_task/launch_new nhận thêm tham số tuỳ chọn images (list (tên_file, bytes)) — sau khi tạo thư mục task và TRƯỚC khi khởi động quản lý, ghi ảnh vào attachments/ và nối đoạn đường dẫn ảnh vào yêu cầu (để brief.md và prompt gửi quản lý đều có). Đọc kỹ new_task (dòng ~1213) và launch_new (~1239) để làm đúng thứ tự.
3. Trang task: đảm bảo ảnh trong attachments/ xem được. Kiểm tra /api/files và /api/file (pt_web.py ~493, ~525) và renderProducts trong index.html; nếu file ảnh hiện không hiển thị được thì thêm endpoint GET an toàn (vd /api/raw?id=&path=, chỉ cho phép file trong thư mục task, chống path traversal bằng realpath, chỉ phục vụ đuôi ảnh với Content-Type đúng, cùng kiểm tra đăng nhập như các GET /api khác) và hiển thị <img> cho ảnh. Trong lịch sử chat nếu tin nhắn có đường dẫn attachments thì hiện thumbnail là điểm cộng, không bắt buộc.
4. Không thêm thư viện ngoài. Không phá luồng cũ khi không có ảnh. Giữ các kiểm tra bảo mật hiện có (X-Pentagon, Origin, đăng nhập).
5. Chạy python3 -m py_compile bin/pt_web.py bin/pt_manager.py. Viết một test nhanh (script tạm, xoá sau) gọi hàm lưu/validate ảnh với PNG hợp lệ, dataURL sai mime, base64 hỏng.
Không commit git. Cuối cùng báo: file đã sửa, tóm tắt thay đổi, cách đã kiểm tra, điều gì chưa chắc chắn.

## Trả lời

## Kết quả

- Đã thêm chọn ảnh, dán ảnh, kéo-thả, xem trước và xoá ảnh trong ô giao task và ô chat. Có giới hạn 8 ảnh, 5 MB mỗi ảnh và thông báo khi vượt giới hạn.
- Backend kiểm tra MIME, base64 và magic bytes; lưu ảnh vào `attachments/`. Ảnh giao task được đưa vào brief và prompt; ảnh chat được đính kèm vào nội dung gửi quản lý.
- Ảnh trong `attachments/` hiển thị qua luồng `/files` hiện có, vốn đã kiểm tra đăng nhập và giới hạn đường dẫn. Nâng giới hạn body lên 30 MB riêng cho `/api/giao` và `/api/send`; các path khác giữ 200 KB.
- Đã chạy `python3 -m py_compile bin/pt_web.py bin/pt_manager.py` và smoke test hàm validate với PNG hợp lệ, sai MIME và base64 hỏng: đều đạt.

**File đã sửa:** [bin/pt_web.py](/Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/bin/pt_web.py), [bin/pt_manager.py](/Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/bin/pt_manager.py), [web/index.html](/Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/web/index.html).

**Chưa kiểm tra:** Chưa chạy thử trực tiếp trên trình duyệt. Body tối đa 30 MB có thể từ chối tổ hợp ảnh tổng lớn dù từng ảnh vẫn dưới 5 MB.