import pytest
import re
import allure

import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import Browser, expect

from functional_playwright.pages.loginPO import LoginPage


load_dotenv(Path(__file__).with_name(".env"))


_FAILURE_SCREENSHOT_ATTACHED = pytest.StashKey[bool]()
_FAILURE_CONTEXT_ATTACHED = pytest.StashKey[bool]()


def pytest_addoption(parser):
    """Register project-wide Playwright assertion settings."""
    parser.addini(
        "playwright_expect_timeout_ms",
        "Default timeout in milliseconds for Playwright expect assertions",
        type="int",
        default=5000,
    )


def pytest_configure(config):
    """Apply the configured default timeout to Playwright assertions."""
    expect.set_options(timeout=config.getini("playwright_expect_timeout_ms"))


def _attach_failure_screenshot(item, page):
    """Attach one full-page screenshot to a failed test's Allure result."""
    if item.stash.get(_FAILURE_SCREENSHOT_ATTACHED, False):
        return

    allure.attach(
        page.screenshot(full_page=True),
        name="failure_screenshot",
        attachment_type=allure.attachment_type.PNG,
    )
    item.stash[_FAILURE_SCREENSHOT_ATTACHED] = True


def _failure_context(item) -> str | None:
    """Format the workflow and dataset identifiers for test failure reports."""
    context = item.funcargs.get("workflow_test_context")
    if context is None:
        return None

    workflow_id = getattr(context, "workflow_id", "") or "not imported"
    workflow_name = getattr(context, "workflow_display_name", "") or getattr(
        context, "workflow_name", ""
    )
    dataset_name = getattr(context, "dataset_name", "") or "not uploaded"
    dataset_content_id = getattr(context, "dataset_content_id", "") or "not available"
    dataset_id = getattr(context, "dataset_id", "") or "not available"
    history_id = getattr(context, "history_id", "") or "not available"
    history_name = getattr(context, "history_name", "") or "not created"

    return (
        f"Workflow: {workflow_name or 'not imported'}\n"
        f"Workflow ID: {workflow_id}\n"
        f"Dataset used: {dataset_name}\n"
        f"Dataset content ID: {dataset_content_id}\n"
        f"Dataset ID: {dataset_id}\n"
        f"History: {history_name} (ID: {history_id})"
    )


def _attach_failure_context(item, exception: BaseException | None = None) -> None:
    """Add Galaxy resource details to the exception and attach them to Allure."""
    context = _failure_context(item)
    if context is None:
        return

    if exception is not None and context not in getattr(exception, "__notes__", []):
        exception.add_note(context)

    if item.stash.get(_FAILURE_CONTEXT_ATTACHED, False):
        return

    allure.attach(
        context,
        name="Galaxy workflow failure context",
        attachment_type=allure.attachment_type.TEXT,
    )
    item.stash[_FAILURE_CONTEXT_ATTACHED] = True


@pytest.hookimpl
def pytest_bdd_apply_tag(tag, function):
    """Map requirement and UI test-case tags to pytest markers."""
    if re.fullmatch(r"(?:REQ_\d+|TC_UI_\d+)", tag):
        pytest.mark.req(tag)(function)
        return True


@pytest.hookimpl(tryfirst=True)
def pytest_bdd_step_error(request, step_func_args, exception):
    """Capture browser state and Galaxy resource IDs when a BDD step fails."""
    page = step_func_args.get("page") or step_func_args.get("authenticated_page")
    if page is not None:
        _attach_failure_screenshot(request.node, page)
    _attach_failure_context(request.node, exception)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add failure screenshots and workflow context to pytest reports."""
    outcome = yield
    rep = outcome.get_result()

    if rep.failed:
        exception = call.excinfo.value if call.excinfo is not None else None
        _attach_failure_context(item, exception)
        context = _failure_context(item)
        if context is not None:
            rep.sections.append(("Galaxy workflow test context", context))

    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page") or item.funcargs.get("authenticated_page")
        if page is not None:
            _attach_failure_screenshot(item, page)

@pytest.fixture(scope="session")
def galaxy_storage_state(
    browser: Browser, base_url: str, tmp_path_factory
) -> str:
    """Log in once and save the browser storage state for UI tests."""
    username = os.getenv("GALAXY_TEST_USERNAME")
    password = os.getenv("GALAXY_TEST_PASSWORD")
    if not username or not password:
        pytest.fail("Set GALAXY_TEST_USERNAME and GALAXY_TEST_PASSWORD.")

    context = browser.new_context(base_url=base_url)
    try:
        page = context.new_page()
        page.goto("/")
        LoginPage(page).perform_login(username, password)
        expect(page.get_by_role("button", name="User Preferences")).to_be_visible()

        state_file = tmp_path_factory.mktemp("galaxy-auth") / "storage-state.json"
        context.storage_state(path=str(state_file))
        return str(state_file)
    finally:
        context.close()


@pytest.fixture
def authenticated_page(
    browser: Browser, base_url: str, galaxy_storage_state: str
):
    """Yield an authenticated Playwright page with an isolated browser context."""
    context = browser.new_context(
        base_url=base_url,
        storage_state=galaxy_storage_state,
    )
    try:
        yield context.new_page()
    finally:
        context.close()