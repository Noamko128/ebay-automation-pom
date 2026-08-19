"""E2E: search under a price ceiling -> add matches to cart -> verify the cart total.

Data-driven: scenarios come from data/search_scenarios.json (query/maxPrice/limit/budget), not
from hardcoded literals in the test body - adding a new scenario means editing that file only.
"""
from __future__ import annotations

import json
from pathlib import Path

import allure
import pytest

from core.config_loader import EnvConfig
from services import auth_service, cart_service, search_service

_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "search_scenarios.json"
SCENARIOS = json.loads(_DATA_FILE.read_text())["scenarios"]


@allure.epic("eBay shopping E2E")
@allure.feature("Search, add to cart, verify total")
@pytest.mark.e2e
@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
def test_search_add_to_cart_and_verify_total(page, context, config: EnvConfig, scenario: dict):
    query = scenario["query"]
    max_price = scenario["max_price"]
    limit = scenario["limit"]
    budget_per_item = scenario["budget_per_item"]

    with allure.step(f"Guest session + search '{query}' with maxPrice={max_price}, limit={limit}"):
        home = auth_service.ensure_guest_session(page, config.base_url)
        urls = search_service.search_items_by_name_under_price(home, query, max_price, limit)
        allure.attach("\n".join(urls) or "(no matches)", name="matched_urls", attachment_type=allure.attachment_type.TEXT)

    assert len(urls) == scenario["expected_matches"], (
        f"query={query!r} maxPrice={max_price}: expected {scenario['expected_matches']} "
        f"matches, got {len(urls)}"
    )
    if not urls:
        pytest.skip(f"No items matched query={query!r} under {max_price}; nothing to add to cart.")

    with allure.step(f"Add {len(urls)} matched item(s) to cart"):
        cart_service.add_items_to_cart(context, config.base_url, urls, config.screenshots_dir)

    with allure.step(f"Assert cart total <= {budget_per_item} x {len(urls)}"):
        cart_service.assert_cart_total_not_exceeds(
            page, config.base_url, budget_per_item, len(urls), config.screenshots_dir, label=scenario["name"]
        )
