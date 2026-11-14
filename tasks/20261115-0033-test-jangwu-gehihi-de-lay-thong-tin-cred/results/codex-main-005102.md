<!-- worker: codex-main (codex) | 2026-11-15 00:51:02 | 360s | quyền: sửa | thư mục: /Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a | model: gpt-6-luna@high · cỡ lon | vai trò: code | phiên: 01a1db29-a7f0-71d3-95fa-964b14b518c7 | hỏi tiếp:  -->
## Việc được giao

Dự án Pentagon (thư mục hiện tại). Bạn vừa thêm tính năng hàng chờ tin nhắn chat (inbox.jsonl) trong bin/pt_manager.py, bin/pt_web.py, web/index.html. Reviewer phát hiện lỗi; hãy sửa TẤT CẢ các mục sau, giữ nguyên các phần đã đúng:
1. (a) send(): sau khi đặt pending='Đang chuẩn bị lượt mới…', mọi exception trước khi start_reserved/work chạy làm pending kẹt mãi (mọi tin sau bị xếp hàng vĩnh viễn). Bọc toàn bộ phần chuẩn bị bằng try/except BaseException: put(tid,'pending',None) rồi raise; nhánh luồng nền: xoá pending nếu Thread.start() lỗi. Thêm phòng hờ: check_queue coi pending 'chuẩn bị lượt' quá 5 phút (không có queued.txt, không có tiến trình chạy) là hết hạn và xoá (ghi timestamp vào pending hoặc dùng mtime file).
2. (b) Sau Dừng: inbox.paused làm tin mới cũng bị xếp hàng đến khi chủ xoá (mất tin). Sửa: trong send(), điều kiện xếp hàng chỉ còn quản lý đang chạy / pending. Nếu không chạy mà inbox còn tin (paused hoặc drain thất bại trước đó): xoá inbox.paused, claim inbox cũ, GỘP tin cũ + tin mới (tin mới cuối cùng, giữ thứ tự) bằng merged_inbox_prompt và chạy ngay một lượt. Tách hàm dùng chung với drain_inbox. Thêm nút 'Chạy hàng chờ' trên UI khi đang dừng mà còn tin (endpoint mới, gọi drain có bỏ paused). Hint UI: khi paused hiện rõ 'Đã Dừng — hàng chờ chưa chạy'.
3. retry_at (đang chờ hạn mức): send() KHÔNG xếp hàng nữa mà chạy ngay như hành vi cũ (gộp inbox cũ nếu có), như trước khi có tính năng.
4. cancel_task: phải dọn inbox (gọi clear_inbox hoặc tương đương) để check_queue không tự chạy lại task vừa huỷ.
5. drain_inbox: chỉ xoá file claim SAU KHI start_turn thành công; mọi lỗi (apply_inbox_options, resume_prompt, start_turn...) đều trả tin về inbox.jsonl (os.replace claim về lại nếu inbox chưa có, hoặc append). Làm tương tự trong check_retries.
6. check_queue: bọc drain_inbox(tid) từng task trong try/except Exception (ghi append_event, nhưng giới hạn tần suất ghi lỗi, vd tối đa 1 lần/5 phút/task) để lỗi một task không làm hỏng vòng lặp nền. Chỉ lấy khoá khi có inbox.jsonl hoặc inbox.claimed.* (kiểm tra exists trước), tránh makedirs/khóa mỗi 10s cho mọi task. Đoạn queued.txt trong check_queue gọi start_turn(_locked=True) mà không giữ inbox_lock: bọc bằng inbox_lock.
7. drain_inbox: nếu status task đang 'cho' thì gọi progress(tid,'tiep','chủ đã gửi thêm tin') như send(); ghi pentagon_event 'Quản lý nhận N tin từ hàng chờ.'
8. Tin xếp hàng có size='auto': khi gộp, nếu không tin nào chỉ định model/size thì giữ model hiện tại (ghi chú comment là chủ ý).
Sau khi sửa: python3 -m py_compile bin/pt_manager.py bin/pt_web.py bin/tracker.py; chạy lại/cập nhật smoke test (thư mục tạm, ORCH_DATA tạm, giả lập start_turn, không gọi AI thật) phủ các trường hợp trên: pending không kẹt khi lỗi; send sau Dừng gộp tin cũ+mới và chạy; send khi retry_at chạy ngay; cancel dọn inbox; drain lỗi không mất tin. KHÔNG sửa tasks/ và config/, KHÔNG commit. Báo cáo ngắn: đã sửa gì (file:hàm), kết quả test.

## Trả lời

## Kết quả

Đã sửa luồng inbox trong [pt_manager.py](/Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/bin/pt_manager.py): giải phóng `pending` khi chuẩn bị hoặc chạy luồng nền lỗi; tự xoá reservation chuẩn bị quá hạn; gộp tin cũ và tin mới để chạy ngay sau Dừng hoặc khi đang `retry_at`; giữ claim và hoàn trả tin nếu drain/retry lỗi; dọn inbox khi huỷ task; thêm log lỗi drain có giới hạn tần suất và khóa đúng khi xử lý `queued.txt`.

Trong [pt_web.py](/Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/bin/pt_web.py) và [index.html](/Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/web/index.html), đã thêm endpoint và nút **Chạy hàng chờ**, cùng hint **Đã Dừng — hàng chờ chưa chạy**. Cỡ `auto` giữ nguyên model hiện tại nếu không có lựa chọn rõ ràng.

Đã thêm [test_inbox_smoke.py](/Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/tests/test_inbox_smoke.py), dùng dữ liệu tạm và giả lập khởi chạy, không gọi AI thật.

- `py_compile` cho `pt_manager.py`, `pt_web.py`, `tracker.py`: đạt.
- Smoke test: **6/6 đạt**, gồm pending lỗi, lỗi `Thread.start()`, gửi sau Dừng, gửi khi retry, huỷ dọn inbox và drain lỗi hoàn trả tin.
- `git diff --check`: đạt.
- Không sửa `tasks/` hoặc `config/`; không commit.