"""searchItemsByNameUnderPrice - see the assignment's TypeScript reference signature:

    async function searchItemsByNameUnderPrice(query, maxPrice, limit = 5): Promise<string[]>

Python/Playwright equivalent below. Behaviour:
  1. Search for `query`.
  2. If the results page exposes a price filter, use it to narrow results server-side.
  3. Independently re-verify every row's own price via XPath + price parsing (defense in depth:
     correct even if the site's filter is partial, absent, or the parser disagrees with it).
  4. If fewer than `limit` matches are on the current page and a "Next" control exists, keep
     paging until `limit` is reached or pages run out.
  5. Return up to `limit` URLs; fewer (including zero) is a valid result, per the spec.
"""
from __future__ import annotations

from pom.home_page import HomePage
from core.logger import get_logger
from core.price_parser import parse_price

log = get_logger(__name__)


def search_items_by_name_under_price(
    home: HomePage, query: str, max_price: float, limit: int = 5
) -> list[str]:
    results_page = home.search(query)
    results_page.apply_max_price_filter(max_price)

    matches: list[str] = []
    pages_checked = 0

    while len(matches) < limit:
        pages_checked += 1
        for row in results_page.get_item_rows():
            price = parse_price(row["price_text"])
            if price is None or price > max_price:
                continue
            matches.append(row["url"])
            if len(matches) >= limit:
                break

        if len(matches) >= limit:
            break
        if not results_page.has_next_page():
            break
        results_page.go_to_next_page()

    log.info(
        "search_items_by_name_under_price(query=%r, max_price=%.2f, limit=%d) -> %d match(es) "
        "after checking %d page(s)",
        query, max_price, limit, len(matches), pages_checked,
    )
    return matches
