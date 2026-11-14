# Kế hoạch

| # | Việc con | Worker | Đầu vào | Đầu ra | Trạng thái |
|---|----------|--------|---------|--------|------------|
| 1 | Ping claude-3, đọc hạn mức | claude-3 (-s nho) | prompt ngắn | results/credit-va-model.md | xong |
| 2 | Ping gehihi + dò model Gemini | quản lý tự chạy bin/ask gehihi -m ... | model mặc định, gemini-2.5-flash | results/credit-va-model.md | xong (bị Google chặn) |
| 3 | Xếp hàng tin nhắn chat trên web | codex (-r code, -s lon), sửa 2 lần theo review | pt_web.py, pt_manager.py, index.html | code + tests/test_inbox_smoke.py | xong |
| 4 | Review việc 3 | claude-3 (-r review, -s vua), 2 vòng | diff so với baseline/ | results/claude-3-004443.md, claude-3-005259.md | xong |
