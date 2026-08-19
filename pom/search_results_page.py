"""Search results Page Object.

Locators here were verified live against real ebay.com (not guessed), then mirrored into the
bundled mock site so the exact same locator strategy works against either profile - see the
"Why a mock site?" section of the README for the evidence (bot-detection behaviour, why
add-to-cart isn't also exercised against production, etc.):
  - Real ebay.com's own result rows/links/prices use classes matching `s-card` /
    `s-card__link` / `s-card__price`; "Next" pagination is an `<a>` whose `aria-label` contains
    the word "next" (exact wording varies - "Go to next search page" on the live site, "Next
    page" on the mock - hence the case-insensitive `contains`, not an exact match).
  - Real ebay.com's own price-range inputs have framework-generated, non-deterministic `id`
    attributes (e.g. `s0-2-51-0-9-...-textbox`, re-rolled on every page load) - using them would
    be the opposite of a smart locator. Its `placeholder` text ("Min ILS"/"Max ILS", currency
    depends on the visitor's detected locale) is the stable thing to key off, applied via Enter
    (there is no separate "Apply" button in the live UI).
  - Result rows and their link/price are located via XPath as the assignment requires, scoped
    relative to each row (`row.locator(...)`) rather than one flat page-wide query - this keeps
    the (url, price) pairing correct even if row ordering or count changes between pages.
  - The price filter and "Next" page control are treated as *optional*: `has_price_filter()`
    and `has_next_page()` check element count before interacting, since the spec explicitly
    calls out that a page may not expose a price filter or pagination at all.
"""
from __future__ import annotations

import re

from pom.base_page import BasePage

ITEM_ROWS_XPATH = "xpath=//ul[contains(@class, 'srp-results')]//li[contains(@class, 's-card')]"
ITEM_LINK_REL_XPATH = "xpath=.//a[contains(@class, 's-card__link')]"
ITEM_PRICE_REL_XPATH = "xpath=.//*[contains(@class, 's-card__price')]"
# translate() lower-cases @aria-label so this matches both "Next page" (mock) and
# "Go to next search page" (real ebay.com) without depending on the exact wording.
NEXT_PAGE_LINK = (
    "xpath=//a[contains("
    "translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
    "'next')]"
)

_MAX_PRICE_PLACEHOLDER = re.compile(r"max", re.IGNORECASE)


class SearchResultsPage(BasePage):
    def has_price_filter(self) -> bool:
        return self.page.get_by_placeholder(_MAX_PRICE_PLACEHOLDER).count() > 0

    def apply_max_price_filter(self, max_price: float) -> "SearchResultsPage":
        if not self.has_price_filter():
            self.log.info("No price filter on this page; relying on client-side filtering only")
            return self
        max_input = self.page.get_by_placeholder(_MAX_PRICE_PLACEHOLDER).first
        max_input.fill(str(max_price))
        max_input.press("Enter")
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
            href = link.first.get_attribute("href")
            results.append({"url": self.to_absolute(href), "price_text": price.first.inner_text()})
        return results

    def has_next_page(self) -> bool:
        return self.page.locator(NEXT_PAGE_LINK).count() > 0

    def go_to_next_page(self) -> "SearchResultsPage":
        self.page.locator(NEXT_PAGE_LINK).first.click()
        self.page.wait_for_load_state("load")
        return self
