from playwright.sync_api import Page, expect


class HistoryPage:
    """Page object for creating and naming Galaxy histories."""

    def __init__(self, page: Page) -> None:
        """Bind history controls to the supplied Playwright page."""
        self.page = page
        self.add_history_button = page.get_by_role("button", name="Create new history")
        self.edit_history_button = page.get_by_role("button", name="Edit")
        self.history_name_textbox = page.get_by_role("textbox", name="Name")
        self.save_history = page.get_by_role("button", name="Save")

    def create_history(self) -> None:
        """Create a history and verify that the new history is visible."""
        self.add_history_button.click()
        expect(self.page.get_by_role("button", name="Unnamed history")).to_be_visible()

    def rename_current_history(self, history_name: str) -> None:
        """Rename the current history and verify its updated title."""
        self.edit_history_button.click()
        self.history_name_textbox.fill(history_name)
        self.save_history.click()
        expect(self.page.get_by_role("button", name=history_name)).to_be_visible()
