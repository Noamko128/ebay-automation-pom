"""Unit tests for the price parser's edge cases (no browser needed)."""
import pytest

from core.price_parser import parse_price


@pytest.mark.parametrize(
    "text,expected",
    [
        ("$19.99", 19.99),
        ("US $19.99", 19.99),
        ("$1,299.00", 1299.00),
        ("$1500.00", 1500.00),
        ("$19.99 to $29.99", 19.99),
        ("$19.99/ea", 19.99),
        ("Free shipping", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_price(text, expected):
    assert parse_price(text) == expected
