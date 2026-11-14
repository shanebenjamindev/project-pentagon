# Kế hoạch

| # | Việc con | Worker | Song song? | Trạng thái |
|---|----------|--------|------------|------------|
| 1 | Sửa CSS/HTML cho đều: lề trang, 2 cột, cỡ điều khiển, font, khung chat, tab, nhịp dọc (web/index.html + theme-*.css) | claude (-r code, -s lon) | không | xong (claude-main, 455s; theme Quân sự đã bị task khác xoá nên chỉ sửa 2 theme) |
| 2 | Review chéo bản sửa (chỉ đọc) | codex (-r review, -s vua) | không | xong (mark-1: ĐẠT, không lỗi nghiêm trọng) |
| 3 | Sửa theo review (nếu có) | claude (-r code, -s vua) | không | xong (bỏ qua — review không có lỗi cần sửa) |
