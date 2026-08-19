"""Base Page Object: behaviour every concrete page shares (OOP base class, not copy-paste)."""
from __future__ import annotations

from playwright.sync_api import Page

from core.logger import get_logger


class BasePage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.log = get_logger(self.__class__.__name__)

    def goto(self, path: str) -> None:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        self.log.info("Navigating to %s", url)
        self.page.goto(url)

    def to_absolute(self, href: str) -> str:
        return href if href.startswith("http") else f"{self.base_url}{href}"

    @property
    def url(self) -> str:
        return self.page.url
