# Gemini CLI báo "gói miễn phí không được hỗ trợ" dù bạn có Google AI Pro

## Kết luận

- Nhiều khả năng đây **không phải lỗi đăng nhập nhầm tài khoản**. Theo kết quả tra cứu của worker `mark-1` (codex), từ **18/6/2026** luồng "Sign in with Google" của Gemini CLI không còn hỗ trợ Gemini Code Assist cá nhân, kể cả Google AI Pro và AI Ultra. Google hướng người dùng sang **Antigravity**.
- Vì vậy **đăng nhập lại bằng đúng tài khoản AI Pro có thể không khôi phục được quyền dùng Gemini CLI**.
- Không nên đặt `GOOGLE_CLOUD_PROJECT` cho tài khoản cá nhân để thử sửa lỗi này.

## Mức độ tin cậy

- Nguồn: worker `mark-1` (codex, có truy cập mạng). Kết quả đầy đủ: `results/mark-1-011704.md`.
- Các URL worker dẫn: `developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals`, `.../deprecations`, `github.com/google-gemini/gemini-cli/blob/main/docs/get-started/authentication.mdx`, `github.com/google-gemini/gemini-cli/issues/28229`, `ai.google.dev/gemini-api/docs/billing`.
- **Tôi chưa tự mở được các URL này** vì quyền WebSearch/WebFetch vẫn bị từ chối. Thông tin ngày 18/6/2026 cần được đối chiếu trực tiếp với trang deprecations trước khi tin tuyệt đối.
- Chưa có worker thứ hai kiểm chéo (bước 5). Lý do: các worker khác không có quyền web, nên không kiểm chứng được nguồn.

## Các cách xử lý

1. **Chuyển sang Antigravity** theo hướng dẫn của Google (nếu đúng như worker báo cáo).
2. **Dùng Gemini API key** từ AI Studio. Đây là cơ chế và quota riêng, tính theo billing của dự án Google Cloud/Gemini API, **không** dùng quyền lợi của AI Pro.
3. Nếu lỗi thực tế không phải `UNSUPPORTED_CLIENT` (ví dụ đòi `GOOGLE_CLOUD_PROJECT` hoặc báo lỗi giấy phép tổ chức), có thể đang dùng nhầm luồng xác thực hoặc tài khoản Workspace. Khi đó cần xem lại thông báo lỗi chính xác.

## Việc còn lại

- Trong `config/workers.conf`, dòng `gehihi` (gemini) đang bật nhưng đã bị chặn cùng lỗi. Nên tắt dòng này.
- Bạn cần đối chiếu thông báo lỗi chính xác đang hiện trên máy với mục 3 ở trên.
