# Kế hoạch

| # | Việc con | Worker | Song song? | Trạng thái |
|---|----------|--------|------------|------------|
| 1 | Viết `code/prime.py` + `code/test_prime.py` (3 test), chạy pytest | codex (codex-main), quyền `-w` trong `code/` | Không — làm trước | xong (pytest chưa chạy được: máy chưa cài pytest) |
| 2 | Review code từ việc 1 (đúng đắn, biên, hiệu năng, chất lượng test) | claude (claude-main), chỉ đọc | Không — sau việc 1 | xong — ĐẠT |
| 3 | Quản lý kiểm tra: đối chiếu review, sửa nếu cần | quản lý | — | xong (đã sửa theo review; pytest chưa chạy thật) |

Lý do chọn: codex mạnh viết code + chạy test; claude mạnh review → đảm bảo "AI khác" review.

Ghi chú: quản lý không được phép cài pytest/chạy python trong phiên này → kiểm tra test data bằng tay (7917=3×2639, 1000001=101×9901, 7919 và 1000003 là số nguyên tố).
