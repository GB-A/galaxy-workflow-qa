from playwright.sync_api import Page, expect


class HomePage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.user_menu_button = page.get_by_role("button", name="user")

    def open_user_menu(self) -> None:
        self.user_menu_button.click()

    def check_user_menu_shows(self, username: str) -> None:
        self.open_user_menu()
        expect(self.page.get_by_text(username, exact=True)).to_be_visible()
