"""Utilities for working with prime numbers."""

import math


def is_prime(n: int) -> bool:
    """Return whether ``n`` is a prime integer.

    Args:
        n: The integer to check. Booleans and non-integers are rejected.

    Returns:
        True if ``n`` is prime, otherwise False.

    Raises:
        TypeError: If ``n`` is not an integer or is a boolean.

    >>> is_prime(7)
    True
    >>> is_prime(9)
    False
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"n must be an integer (not bool), got {type(n).__name__}")

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
