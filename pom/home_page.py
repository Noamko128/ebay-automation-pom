from __future__ import annotations

from pom.base_page import BasePage
from pom.search_results_page import SearchResultsPage


class HomePage(BasePage):
    CONTINUE_AS_GUEST_BTN = "#continue-as-guest-btn"
    GUEST_BANNER = "#guest-banner"

    def open(self) -> "HomePage":
        self.goto("/")
        return self

    def continue_as_guest(self) -> "HomePage":
        """Auth stub: eBay lets shoppers add to cart / check out as a guest, so real
        credentialed login (out of scope - see README assumptions) isn't required for this
        flow. Real ebay.com has no such button on its homepage (guest checkout there only
        appears later, at payment) - the count() guard makes this a no-op against "live" and
        only meaningful against the bundled "mock" profile."""
        guest_button = self.page.locator(self.CONTINUE_AS_GUEST_BTN)
        if guest_button.count() > 0:
            guest_button.click()
            self.page.wait_for_selector(self.GUEST_BANNER)
            self.log.info("Continued as guest")
        return self

    def search(self, query: str) -> SearchResultsPage:
        """Locates the search box by its placeholder text and the button by its accessible
        role/name rather than an id - real ebay.com's own search input (#gh-ac) happens to use
        the exact placeholder "Search for anything", which the mock site mirrors, so this one
        locator strategy is verified against both profiles. `exact=True` matters here: real
        ebay.com also has a "Clear search" button, whose accessible name otherwise
        substring-matches "Search" too and trips Playwright's strict-mode duplicate check."""
        self.page.get_by_placeholder("Search for anything").fill(query)
        self.page.get_by_role("button", name="Search", exact=True).click()
        self.page.wait_for_load_state("load")
        self.log.info("Searched for '%s'", query)
        return SearchResultsPage(self.page, self.base_url)
