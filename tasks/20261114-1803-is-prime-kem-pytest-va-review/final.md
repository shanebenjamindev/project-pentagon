# Kết quả: is_prime + 3 test pytest + review

## Sản phẩm
- `code/prime.py`: hàm `is_prime(n: int) -> bool`.
  - Chia thử đến `math.isqrt(n)` và bỏ qua số chẵn.
  - Raise `TypeError` nếu đầu vào không phải `int` hoặc là `bool`.
  - Docstring có mục Returns/Raises và ví dụ doctest.
- `code/test_prime.py`: 3 hàm test, mỗi hàm chạy nhiều giá trị bằng parametrize.
  - `test_primes`: 8 số nguyên tố.
  - `test_composites`: 9 hợp số, gồm cả bình phương số nguyên tố và 7919² = 62.710.561.
  - `test_edge_cases`: 0, 1, số âm; các đầu vào sai kiểu 2.0, "7", None, True, False phải raise TypeError (dùng `match=`).

## Ai làm gì
| Phần | Người làm |
|---|---|
| Viết code và test bản đầu | codex-main (`results/codex-main-180438.md`) |
| Review | claude-main (`results/claude-main-180606.md`). Kết luận ĐẠT: 0 nghiêm trọng, 3 nên sửa, 6 góp ý |
| Sửa 3 mục NÊN SỬA và các góp ý 4, 5, 8, 9 | Quản lý |

## Chưa chắc chắn
- **Chưa chạy thật pytest.** Máy chưa cài pytest, và phiên này không được duyệt quyền cài pytest hay chạy Python.
- Tính đúng của code và dữ liệu test đã được cả claude-main lẫn quản lý kiểm tra bằng tay:
  - 7917 = 3 × 2639 và 1.000.001 = 101 × 9901 là hợp số.
  - 7919 và 1.000.003 là số nguyên tố.
- Lệnh để tự xác nhận:
  `cd tasks/20261114-1803-is-prime-kem-pytest-va-review/code && pip install pytest && python3 -m pytest -q`
- Các góp ý không áp dụng, vì vượt ngoài spec:
  - Bước 6k±1 để tăng tốc.
  - Nhận thêm `numpy.int64`.
