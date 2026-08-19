"""addItemsToCart and assertCartTotalNotExceeds from the assignment spec."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import BrowserContext, Page

from core.logger import get_logger
from core.price_parser import format_price
from core.screenshot_helper import capture_screenshot
from pom.cart_page import CartPage
from pom.item_page import ItemPage

log = get_logger(__name__)


def _item_slug(url: str) -> str:
    return urlparse(url).path.strip("/").replace("/", "_") or "item"


def add_items_to_cart(context: BrowserContext, base_url: str, urls: list[str], screenshots_dir: Path) -> None:
    """Opens each item URL in its own tab, adds it to the cart with a random variant selection,
    screenshots the confirmation, and closes the tab. The original search-results tab is never
    navigated away from, so it's still the active page for the caller once this returns (the
    spec's "return to the search screen/tab" behaviour)."""
    for index, url in enumerate(urls, start=1):
        item_tab = context.new_page()
        try:
            item_page = ItemPage(item_tab, base_url).open(url)
            selections = item_page.add_to_cart()
            capture_screenshot(item_tab, screenshots_dir, f"add_to_cart_{index:02d}_{_item_slug(url)}")
            log.info("[%d/%d] Added to cart: %s (selections=%s)", index, len(urls), url, selections)
        finally:
            item_tab.close()


def assert_cart_total_not_exceeds(
    page: Page, base_url: str, budget_per_item: float, items_count: int, screenshots_dir: Path, label: str = ""
) -> None:
    cart_page = CartPage(page, base_url).open()
    try:
        subtotal = cart_page.get_subtotal()
        threshold = budget_per_item * items_count
        log.info(
            "Cart subtotal %s vs threshold %s (budgetPerItem=%s x itemsCount=%d)",
            format_price(subtotal), format_price(threshold), format_price(budget_per_item), items_count,
        )
        assert subtotal <= threshold, (
            f"Cart subtotal {format_price(subtotal)} exceeds allowed threshold "
            f"{format_price(threshold)} (budgetPerItem={format_price(budget_per_item)} x "
            f"itemsCount={items_count})"
        )
    finally:
        name = f"cart_total_assertion_{label}" if label else "cart_total_assertion"
        capture_screenshot(page, screenshots_dir, name)
