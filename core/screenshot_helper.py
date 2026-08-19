"""Screenshot capture that both saves to disk and attaches to the live Allure report.

Kept as a standalone utility (not a Page Object method) since it's cross-cutting - every page
object and the cart-total assertion need it, and it has nothing to do with any single page's
locators (SRP).
"""
from __future__ import annotations

import re
from pathlib import Path

import allure
from playwright.sync_api import Page

from core.logger import get_logger

log = get_logger(__name__)
_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9_.-]+")


def capture_screenshot(page: Page, screenshots_dir: Path, name: str) -> Path:
    """Saves a full-page PNG to ``screenshots_dir`` and attaches it to the Allure report."""
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _UNSAFE_CHARS.sub("_", name)
    path = screenshots_dir / f"{safe_name}.png"
    page.screenshot(path=str(path), full_page=True)
    allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
    log.info("Screenshot saved: %s", path)
    return path
