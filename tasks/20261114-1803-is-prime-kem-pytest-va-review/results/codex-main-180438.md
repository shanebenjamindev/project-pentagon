<!-- worker: codex-main (codex) | 2026-11-14 18:04:38 | 33s | quyền: sửa | thư mục: /Users/macbookair/Documents/PERSONAL/ai-orchestrator/tasks/20261114-1803-is-prime-kem-pytest-va-review/code -->
## Việc được giao

Trong thư mục làm việc hiện tại, tạo 2 file Python (chỉ dùng thư viện chuẩn + pytest):

1. prime.py: hàm is_prime(n: int) -> bool, có docstring.
   - Trả False với n <= 1; True với 2, 3.
   - Thuật toán chia thử đến căn bậc hai nguyên của n (dùng math.isqrt), bỏ qua số chẵn (hoặc dùng bước 6k±1).
   - Nếu n không phải int, hoặc là bool, thì raise TypeError.
2. test_prime.py: ĐÚNG 3 hàm test pytest (được dùng pytest.mark.parametrize cho nhiều giá trị):
   - test_primes: các số nguyên tố, gồm 2, 3, 5, 7, 13, 97, 7919, 1_000_003 -> True.
   - test_composites: hợp số, gồm 4, 9, 15, 25, 49, 121, 7917, 1_000_001 -> False (lưu ý có bình phương số nguyên tố).
   - test_edge_cases: 0, 1, -1, -7 -> False; và 2.0, '7', True -> raise TypeError (dùng pytest.raises).

Sau đó chạy: python3 -m pytest -q trong thư mục này và dán nguyên output. Trả về nội dung đầy đủ cả 2 file trong câu trả lời.

## Trả lời

Đã tạo hai file. Lệnh `python3 -m pytest -q` được chạy trong thư mục làm việc nhưng không chạy được vì môi trường Python hiện tại chưa cài `pytest`. Đây là nguyên output:

```text
/opt/homebrew/opt/python@3.15/bin/python3.15: No module named pytest
```

### `prime.py`

```python
"""Utilities for working with prime numbers."""

import math


def is_prime(n: int) -> bool:
    """Return whether ``n`` is a prime integer.

    Args:
        n: The integer to check. Booleans and non-integers are rejected.

    Raises:
        TypeError: If ``n`` is not an integer or is a boolean.
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an integer (not bool)")

    if n <= 1:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False

    for divisor in range(3, math.isqrt(n) + 1, 2):
        if n % divisor == 0:
            return False
    return True
```

### `test_prime.py`

```python
import pytest

from prime import is_prime


@pytest.mark.parametrize(
    "number",
    [2, 3, 5, 7, 13, 97, 7919, 1_000_003],
)
def test_primes(number):
    assert is_prime(number) is True


@pytest.mark.parametrize(
    "number",
    [4, 9, 15, 25, 49, 121, 7917, 1_000_001],
)
def test_composites(number):
    assert is_prime(number) is False


def test_edge_cases():
    for number in (0, 1, -1, -7):
        assert is_prime(number) is False

    for value in (2.0, "7", True):
        with pytest.raises(TypeError):
            is_prime(value)
```

## Kết quả

Hai file đã được tạo. Chưa thể chạy bộ kiểm thử do `pytest` không có trong môi trường Python hiện tại.