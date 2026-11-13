import os, re
import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page, expect
from pytest_bdd import given, when, then,  scenarios

from functional_playwright.pages.homepagePO import HomePage
from functional_playwright.pages.loginPO import LoginPage

load_dotenv()
scenarios('login.feature')


@given("I am not signed in to Galaxy")
def check_user_isnot_signedin(page: Page) -> None:
    page.goto("/")
    login_page = LoginPage(page)
    login_page.check_user_signed_in(user_signed_in=False)
    expect(login_page.login_link).to_be_visible()

@when("I sign in with the test user credentials")
def sign_in_with_user(page: Page) -> None:
    username = os.getenv("GALAXY_TEST_USERNAME")
    password = os.getenv("GALAXY_TEST_PASSWORD")
    if not username or not password:
        pytest.fail(
            "Set GALAXY_TEST_USERNAME and GALAXY_TEST_PASSWORD in .env "
            "or the environment before running the login scenario."
        )

    login_page = LoginPage(page)
    login_page.perform_login(username, password)

@then('I am taken to the Galaxy home page')
def check_homepage(page: Page):
    expect(page).to_have_url("http://localhost:8080/")
@then('the user menu shows the test user')
def user_menu_is_shown(page: Page):
    username = os.getenv("GALAXY_TEST_USERNAME")
    if not username:
        pytest.fail("Set GALAXY_TEST_USERNAME before running the login scenario.")

    home_page = HomePage(page)
    home_page.check_user_menu_shows("username")