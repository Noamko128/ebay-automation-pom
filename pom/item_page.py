"""Item detail Page Object: random variant selection + add-to-cart, per the spec ("if variants
like size/color must be chosen, pick randomly among the available values")."""
from __future__ import annotations

import random

from pom.base_page import BasePage

VARIANT_SELECT_XPATH = "xpath=//div[contains(@class, 'variant-group')]//select"


class ItemPage(BasePage):
    ADD_TO_CART_BTN = "#add-to-cart-btn"
    ADDED_CONFIRMATION = "#add-to-cart-confirmation"

    def open(self, url: str) -> "ItemPage":
        self.goto(url)
        return self

    def select_random_variants(self) -> dict[str, str]:
        selections: dict[str, str] = {}
        selects = self.page.locator(VARIANT_SELECT_XPATH)
        for i in range(selects.count()):
            select = selects.nth(i)
            name = select.get_attribute("name")
            option_locators = select.locator("option")
            values = [option_locators.nth(j).get_attribute("value") for j in range(option_locators.count())]
            if not values:
                continue
            chosen = random.choice(values)
            select.select_option(chosen)
            selections[name] = chosen
        return selections

    def add_to_cart(self) -> dict[str, str]:
        """Selects random variants (if any) and clicks Add to cart, waiting for the site's own
        confirmation UI rather than a fixed sleep - avoids flakiness on slower page loads."""
        selections = self.select_random_variants()
        self.page.click(self.ADD_TO_CART_BTN)
        self.page.wait_for_selector(self.ADDED_CONFIRMATION)
        self.log.info("Added to cart with selections: %s", selections)
        return selections
