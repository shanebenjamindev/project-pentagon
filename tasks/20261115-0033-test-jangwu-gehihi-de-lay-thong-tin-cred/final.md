# Kết quả

## 1. Credit claude-3 (JiangWu) — chạy tốt
- Khung 5 giờ: đã dùng 3% (làm mới 15/11 05:30). Khung 7 ngày: đã dùng 19% (làm mới 20/11 01:00).
- Trạng thái allowed; không dùng được phần trả thêm (overage), vì tổ chức đã tắt.

## 2. gehihi (Gemini) — không dùng được
- Google chặn: tài khoản gói miễn phí không còn được dùng Gemini CLI (UNSUPPORTED_CLIENT).
- Đã thử model mặc định và gemini-2.5-flash; tài khoản `gemini` cũng bị chặn y hệt.
- **Số model Gemini dùng được hiện tại: 0.** Lệnh chặn áp lên cả tài khoản nên đổi model không giúp được.
- Muốn dùng lại: cần tài khoản Google AI Pro/Ultra hoặc Workspace có Gemini Code Assist, rồi `bin/login gehihi` và test lại.
- Không lấy được số credit của Gemini: Gemini CLI không báo hạn mức, Pentagon chỉ đếm được số việc, thời gian chạy và số lỗi.

## 3. Web: gửi tin dồn dập, quản lý tự sắp xếp
- Khi quản lý đang chạy, ô chat vẫn gửi được. Tin hiện ngay trong chat, vào hàng chờ (`manager/inbox.jsonl`), có nhãn "N tin đang chờ" và nút xoá hàng chờ.
- Hết lượt, quản lý tự nhận hết các tin đang chờ trong một lượt mới, gộp theo thứ tự, với lời dặn "tự sắp xếp ưu tiên / gộp việc trùng".
- Khi chủ bấm Dừng, hàng chờ được giữ lại và không tự chạy. Chủ gửi tin mới hoặc bấm "Chạy hàng chờ" thì tin cũ và tin mới được gộp và chạy ngay.
- Có khoá chống chạy trùng hai lượt; tin không mất khi có lỗi; huỷ task thì hàng chờ được dọn; trạng thái "đang chuẩn bị" bị kẹt quá 10 phút thì tự gỡ.
- Code: bin/pt_manager.py, bin/pt_web.py, web/index.html; test: tests/test_inbox_smoke.py (10 test OK, theo codex).

## Ai làm gì
- Quản lý: chạy test credit và dò model.
- codex-main: code tính năng (1 lần làm, 2 lần sửa).
- claude-3: review 2 vòng.

## Chưa chắc chắn
- Quản lý chưa tự chạy được py_compile và test vì bị chặn quyền; kết quả "10 test OK" là do codex báo.
- Cần khởi động lại `bin/dashboard` để nạp code mới. Chưa thử trên trình duyệt thật.
- Chưa commit git. Bản gốc trước khi sửa lưu ở baseline/.
