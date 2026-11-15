# Kế hoạch

Đầu ra: blog tuyển "booking không giới hạn" cho DEN HAAG (để chạy ads), kèm caption ads và ảnh chọn từ thư mục DanHeeg.

| # | Việc con | Worker | Song song? | Trạng thái |
|---|----------|--------|------------|------------|
| 1 | Tra cứu: đọc trang marketing plan + liệt kê ảnh/video trong DanHeeg | codex mark-1 (-r code, -s nho) | không | xong (DanHeeg OK; trang web chỉ chạy bằng JS, không đọc được) |
| 1b | Thu nhỏ 41 ảnh + 6 khung hình video để chọn | codex (-r code, -s nho) | không | xong |
| 2 | Viết blog HTML + MD + caption ads, chọn 6 ảnh | claude-3 (-r viet, -s vua) | không | xong |
| 2b | Sửa tên thành DEN HAAG (theo biển hiệu), xuất ảnh chất lượng cao từ file gốc | codex (-r code, -s nho) | không | xong |
| 3 | Review số liệu, chính sách ads, HTML | codex (-r review, -s nho) | không | xong (quản lý đã tự sửa các lỗi nhỏ) |

## Vòng 2 — chủ góp ý: sai màu chủ đạo, nhiều lỗi, thiếu ảnh
Màu thương hiệu lấy từ HTML trang marketing plan: navy #031725, paper #f5f5f2, đỏ #b20c2b (hover #e03550), muted #bbc7cf, line #29404e, teal #07516c; font Barlow Condensed (tiêu đề) + Be Vietnam Pro (chữ).

| # | Việc con | Worker | Song song? | Trạng thái |
|---|----------|--------|------------|------------|
| 4 | Xuất toàn bộ ảnh gốc 1600px + nhiều khung hình video | codex (-r code, -s nho) | không | xong |
| 5 | Dựng lại blog theo màu/font thương hiệu + thông tin fanpage, 15 ảnh | claude-3 (-r code, -s lon) | không | xong |
| 6 | Retouch 15 ảnh (lần 2: brand grade mạnh hơn), hero mới từ biển hiệu, bỏ fallback | codex (-r code, -s vua) | không | xong (không chụp màn hình được vì sandbox chặn Chrome) |
