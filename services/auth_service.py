"""Authentication ("הזדהות") for the shopping flow.

Real eBay login (credentials, 2FA, and potentially CAPTCHA) is explicitly out of scope for
this exercise - see README "Assumptions & Limitations". eBay itself lets shoppers add to cart
and check out as a guest, so a guest-mode stub is a faithful, unblocked substitute for a full
credentialed login flow here.
"""
from __future__ import annotations

from playwright.sync_api import Page

from core.logger import get_logger
from pom.home_page import HomePage

log = get_logger(__name__)


def ensure_guest_session(page: Page, base_url: str) -> HomePage:
    home = HomePage(page, base_url).open()
    home.continue_as_guest()
    log.info("Guest session ready")
    return home
