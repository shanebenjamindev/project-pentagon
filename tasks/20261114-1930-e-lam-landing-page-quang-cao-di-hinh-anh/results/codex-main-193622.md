<!-- worker: codex-main (codex) | 2026-11-14 19:36:22 | 201s | quyền: sửa | thư mục: /Users/macbookair/Documents/PERSONAL/Pentagon/.claude/worktrees/pentagon-task-tracking-861c0a/tasks/20261114-1930-e-lam-landing-page-quang-cao-di-hinh-anh/site | model: gpt-6-luna@medium · cỡ vua -->
## Việc được giao

Nhiệm vụ: tạo bộ ẢNH MINH HOẠ tự tạo (không dùng ảnh stock, không tải gì từ mạng) cho landing page quảng cáo sản phẩm 'Pentagon'. Chỉ ghi file vào thư mục img/ trong thư mục hiện tại.

Pentagon là gì: một hệ thống chạy trên máy cá nhân, khẩu hiệu '1 người giao việc, 1 AI quản lý, nhiều AI làm'. Người dùng giao task bằng tiếng Việt cho một AI quản lý (Claude Code); quản lý tối ưu yêu cầu, chia việc, giao cho nhiều AI worker (claude, codex, gemini, mỗi công cụ có thể nhiều tài khoản, hết hạn mức thì tự chuyển tài khoản và làm tiếp phần dở), kiểm tra rồi tổng hợp. Dùng gói thuê bao sẵn có qua CLI chính chủ, không cần API key. Có web dashboard theo dõi tiến độ 6 bước.

Bảng màu (bắt buộc dùng cho thống nhất): tím quản lý #8a4fd1 (sáng hơn #b98aff), xanh worker/nút chính #3b6fd8 (sáng hơn #6f9bff), xanh lá xong #1f9d55, xanh ngọc đang chạy #0e8fa6, nền tối #121417 / #1a1d21, nền sáng #f6f7f9. Logo có sẵn: img/mark.png (ngũ giác, 160x138, nền trong suốt) — đừng sửa nó.

Cách tạo ảnh: nếu bạn có công cụ tạo ảnh tích hợp (image generation) thì có thể dùng để tạo ảnh PNG/WebP; nếu không, VẼ BẰNG SVG thủ công (vector, phong cách minh hoạ phẳng/isometric hiện đại, gradient nhẹ, có chiều sâu, chi tiết vừa đủ, KHÔNG chứa chữ dài — chỉ nhãn ngắn nếu cần, không dùng font ngoài: font-family system-ui,sans-serif). Mỗi SVG có viewBox, không width/height cố định, nhẹ (< 40KB), không script, nhìn tốt cả trên nền sáng lẫn nền tối (có nền riêng hoặc thiết kế trung tính).

Danh sách file cần tạo (tên cố định, phần mở rộng .svg hoặc .png/.webp tuỳ cách tạo):
1. img/hero.svg (tỉ lệ ~4:3): hình ngũ giác/trung tâm phát sáng màu tím tượng trưng AI quản lý ở giữa, nối bằng các đường dữ liệu tới 3-5 'worker' (khối/robot nhỏ màu xanh) đang làm việc (cửa sổ code, tài liệu, ảnh), có biểu tượng người dùng gửi một task vào quản lý.
2. img/feature-rotate.svg (~4:3): xoay vòng tài khoản — vài 'pin/thẻ tài khoản' xếp hàng, một cái cạn năng lượng chuyển tiếp sang cái kế tiếp bằng mũi tên vòng, công việc tiếp tục liền mạch.
3. img/feature-size.svg (~4:3): chọn model theo cỡ việc — ba khối nhỏ/vừa/lớn (như bánh răng hoặc chip) với nhãn 'nhỏ', 'vừa', 'lớn'.
4. img/feature-safe.svg (~4:3): an toàn mặc định — thư mục có khiên/khoá; worker chỉ đọc, chỉ được sửa trong 1 thư mục được cấp phép.
5. img/feature-dashboard.svg (~4:3): mockup trừu tượng web dashboard: danh sách thẻ task với thanh tiến độ 6 bước, chấm trạng thái xanh ngọc 'đang chạy' và xanh lá 'xong' (không chữ dài, chỉ thanh xám thay chữ).
6. img/og.png 1200x630: ảnh chia sẻ mạng xã hội — dùng lại bố cục hero thu gọn + chữ 'Pentagon' và '1 người giao việc, 1 AI quản lý, nhiều AI làm' trên nền tối. Hãy tạo bản og.svg trước rồi chuyển sang PNG bằng công cụ có sẵn trên macOS (vd: qlmanage -t -s 1200 -o . og.svg rồi đổi tên/crop bằng sips, hoặc python3 nếu có thư viện); nếu không chuyển được thì để lại og.svg và báo rõ.
7. img/favicon.svg: biểu tượng ngũ giác đơn giản màu tím-xanh (vuông).

Kiểm tra trước khi xong: mỗi SVG là XML hợp lệ (vd: python3 -c 'import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])' file.svg, hoặc xmllint --noout), kích thước file hợp lý. Trả lời ngắn: danh sách file + kích thước, cách đã tạo (công cụ tạo ảnh hay SVG thủ công), mô tả 1 câu mỗi ảnh, điểm cần lưu ý.

## Trả lời

Đã tạo minh hoạ bằng SVG thủ công, không dùng ảnh stock hay tải tài nguyên mạng. Tất cả SVG đều hợp lệ và dưới 40 KB; `img/mark.png` được giữ nguyên.

| File | Kích thước | Mô tả |
|---|---:|---|
| [hero.svg](img/hero.svg) | 4.5 KB | AI quản lý màu tím kết nối người giao việc với các worker và khung code, ảnh, tài liệu. |
| [feature-rotate.svg](img/feature-rotate.svg) | 3.4 KB | Các thẻ tài khoản nối thành vòng, minh hoạ công việc chuyển tiếp khi một tài khoản cạn năng lượng. |
| [feature-size.svg](img/feature-size.svg) | 2.9 KB | Ba chip kích cỡ nhỏ, vừa, lớn. |
| [feature-safe.svg](img/feature-safe.svg) | 2.8 KB | Thư mục được bảo vệ bằng khiên và khoá, cùng worker và dấu cho phép. |
| [feature-dashboard.svg](img/feature-dashboard.svg) | 4.3 KB | Dashboard trừu tượng với thẻ task, sáu bước và trạng thái đang chạy/hoàn tất. |
| [og.svg](img/og.svg) | 3.5 KB | Bố cục chia sẻ nền tối, có hero thu gọn, tên Pentagon và khẩu hiệu. |
| [og.png](img/og.png) | 78 KB · 1200×630 | Bản PNG xuất từ SVG bằng ImageMagick. |
| [favicon.svg](img/favicon.svg) | 1.3 KB | Biểu tượng ngũ giác tím-xanh. |

**Lưu ý:** PNG OG đã xuất đúng kích thước, nhưng ImageMagick trên máy thiếu hỗ trợ render chữ SVG; vì vậy phần chữ trong `og.png` không hiển thị đầy đủ. Chữ vẫn có trong `og.svg`.