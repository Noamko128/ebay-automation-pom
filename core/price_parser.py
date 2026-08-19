"""Robust parsing of eBay-style price strings.

Real listings render price text in several shapes: "$19.99", "US $1,299.00" (thousands
separator), "$19.99 to $29.99" (a variant price range), "$19.99/ea", or interleaved with
unrelated text like "Free shipping" / "or Best Offer". A naive `float(text.strip("$"))` breaks
on all but the simplest case, which is the kind of bug this exercise's ReadMeAIBugs.md calls
out - see that file for a concrete example.
"""
from __future__ import annotations

import re

_NUMBER_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d{1,2})?)")


def parse_price(text: str | None) -> float | None:
    """Extracts the lowest monetary amount in ``text``, or None if no number is present.

    For a range such as "$19.99 to $29.99" the lower bound is returned: the use case this
    parser serves (searchItemsByNameUnderPrice) treats a listing as matching a max-price filter
    if *some* purchasable configuration of it is at or under that price.
    """
    if not text:
        return None
    matches = _NUMBER_RE.findall(text)
    if not matches:
        return None
    return min(float(m.replace(",", "")) for m in matches)


def format_price(amount: float, currency_symbol: str = "$") -> str:
    return f"{currency_symbol}{amount:,.2f}"
