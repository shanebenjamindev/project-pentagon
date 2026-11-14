<!-- worker: codex-main (codex) | 2026-11-14 19:37:08 | 25s | quyền: sửa | thư mục: /Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/tasks/20261114-1930-e-lam-landing-page-quang-cao-di-hinh-anh | model: gpt-6-luna@low · cỡ nho -->
## Việc được giao

Trong thư mục hiện tại có site/img/*.svg (ảnh minh hoạ landing page) và site/img/og.png bị lỗi: lần trước xuất bằng ImageMagick nên MẤT CHỮ, chỉ một phần ảnh nền tối, phần còn lại trắng (bố cục sai). Việc cần làm:
1. Xuất lại site/img/og.png đúng 1200x630, giống hệt site/img/og.svg (nền tối phủ kín, có chữ 'Pentagon' và khẩu hiệu tiếng Việt có dấu). Dùng trình render có hỗ trợ chữ, ví dụ: Google Chrome headless ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' --headless --disable-gpu --window-size=1200,630 --screenshot=out.png file:///.../og.svg hoặc một file html bọc svg với margin 0), hoặc qlmanage -t, hoặc rsvg-convert nếu có. Nếu og.svg tự nó có lỗi bố cục (không phủ kín 1200x630 viewBox) thì sửa og.svg trước.
2. Render xem trước mọi SVG trong site/img/ ra preview/<tên>.png (rộng ~800px) bằng cùng cách, để người kiểm tra xem được.
Chỉ sửa site/img/og.png, site/img/og.svg (nếu cần) và tạo preview/. Xong thì mở og.png kiểm tra kích thước (sips -g pixelWidth -g pixelHeight) và trả lời ngắn: đã dùng công cụ nào, kết quả.

## Trả lời

Chrome headless đã render được `site/img/og.png` ở kích thước **1200×630**.

Lệnh render preview trước đó không tạo file trong `preview/`, nên hiện chưa có các PNG preview. `og.svg` vẫn giữ nguyên vì đã có nền phủ kín và chữ cần thiết.