from playwright.sync_api import Page, expect


class LoginPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.login_link = page.get_by_role("link", name="Login")
        self.username = page.get_by_role(
            "textbox", name="Public Name or Email Address"
        )
        self.password = page.get_by_role("textbox", name="Password")
        self.login_button = page.get_by_role("button", name="Login")
        self.logged_in_menu = page.get_by_role("button", name="User Preferences")

    def click_login(self) -> None:
        self.login_link.click()

    def enter_username(self, username: str) -> None:
        self.username.fill(username)

    def enter_password(self, password: str) -> None:
        self.password.fill(password)

    def click_login_button(self) -> None:
        self.login_button.click()

    def check_user_signed_in(self, user_signed_in: bool = True) -> None:
        if user_signed_in:
            expect(self.logged_in_menu).to_be_visible()
        else:
            expect(self.logged_in_menu).to_be_hidden()

    def perform_login(self, username: str, password: str) -> None:
        self.check_user_signed_in(False)
        self.click_login()
        self.enter_username(username)
        self.enter_password(password)
        self.click_login_button()
        self.check_user_signed_in()
