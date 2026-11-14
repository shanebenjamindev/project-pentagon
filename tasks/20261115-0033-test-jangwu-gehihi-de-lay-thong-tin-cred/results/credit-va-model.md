# Kết quả test credit (quản lý tự chạy, 15/11/2026 ~00:34)

## claude-3 (JiangWu) — chạy được
- Ping haiku: OK (2s, 19.444 token, ~0,0039 USD quy đổi).
- Hạn mức 5 giờ: đã dùng 3% — làm mới 15/11 05:30.
- Hạn mức 7 ngày: đã dùng 19% — làm mới 20/11 01:00.
- Trạng thái: allowed. Overage (dùng quá hạn mức trả thêm): tắt ở cấp tổ chức.

## gehihi (Gemini) — KHÔNG chạy được
- Lỗi: Google chặn tài khoản gói miễn phí dùng Gemini CLI (UNSUPPORTED_CLIENT).
- Thử model mặc định và gemini-2.5-flash: cả 2 đều bị chặn; tài khoản dự phòng `gemini` cũng bị chặn y hệt.
- => Số model Gemini dùng được qua Pentagon hiện tại: 0. Chặn ở cấp tài khoản nên đổi model không giúp được.
- Cách mở lại: dùng tài khoản Google AI Pro/Ultra hoặc Google Workspace có Gemini Code Assist, rồi bin/login gehihi,
  sau đó test lại từng model.
