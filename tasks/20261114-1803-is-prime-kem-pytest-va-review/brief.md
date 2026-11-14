# is_prime kem pytest va review

## Yêu cầu gốc (nguyên văn)

Viết hàm Python is_prime(n) kèm 3 test pytest, rồi nhờ một AI khác review code đó. Task nhỏ, cứ làm luôn không cần chờ duyệt.

## Yêu cầu đã tối ưu
- Mục tiêu: Có một hàm `is_prime(n)` đúng, gọn, hiệu quả hợp lý; được kiểm thử bằng pytest và được một AI khác (khác AI viết code) review.
- Đầu ra mong muốn:
  - `code/prime.py` — hàm `is_prime(n: int) -> bool` (thuật toán chia thử đến √n, bỏ qua số chẵn), có docstring.
  - `code/test_prime.py` — đúng 3 test pytest: (1) các số nguyên tố nhỏ/lớn trả True, (2) hợp số (gồm bình phương số nguyên tố như 25, 49) trả False, (3) trường hợp biên n ≤ 1 (0, 1, số âm) trả False.
  - Báo cáo review từ một AI khác loại.
- Ràng buộc: chỉ dùng thư viện chuẩn Python; worker chỉ được sửa file trong thư mục `code/` của task.
- Tiêu chí xong: `pytest` chạy 3/3 pass; review không còn lỗi nghiêm trọng (hoặc lỗi đã được sửa).
- Giả định:
  - Chủ không chỉ định thư mục → code đặt trong `tasks/<task>/code/`.
  - Đầu vào không phải `int` (float, str, bool): hàm raise `TypeError` (bool cũng bị từ chối vì là trường hợp gây nhầm lẫn).
  - "3 test" = 3 hàm test (mỗi hàm có thể dùng `parametrize` cho nhiều giá trị).
