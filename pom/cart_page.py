from __future__ import annotations

from pom.base_page import BasePage
from core.price_parser import parse_price

SUBTOTAL_SELECTOR = "#cart-subtotal"


class CartPage(BasePage):
    def open(self) -> "CartPage":
        self.goto("/cart")
        return self

    def get_subtotal(self) -> float:
        text = self.page.locator(SUBTOTAL_SELECTOR).inner_text()
        amount = parse_price(text)
        if amount is None:
            raise ValueError(f"Could not parse a price out of cart subtotal text: {text!r}")
        return amount
