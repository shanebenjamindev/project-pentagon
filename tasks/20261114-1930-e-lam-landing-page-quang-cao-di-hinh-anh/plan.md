# Kế hoạch

| # | Việc con | Worker | Song song? | Trạng thái |
|---|----------|--------|------------|------------|
| 1 | Tạo bộ ảnh minh hoạ (hero, 4 ảnh tính năng, og, favicon) vào `site/img/` — SVG vẽ tay | codex (-s vua) | không | xong (7 SVG hợp lệ, mỗi file < 5KB) |
| 2 | Viết copy quảng cáo + dựng `site/index.html` dùng các ảnh ở bước 1 | claude (-s lon), làm tiếp bằng claude-main (-s vua) | không | xong (782 dòng, 50KB; lần 1 bị dừng giữa chừng nhưng file đã hoàn chỉnh) |
| 3 | Xuất lại `og.png` có chữ + chụp preview 375px/1280px | codex (-s nho) ×2, claude-main (-s vua) | không | lỗi — môi trường nền không chạy được Chrome/qlmanage/sips; chủ chạy tay (xem final.md) |
| 4 | Kiểm tra nội dung, ảnh, responsive (đọc mã) | quản lý tự kiểm | không | xong |
| 5 | Thêm hiệu ứng chuyển động (hiện dần khi cuộn, hero, ảnh SVG động, hover) — chủ yêu cầu thêm | claude-main (-s vua) → claude-2 (claude-main hết hạn mức) | không | xong (index.html 56.8KB; hero/feature-rotate/feature-dashboard.svg có chuyển động) |
| 6 | Kiểm tra hiệu ứng (đọc mã: reduced-motion, không vỡ bố cục, không JS lỗi) | quản lý tự kiểm | không | xong (đọc mã, chưa xem trên trình duyệt) |

Đầu vào chung: README.md, `noi-dung-pentagon.txt` (chép từ task landing trước), `mark.png` (logo).
Đầu ra: `tasks/20261114-1930-e-lam-landing-page-quang-cao-di-hinh-anh/site/`.
