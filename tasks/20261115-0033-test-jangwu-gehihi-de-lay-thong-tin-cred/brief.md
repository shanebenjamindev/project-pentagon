# Test credit claude-3 (JiangWu) + gehihi; xếp hàng chat web

## Yêu cầu gốc (nguyên văn)

test jangwu, gehihi để lấy thông tin credit, riêng gemini có thể có dùng được bao nhiêu model hãy trả lời, trang pentagon này cũng nên cho nhận yêu cầu chat dồn dập mà không cần phải đợi quản lý, cho quản lý sắp xếp

## Yêu cầu đã tối ưu
- Mục tiêu:
  1. Chạy thử worker `claude-3` (tài khoản JiangWu) và `gehihi` (Gemini) để ghi nhận hạn mức/credit hiện tại (% đã dùng, giờ làm mới, gói).
  2. Với gehihi: dò xem tài khoản gọi được những model Gemini nào (gọi thử từng model, ghi model nào OK/lỗi).
  3. Web Pentagon: cho chủ gửi nhiều tin nhắn liên tiếp vào task khi quản lý đang chạy — tin nhắn được XẾP HÀNG, không bị chặn; quản lý xong lượt thì tự nhận các tin đang chờ (gộp lại) và sắp xếp xử lý.
- Đầu ra: bảng credit 2 tài khoản + danh sách model Gemini dùng được; code sửa trong bin/pt_web.py / bin/pt_manager.py / web/index.html.
- Ràng buộc: không lộ thông tin tài khoản ra ngoài; test bằng prompt ngắn để đỡ tốn hạn mức.
- Tiêu chí xong: có số liệu thực tế; gửi tin khi quản lý đang chạy không còn bị từ chối, tin được hiển thị "đang chờ" và được xử lý ở lượt sau.
- Giả định: "jangwu" = worker claude-3 (JiangWu). "credit" = hạn mức gói thuê bao (Claude/Gemini CLI không có số dư credit kiểu API).
