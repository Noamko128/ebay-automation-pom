# eBay Automation POM — E2E Shopping Flow

A Playwright + Python end-to-end suite for an eBay-like shopping flow: search under a price
ceiling, add matching items to the cart (with random variant selection), and verify the cart
total doesn't exceed budget. Built as a take-home exercise; see the assignment's requirements
mapping and design rationale below.

## Requirements

- Python 3.10–3.14 (playwright/greenlet need `greenlet>=3.5.5` on 3.14 — already pinned in
  `requirements.txt`)
- No Node/Java required to run the suite. Java + the Allure commandline tool are only needed
  if you want the *interactive* Allure report UI (see "Reports" below).

## Setup & run

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

pytest                            # runs everything against the bundled mock eBay site
```

That's it — `pytest` starts the local mock site itself (see `tests/conftest.py`), runs all
scenarios, and writes reports/screenshots/traces (paths below). No `.env` file is required; copy
`.env.example` to `.env` only if you want to override defaults (browser, headless, profile).

## Reports produced by a run

| Artifact | Path | Notes |
|---|---|---|
| Self-contained HTML report | `reports/run-report.html` | Open directly in a browser, no tooling needed. |
| Allure raw results | `reports/allure-results/` | View interactively with `allure serve reports/allure-results` if you have the [Allure commandline](https://allurereport.org/docs/install/) + a JDK installed. |
| Screenshots | `screenshots/` | One per item added to cart, plus one per cart-total assertion. |
| Playwright traces | `reports/traces/` | One `.zip` per test; open with `playwright show-trace <file>`. |

## Architecture

```
config/            YAML profiles (mock/live) + browser settings — Data-Driven ENV config
data/               search_scenarios.json — Data-Driven test inputs (query/maxPrice/limit/budget)
mock_site/          Local Flask test double for eBay (see "Why a mock site?" below)
core/               Cross-cutting utilities, each with a single responsibility (SRP):
  config_loader.py    resolves the active profile + env overrides into a typed EnvConfig
  price_parser.py     robust "$19.99" / "$1,299.00" / "$19.99 to $29.99" price parsing
  logger.py           one place owning logging config
  screenshot_helper.py screenshot capture + Allure attachment
pom/                Page Object Model — one class per screen, all inheriting BasePage:
  base_page.py         shared navigation/URL helpers
  home_page.py          search box, guest-login stub
  search_results_page.py  XPath-based result extraction, price filter, pagination
  item_page.py           random variant selection, add-to-cart
  cart_page.py           subtotal parsing
services/           The 4 functions the assignment asks for, composed from POM + core:
  auth_service.py        ensure_guest_session            (הזדהות)
  search_service.py      search_items_by_name_under_price
  cart_service.py        add_items_to_cart, assert_cart_total_not_exceeds
tests/              pytest suite: conftest.py (fixtures: mock server, browser, context+tracing,
                    page) and test_e2e_shopping_flow.py, parametrized from data/search_scenarios.json
