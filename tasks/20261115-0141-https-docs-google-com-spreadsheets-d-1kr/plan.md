# Kế hoạch — Video PPF Summer Breeze (1 bản)

| # | Việc con | Worker | Đầu vào | Đầu ra | Trạng thái |
|---|---|---|---|---|---|
| 1 | Tải voice, logo, video reference, footage PPF từ Drive; lập danh mục shot | codex (-r code, -s vua) | ppf_script.md | work/assets/ + work/assets.md | đang làm |
| 2 | Dựng video 9:16 60s bằng ffmpeg theo 8 cảnh: footage, text, logo, voice, nhạc | claude (-r code, -s lon) | assets + ppf_script.md | results/ppf_final.mp4 | chờ |
| 3 | Review video so với kịch bản | gemini (-r review, -s vua) | ppf_final.mp4 + ppf_script.md | results/review | chờ |
| 4 | Sửa theo review (nếu cần), viết final.md | claude / quản lý | review | final.md | chờ |
