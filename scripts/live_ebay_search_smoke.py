"""Manual proof that search_items_by_name_under_price runs, unmodified, against real ebay.com.

Deliberately NOT a pytest test / not part of the CI-facing suite: see the README's "Why a mock
site?" section for why live ebay.com isn't suitable for unattended runs (headless traffic and
direct deep-links get HTTP 403; only a headed, homepage-first navigation - exactly what this
script does - was observed to work reliably). It also deliberately stops after search/filter/
pagination and does not call add_items_to_cart: repeatedly adding items to real sellers' carts
on a production marketplace you don't own has no test value and pollutes real listing
analytics, independent of whether it's technically possible.

Usage (run headed so you can watch it):

    HEADLESS=false SLOW_MO_MS=250 python scripts/live_ebay_search_smoke.py shoes 30 5
"""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

from core.config_loader import load_config
from services import auth_service, search_service


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "shoes"
    max_price = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    config = load_config(profile="live")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.browser.headless, slow_mo=config.browser.slow_mo_ms)
        context = browser.new_context(
            viewport={"width": config.browser.viewport_width, "height": config.browser.viewport_height}
        )
        page = context.new_page()

        home = auth_service.ensure_guest_session(page, config.base_url)
        urls = search_service.search_items_by_name_under_price(home, query, max_price, limit)

        print(f"\nFound {len(urls)} item(s) for query={query!r}, maxPrice={max_price}:")
        for url in urls:
            print(f"  - {url}")

        browser.close()


if __name__ == "__main__":
    main()
