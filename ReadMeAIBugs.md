# AI Bug-Hunting Exercise

## The code under review

```python
from playwright.sync_api import sync_playwright
from selenium import webdriver
import time

def test_search_functionality():
    browser = sync_playwright().start().chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")

    time.sleep(2)

    search_box = page.locator("#search")
    search_box.fill("playwright testing")

    page.locator(".button").click()

    time.sleep(3)

    results = page.locator(".result-item")

    browser.close()
```

## Bugs found

### 1. No assertions anywhere — this test cannot fail (line 20)

```python
results = page.locator(".result-item")

browser.close()
```

`page.locator(...)` just builds a `Locator` object; it doesn't query the page or check anything.
Nothing here ever calls `.count()`, reads `.inner_text()`, or hits an `expect(...)` assertion.
Whether the search actually worked, returned results, or crashed the page entirely, this
function runs to completion and the test reports green. This is the single most serious bug:
a test that validates nothing is worse than no test, because it actively hides regressions
behind a passing badge — exactly the kind of thing that made the teammate say "it doesn't work
as I expected" with no error to go on.

**Fix**: assert on something observable, ideally with Playwright's own auto-retrying
assertions rather than a one-shot count check:

```python
from playwright.sync_api import expect

results = page.locator(".result-item")
expect(results.first).to_be_visible()
assert results.count() > 0, "Expected at least one search result"
```

### 2. Selenium imported into a Playwright script, and never used (line 2)

```python
from selenium import webdriver
```

This import does nothing for this test — `webdriver` is never referenced anywhere in the
function — and it mixes two unrelated automation frameworks in one file. This is a classic
tell for AI-generated code: the model has seen thousands of Selenium examples and thousands of
Playwright examples for "search box test" and blended boilerplate from both without noticing
they don't belong together. Left in, it's a dead import at best; at worst it means `selenium`
has to be installed as a dependency for a codebase that doesn't actually use it, and it
confuses the next reader into thinking Selenium is involved in this flow.

**Fix**: delete the line. (And if this recurs across a codebase, it's worth grepping for
`import selenium` in a nominally-Playwright project as a quick sanity check.)

### 3. The `Playwright` driver object is started but never stopped (line 6)

```python
browser = sync_playwright().start().chromium.launch()
```

`sync_playwright().start()` returns a `Playwright` driver instance, which owns a background
driver process/connection. Chaining `.chromium.launch()` off it immediately and discarding the
reference means there is no handle left to call `.stop()` on later — the driver process is
leaked for the lifetime of the Python process. `browser.close()` at the end only closes the
*browser*, not the driver that launched it. Run this in a long-lived test session or a loop and
the leaked driver processes accumulate.

**Fix**: use the `with sync_playwright() as p:` context manager, which guarantees `stop()` runs
even if something in the middle raises:

```python
with sync_playwright() as p:
    browser = p.chromium.launch()
    ...
```

### 4. No explicit `BrowserContext`, and nothing is ever closed in the right order (line 7)

```python
page = browser.new_page()
```

Calling `new_page()` directly on `browser` creates an *implicit* default context behind the
scenes, with no way to configure it (viewport, locale, tracing, storage state, etc.) and no
explicit reference to close it. `browser.close()` at the end will tear down that implicit
context along with it, but if this function is extended later (e.g. to open a second page, or
to run assertions after an exception), there's no `context` variable to reason about or clean up
independently of the browser. This also matters for isolation: an explicit context is what lets
each test get its own cookies/storage without leaking into the next one — see this project's own
`tests/conftest.py`, where a fresh `BrowserContext` is created per test for exactly that reason.

**Fix**: create the context explicitly and close it before closing the browser:

```python
context = browser.new_context()
page = context.new_page()
...
context.close()
browser.close()
```

### 5. Hardcoded `time.sleep()` instead of waiting on real page state (lines 9 and 16)

```python
time.sleep(2)
...
time.sleep(3)
```

Both sleeps are guesses about how long the page needs. They're slow when the page is actually
ready sooner (every run pays the full 2+3 seconds regardless), and still flaky when it's slower
than guessed (a loaded CI machine, a slow network) — the next line proceeds against a page that
isn't ready yet, with no error explaining why. Playwright already auto-waits for elements to be
actionable before interacting with them, so most of these sleeps aren't even necessary; where an
explicit wait genuinely is needed, it should be tied to a real condition, not a clock.

**Fix**: remove the sleeps and, only where actually needed, wait on the specific thing that
matters:

```python
page.goto("https://example.com")
search_box = page.locator("#search")
search_box.fill("playwright testing")
page.locator(".button").click()
page.wait_for_load_state("load")  # or wait_for_selector(...) on a specific result element
```

### 6. Overly generic locator likely to match the wrong element (line 14)

```python
page.locator(".button").click()
```

`.button` is a generic, presentational class name — the kind of thing many unrelated elements
on a real page share (a "Search" button, a cookie-consent banner's button, a "Sign in" button,
etc.). In Playwright's default (non-strict-mode-tolerant) usage this either clicks whichever
element happens to match first, silently, or raises a strict-mode error if there's more than
one — either way, it isn't reliably clicking "the search submit button" on purpose. This is the
same category of mistake this project's own `pom/home_page.py` had to explicitly guard against
(`get_by_role("button", name="Search", exact=True)`, chosen specifically because a plain
`name="Search"` locator on real ebay.com ambiguously also matched a "Clear search" button).

**Fix**: locate by role/accessible name, or another attribute that's actually unique to this
control, not a shared styling class:

```python
page.get_by_role("button", name="Search").click()
```

### 7. No `try`/`finally` around browser teardown (whole function)

```python
browser = sync_playwright().start().chromium.launch()
page = browser.new_page()
page.goto("https://example.com")
...
browser.close()
```

`browser.close()` is the last line of the function. If `page.goto(...)`, the `fill(...)`, the
`click(...)`, or the (missing) assertion raises for any reason, the function exits via the
exception and `browser.close()` never runs. Combined with bug #3, this compounds into a real
resource leak on every single failure — precisely the runs where you'd want teardown to still
happen so the next test isn't fighting a leftover browser process for resources.

**Fix**: guarantee cleanup with `finally` (or, better, let a context manager / pytest fixture
own the lifecycle entirely, as in `tests/conftest.py`'s `browser`/`context`/`page` fixtures,
which yield inside a `try`/`finally`-equivalent generator so teardown always runs):

```python
browser = p.chromium.launch()
try:
    context = browser.new_context()
    page = context.new_page()
    ...
finally:
    browser.close()
```

## Corrected version, all fixes combined

```python
from playwright.sync_api import sync_playwright, expect

def test_search_functionality():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://example.com")

            page.locator("#search").fill("playwright testing")
            page.get_by_role("button", name="Search").click()

            results = page.locator(".result-item")
            expect(results.first).to_be_visible()
            assert results.count() > 0, "Expected at least one search result"

            context.close()
        finally:
            browser.close()
```
