# Gemini CLI: tài khoản miễn phí bị chặn dù đã có gói AI Pro

## Yêu cầu gốc (nguyên văn)

Không dùng được — Google chặn: tài khoản gói miễn phí không còn dùng được Gemini CLI
 trong khi gói tôi là ai pro

## Yêu cầu đã tối ưu
- Mục tiêu: hiểu vì sao Gemini CLI báo lỗi (UNSUPPORTED_CLIENT / gói miễn phí không được hỗ trợ) khi tài khoản đăng nhập đang là gói miễn phí, trong khi người dùng đã có Google AI Pro; và tìm cách làm cho Gemini CLI dùng được gói AI Pro.
- Đầu ra mong muốn: báo cáo tiếng Việt ngắn gồm (1) nguyên nhân có khả năng nhất, (2) các bước xử lý cụ thể (đăng nhập lại bằng tài khoản nào, kiểm tra gói, biến môi trường/project nếu cần), (3) nguồn tham khảo, (4) điều chưa chắc chắn.
- Ràng buộc: chỉ nghiên cứu và hướng dẫn, KHÔNG sửa code trong repo. Không đưa thông tin đăng nhập/email của chủ vào prompt gửi worker.
- Tiêu chí xong: có nguyên nhân + các bước xử lý, mỗi ý ghi nguồn; có một bước kiểm tra chéo.
- Giả định: "gói tôi là ai pro" nghĩa là Google AI Pro. Tài khoản bị lỗi là tài khoản `gemini-main` (default) đang đăng nhập sẵn trên máy, như ghi trong config/workers.conf. Chủ muốn dùng lại Gemini CLI qua tài khoản AI Pro.
