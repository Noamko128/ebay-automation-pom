"""Search results Page Object.

Locator strategy (Robustness & Smart Locators):
  - Result rows and their link/price are located via XPath as the assignment requires, scoped
    relative to each row (`row.locator(...)`) rather than one flat page-wide query - this keeps
    the (url, price) pairing correct even if row ordering or count changes between pages.
  - The price filter and "Next" page control are treated as *optional*: `has_price_filter()`
    and `has_next_page()` check element count before interacting, since the spec explicitly
    calls out that a page may not expose a price filter or pagination at all.
"""
from __future__ import annotations

from pom.base_page import BasePage

ITEM_ROWS_XPATH = "xpath=//li[contains(@class, 's-item')]"
ITEM_LINK_REL_XPATH = "xpath=.//a[contains(@class, 's-item__link')]"
ITEM_PRICE_REL_XPATH = "xpath=.//span[contains(@class, 's-item__price')]"
NEXT_PAGE_LINK = "xpath=//a[@aria-label='Next page']"


class SearchResultsPage(BasePage):
    PRICE_MIN_INPUT = "#price-min-input"
    PRICE_MAX_INPUT = "#price-max-input"
    PRICE_FILTER_SUBMIT = "#price-filter-submit-btn"

    def has_price_filter(self) -> bool:
        return self.page.locator(self.PRICE_MAX_INPUT).count() > 0

    def apply_max_price_filter(self, max_price: float) -> "SearchResultsPage":
        if not self.has_price_filter():
            self.log.info("No price filter on this page; relying on client-side filtering only")
            return self
        self.page.fill(self.PRICE_MAX_INPUT, str(max_price))
        self.page.click(self.PRICE_FILTER_SUBMIT)
        self.page.wait_for_load_state("load")
        self.log.info("Applied max price filter: %.2f", max_price)
        return self

    def get_item_rows(self) -> list[dict]:
        """Extracts {url, price_text} for every result row on the *current* page via XPath."""
        rows = self.page.locator(ITEM_ROWS_XPATH)
        results: list[dict] = []
        for i in range(rows.count()):
            row = rows.nth(i)
            link = row.locator(ITEM_LINK_REL_XPATH)
            price = row.locator(ITEM_PRICE_REL_XPATH)
            if link.count() == 0 or price.count() == 0:
                continue
            href = link.get_attribute("href")
            results.append({"url": self.to_absolute(href), "price_text": price.inner_text()})
        return results

    def has_next_page(self) -> bool:
        return self.page.locator(NEXT_PAGE_LINK).count() > 0

    def go_to_next_page(self) -> "SearchResultsPage":
        self.page.click(NEXT_PAGE_LINK)
        self.page.wait_for_load_state("load")
        return self
