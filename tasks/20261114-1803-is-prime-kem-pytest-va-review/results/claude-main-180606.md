<!-- worker: claude-main (claude) | 2026-11-14 18:06:06 | 80s | quyền: đọc | thư mục: /Users/macbookair/Documents/PERSONAL/ai-orchestrator/tasks/20261114-1803-is-prime-kem-pytest-va-review/code -->
## Việc được giao

Review code trong thư mục làm việc hiện tại: prime.py (hàm is_prime(n)) và test_prime.py (3 test pytest). Do một AI khác viết.

Yêu cầu của hàm: trả False với n <= 1; chia thử đến isqrt(n), bỏ qua số chẵn; raise TypeError nếu n không phải int hoặc là bool. Test phải đúng 3 hàm test: số nguyên tố, hợp số (có bình phương số nguyên tố), trường hợp biên.

Hãy kiểm tra: (1) tính đúng đắn, kể cả biên (0, 1, 2, 3, 4, số âm, bình phương số nguyên tố, số lớn); (2) xử lý kiểu dữ liệu; (3) hiệu năng; (4) chất lượng và độ bao phủ của test — test có thực sự bắt được lỗi không, dữ liệu kỳ vọng có đúng không (tự xác minh 7919, 1_000_003 là số nguyên tố; 7917, 1_000_001 là hợp số); (5) style/docstring.
Phân loại mỗi nhận xét: NGHIÊM TRỌNG / NÊN SỬA / GÓP Ý. Với mỗi nhận xét, nêu dòng và đề xuất sửa cụ thể. Kết luận cuối: ĐẠT hoặc CHƯA ĐẠT.

## Trả lời

# Review `prime.py` và `test_prime.py`

**Lưu ý:** tôi không chạy được `pytest` hay script kiểm tra, vì lệnh Python cần quyền và không được duyệt trong phiên này. Mọi kết luận dưới đây đến từ việc đọc code, lần từng bước bằng tay và tự phân tích thừa số. Tôi không sửa file nào trong thư mục làm việc.

## 1. Tính đúng đắn của `is_prime`

Lần từng bước bằng tay cho từng trường hợp:

| Đầu vào | Đi qua | Kết quả |
|---|---|---|
| 0, 1, số âm | dòng 18 | False ✔ |
| 2, 3 | dòng 20 | True ✔ |
| 4 và mọi số chẵn > 2 | dòng 22 | False ✔ |
| 5, 7 | `isqrt` = 2, `range(3, 3, 2)` rỗng | True ✔ |
| 9, 25, 49, 121 (bình phương số nguyên tố) | `+ 1` ở dòng 25 giúp xét tới đúng `isqrt(n)` | False ✔ |
| Số lớn | `math.isqrt` tính chính xác với int tuỳ ý, không sai số như `int(n ** 0.5)` | ✔ |

Hàm đúng với mọi số nguyên. Hàm có chia thử đến `isqrt(n)` và bỏ qua số chẵn đúng như yêu cầu.

## 2. Tự xác minh dữ liệu kỳ vọng trong test

- **7919** là số nguyên tố, cũng là số nguyên tố thứ 1000. `isqrt` = 88, không có ước lẻ nào từ 3 đến 87. ✔
- **1_000_003** là số nguyên tố nhỏ nhất lớn hơn 10⁶. ✔
- **7917** = 3 × 7 × 13 × 29 = 3 × 2639 (tổng chữ số bằng 24, chia hết cho 3). Là hợp số ✔
- **1_000_001** = 101 × 9901. Là hợp số ✔. Hàm trả False vì 101 ≤ `isqrt` = 1000.
- Các giá trị còn lại (2, 3, 5, 7, 13, 97 / 4, 9, 15, 25, 49, 121) đều đúng.

Theo lần từng bước bằng tay, cả 3 test sẽ pass (chưa xác nhận bằng lần chạy thật).

## 3. Test có bắt được lỗi thật không

Tôi thử các lỗi giả định (mutation), lần bằng tay:

| Lỗi giả định | Test bắt bằng |
|---|---|
| Quên `+ 1`: `range(3, isqrt(n), 2)` | 9, 25 |
| Bắt đầu chia từ 5 | 9, 15 |
| Bỏ nhánh `n % 2 == 0` | 4 |
| Bỏ nhánh `n in (2, 3)` | 2 |
| `n < 1` thay cho `n <= 1` | 1 |
| Bỏ kiểm tra bool | `True` |
| Bỏ `not isinstance(n, int)` | 2.0 |

Bộ test diệt được tất cả lỗi trên. Test dùng `is True` / `is False` nên kiểm tra luôn kiểu trả về là `bool`, đây là điểm tốt.