```

**OOP / POM**: every screen is a class inheriting `BasePage`; locators live as class-level
constants next to the methods that use them, so a UI change touches one file. **Services** are
the layer the assignment's four functions map onto — each one composes page objects rather than
talking to `page` directly, so the same `search_items_by_name_under_price` works unchanged
whether the browser is on the mock site or (in principle) real eBay. **SRP**: price parsing,
config resolution, logging and screenshotting are each their own module, used by page objects and
services alike, instead of being duplicated inline.

## Why a local mock eBay site?

Real `ebay.com` returned **HTTP 403** to this project's own request traffic while researching
selectors (bot/anti-scraping protection) — consistent with the assignment's note that CAPTCHA
handling is explicitly out of scope. Relying on the live site would make the suite flaky or
outright unrunnable in CI/for grading.

`mock_site/` is a small Flask app that reproduces just enough real eBay UI/URL conventions to
exercise the same automation logic honestly:
- `/sch/i.html?_nkw=...&_udlo=...&_udhi=...&_pgn=...` — search with eBay's own price-filter query
  param names, paginated (3 items/page, deliberately smaller than the default `limit=5` so
  pagination is actually exercised).
- Result rows use `s-item` / `s-item__link` / `s-item__price` classes, matching eBay's known
  markup conventions, and are extracted via XPath as the assignment specifies.
- Item pages render `<select>` variant dropdowns (size/color) exactly when a listing has them.
- Two listings are price *ranges* ("$60.00 to $75.00") whose real price depends on the selected
  variant — exercising the price-range parsing the spec calls out.
- The cart is session-backed (one per browser context, i.e. one per test), with a subtotal line
  rendered as free text (`Subtotal (3 items): $434.97`), forcing the same regex-based parsing a
  real listing page would need.

Switching to the real site is a one-line config change:

```bash
TEST_ENV=live pytest
```

but per the above, this is a **manual/best-effort demo path only** — expect eBay's bot
protection to interfere with unattended runs.

## The 4 required functions

| Spec name | Implementation |
|---|---|
| הזדהות (authentication) | `services/auth_service.py::ensure_guest_session` — guest-mode stub, see Assumptions |
| `searchItemsByNameUnderPrice(query, maxPrice, limit=5)` | `services/search_service.py::search_items_by_name_under_price` |
| `addItemsToCart(urls)` | `services/cart_service.py::add_items_to_cart` |
| `assertCartTotalNotExceeds(budgetPerItem, itemsCount)` | `services/cart_service.py::assert_cart_total_not_exceeds` |

`search_items_by_name_under_price`: searches, applies the page's own price filter *if present*,
then independently re-verifies every row's price via XPath + `price_parser` (so it's still
correct if the site's filter is partial, or absent entirely), paginating via "Next" until `limit`
matches are found or pages run out. Returns fewer than `limit` (including zero) when that's all
that qualifies — this is asserted explicitly per scenario via `expected_matches` in the data file.

`add_items_to_cart`: opens each URL in its own browser tab, picks a random value for every
variant dropdown present, clicks Add to cart, screenshots the confirmation, and closes the tab —
the original search-results tab is never navigated away from, satisfying "return to the
search screen/tab" without extra bookkeeping.

`assert_cart_total_not_exceeds`: reads the cart's own rendered subtotal (not a client-side
recomputation), screenshots the cart regardless of pass/fail, and asserts
`subtotal <= budgetPerItem * itemsCount`.

## Data-driven scenarios

`data/search_scenarios.json` drives `tests/test_e2e_shopping_flow.py` via `pytest.mark.parametrize`
— adding a scenario means editing that file, not the test code. The three bundled scenarios were
chosen to exercise specific robustness paths against the mock catalog:

| Scenario | query / maxPrice / limit | Exercises |
|---|---|---|
| `shoes_under_220_paginates_to_fill_limit` | shoes / 220 / 5 | Must page past page 1 to fill the limit (5 of 5 found) |
| `headphones_under_100_exhausts_all_pages` | headphones / 100 / 5 | Pages run out before the limit — must return the short result (4 of 5), not error |
| `watch_under_50_single_match` | watch / 50 / 5 | Near-empty result set (1 of 5) is still valid |

Config profiles (`config/config.yaml`, selected by `TEST_ENV`, overridable per-key via env vars
like `BASE_URL`/`BROWSER`/`HEADLESS`) are the other Data-Driven axis — same test code, different
target environment.

## Assumptions & limitations

- **Login**: implemented as a guest-mode stub (`continue_as_guest`), not real credentialed login.
  eBay itself allows guest checkout, and the assignment explicitly excludes CAPTCHA handling,
  which real login risks triggering.
- **Currency**: single currency, USD (`$`), throughout — no multi-currency conversion.
- **Price ranges**: for a listing priced as a range ("$X to $Y"), the *filtering* decision
  (`price <= maxPrice`) uses the lower bound `X`; the *actual charged price* added to the cart is
  whatever the selected variant resolves to (which may legitimately be higher, up to `Y`).
- **Live eBay**: not exercised automatically — see "Why a local mock site?" above.
- **Concurrency**: each pytest test gets its own browser context (hence its own cookie
  session/cart), so tests don't interfere with each other and need no manual cart reset.

## Bug-hunting exercise

See [`ReadMeAIBugs.md`](ReadMeAIBugs.md).
