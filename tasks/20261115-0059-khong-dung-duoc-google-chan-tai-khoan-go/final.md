# Gemini CLI báo "gói miễn phí không được hỗ trợ" dù bạn có Google AI Pro

**Trạng thái: CHƯA XONG.** Không tra cứu được nguồn chính thức, nên chưa có nguyên nhân đã được xác minh.

## Đã xác minh (từ máy này)

- `config/workers.conf`: tài khoản `gemini-main` (đăng nhập mặc định) đã bị tắt, ghi chú lỗi `UNSUPPORTED_CLIENT`: Google ngừng cho Gemini CLI dùng gói miễn phí.
- Tài khoản `gehihi` (công cụ gemini) cũng báo đúng lỗi "Google chặn: tài khoản gói miễn phí không còn dùng được Gemini CLI". Dòng `gehihi` trong `config/workers.conf` vẫn đang bật, dù ghi chú nói Gemini tắt. Đây là mâu thuẫn cần sửa.
- Worker Claude (`claude-3`, vai trò tra-cứu) không tìm được nguồn vì quyền WebSearch/WebFetch bị từ chối.
- Tôi cũng thử WebSearch và WebFetch trực tiếp: đều bị từ chối quyền, nên không lấy được tài liệu Google.

## Giả thuyết chưa kiểm chứng

- Nguyên nhân khả dĩ nhất: Gemini CLI đang đăng nhập bằng một tài khoản Google khác với tài khoản đã mua AI Pro (ví dụ tài khoản cá nhân miễn phí hoặc tài khoản Workspace).
- Cách thử (do bạn tự làm, tôi chưa làm): vào one.google.com để xem gói AI Pro gắn với email nào. Sau đó đăng nhập lại Gemini CLI bằng đúng email đó. Có thể cần xoá thông tin đăng nhập cũ trong `~/.gemini/` (ví dụ `oauth_creds.json`) rồi chạy lại.
- Chưa biết AI Pro có cần thêm `GOOGLE_CLOUD_PROJECT` hay không. Cần đối chiếu tài liệu chính thức của Gemini CLI.

## Việc cần chủ làm

1. Cấp quyền WebSearch và WebFetch cho phiên này, rồi tôi tra lại các nguồn chính thức (github.com/google-gemini/gemini-cli, support.google.com, ai.google.dev).
2. Hoặc tự kiểm tra email gắn với gói AI Pro tại one.google.com và báo lại.
3. Quyết định có sửa `config/workers.conf` (tắt dòng `gehihi` nếu vẫn bị chặn) không.