## 4. Các nhận xét

**NGHIÊM TRỌNG:** không có.

**NÊN SỬA**

1. **`test_prime.py:22-28`: test biên dùng vòng `for` thay vì parametrize.** Nếu giá trị đầu tiên fail thì các giá trị sau không được chạy, và báo lỗi không nói rõ giá trị nào sai. Vẫn giữ đúng 3 hàm test bằng cách parametrize theo cặp (giá trị, kết quả hoặc ngoại lệ):
   ```python
   @pytest.mark.parametrize(
       "value, expected",
       [(0, False), (1, False), (-1, False), (-7, False),
        (2.0, TypeError), ("7", TypeError), (None, TypeError),
        (True, TypeError), (False, TypeError)],
   )
   def test_edge_cases(value, expected):
       if expected is TypeError:
           with pytest.raises(TypeError, match="integer"):
               is_prime(value)
       else:
           assert is_prime(value) is expected
   ```
2. **`test_prime.py:26`: thiếu `False` và `None`.** Mới test `True`, chưa test `False`. Giá trị `"7"` tự gây TypeError khi so sánh `"7" <= 1`, nên nó không chứng minh được hàm có kiểm tra kiểu. Thêm `False` và `None` như đoạn code ở mục 1.
3. **`test_prime.py:27`: `pytest.raises(TypeError)` không có `match=`.** Một TypeError phát sinh ngẫu nhiên (như trường hợp `"7"` ở trên) cũng làm test pass. Nên dùng `pytest.raises(TypeError, match="integer")`.

**GÓP Ý**

4. **`prime.py:7-14`:** docstring thiếu mục `Returns:`. Đề xuất thêm `Returns: True nếu n là số nguyên tố, ngược lại False.`, có thể kèm ví dụ doctest (`>>> is_prime(7)` → `True`).
5. **`prime.py:16`:** thông báo lỗi nên nêu kiểu thực nhận, ví dụ `f"n must be an int (not bool), got {type(n).__name__}"`.
6. **`prime.py:25`, hiệu năng:** độ phức tạp O(√n/2) là hợp lý theo yêu cầu. Với n khoảng 10¹² hàm chạy cỡ 5·10⁵ vòng, vẫn ổn. Với số nguyên tố cỡ 2⁶¹−1 thì sẽ mất nhiều phút. Có thể dùng bước 6k±1 để giảm thêm khoảng 1/3 số vòng, hoặc ghi giới hạn này vào docstring. Không bắt buộc vì spec chỉ yêu cầu bỏ qua số chẵn.
7. **`prime.py:15`:** `numpy.int64` sẽ bị từ chối vì không phải lớp con của `int`. Cách này đúng theo spec. Nếu muốn nhận cả loại này thì dùng `operator.index(n)`, nhưng như vậy là đổi spec, nên chỉ ghi nhận.
8. **`test_prime.py:8, 16`:** nên thêm một số lớn là tích hai số nguyên tố gần nhau (ví dụ `1_000_003 * 999_983`), hoặc bình phương số nguyên tố lớn như `7919**2 = 62_710_561`. Như vậy sẽ kiểm tra biên `isqrt` ở số lớn và vòng lặp không thoát sớm.
9. **`test_prime.py:1`:** thiếu docstring module. Tên biến chưa thống nhất: `number` (dòng 23) và `value` (dòng 26). Đề xuất thêm docstring và dùng chung một tên.

## Kết quả

- **Hàm `is_prime` đúng hoàn toàn:** xử lý đúng các trường hợp 0, 1, 2, 3, 4, số âm, bình phương số nguyên tố và số lớn. Đúng yêu cầu về kiểu (từ chối bool, float, str) và về thuật toán (chia đến `isqrt`, bỏ qua số chẵn).
- **Dữ liệu kỳ vọng đều đúng:** 7919 và 1_000_003 là số nguyên tố; 7917 = 3·7·13·29 và 1_000_001 = 101·9901 là hợp số.
- **Test:** có đúng 3 hàm như yêu cầu và bắt được mọi lỗi giả định tôi thử.
- **Phân loại nhận xét:** 0 NGHIÊM TRỌNG, 3 NÊN SỬA (đều ở `test_edge_cases`: nên parametrize, thêm `False`/`None`, thêm `match=` cho `pytest.raises`), 6 GÓP Ý về docstring, thông báo lỗi, hiệu năng với số rất lớn và dữ liệu test lớn.
- **Chưa xác nhận bằng lần chạy thật:** phiên này không có quyền chạy `pytest`.

**Kết luận: ĐẠT.** Các mục NÊN SỬA làm test chắc hơn nhưng không chặn việc chấp nhận code.
