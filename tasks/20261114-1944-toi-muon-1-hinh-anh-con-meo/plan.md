# Kế hoạch

| # | Việc con | Worker | Song song? | Trạng thái |
|---|----------|--------|------------|------------|
| 1 | Vẽ con mèo bằng SVG (1024x1024, flat, nền trắng) lưu `results/cat.svg`; nếu có công cụ convert thì xuất thêm `results/cat.png` | codex-main (-s vua) | Không | xong (file đầy đủ; worker bị dừng sau khi ghi xong, không giao lại) |
| 2 | Kiểm tra chéo: đọc `cat.svg`, xác nhận là con mèo, không lỗi cú pháp; ghi nhận xét ngắn | claude-main (-s nho) | Không (sau việc 1) | chờ |

Đầu vào: yêu cầu đã tối ưu trong brief.md.
Đầu ra: results/cat.svg (+ cat.png nếu convert được), results/review-*.md.
