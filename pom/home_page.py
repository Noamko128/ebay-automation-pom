from __future__ import annotations

from pom.base_page import BasePage
from pom.search_results_page import SearchResultsPage


class HomePage(BasePage):
    SEARCH_INPUT = "#search-input"
    SEARCH_SUBMIT = "#search-submit-btn"
    CONTINUE_AS_GUEST_BTN = "#continue-as-guest-btn"
    GUEST_BANNER = "#guest-banner"

    def open(self) -> "HomePage":
        self.goto("/")
        return self

    def continue_as_guest(self) -> "HomePage":
        """Auth stub: eBay lets shoppers add to cart / check out as a guest, so real
        credentialed login (out of scope - see README assumptions) isn't required for this
        flow. This clicks through that guest entry point when it's offered."""
        guest_button = self.page.locator(self.CONTINUE_AS_GUEST_BTN)
        if guest_button.count() > 0:
            guest_button.click()
            self.page.wait_for_selector(self.GUEST_BANNER)
            self.log.info("Continued as guest")
        return self

    def search(self, query: str) -> SearchResultsPage:
        self.page.fill(self.SEARCH_INPUT, query)
        self.page.click(self.SEARCH_SUBMIT)
        self.page.wait_for_load_state("load")
        self.log.info("Searched for '%s'", query)
        return SearchResultsPage(self.page, self.base_url)
