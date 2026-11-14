"""Tests for prime.is_prime."""

import pytest

from prime import is_prime


@pytest.mark.parametrize(
    "value",
    [2, 3, 5, 7, 13, 97, 7919, 1_000_003],
)
def test_primes(value):
    assert is_prime(value) is True


@pytest.mark.parametrize(
    "value",
    # 62_710_561 = 7919**2: checks the isqrt boundary on a larger number
    [4, 9, 15, 25, 49, 121, 7917, 1_000_001, 62_710_561],
)
def test_composites(value):
    assert is_prime(value) is False


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, False),
        (1, False),
        (-1, False),
        (-7, False),
        (2.0, TypeError),
        ("7", TypeError),
        (None, TypeError),
        (True, TypeError),
        (False, TypeError),
    ],
)
def test_edge_cases(value, expected):
    if expected is TypeError:
        with pytest.raises(TypeError, match="must be an integer"):
            is_prime(value)
    else:
        assert is_prime(value) is expected
