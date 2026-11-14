# Kế hoạch

| # | Việc con | Worker | Song song? | Trạng thái |
|---|----------|--------|------------|------------|
| 1 | Sửa 4 lỗi UI (toast góc phải, thông báo kết nối + phát hiện code cũ, nén ảnh + lỗi 413, đồng đều giao diện) | claude (-r code, -s lon) | không | xong (claude-3) |
| 2 | Review chéo phần sửa | codex (-r review, -s vua) | không | xong (mark-1, 1 lỗi nhỏ, quản lý tự sửa) |
| 3 | Chạy py_compile + test + node --check | codex (-r code, -s nho) | không | xong — tất cả đạt |
