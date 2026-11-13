import pytest 
import re
import allure


_FAILURE_SCREENSHOT_ATTACHED = pytest.StashKey[bool]()


def _attach_failure_screenshot(item, page):
    if item.stash.get(_FAILURE_SCREENSHOT_ATTACHED, False):
        return

    allure.attach(
        page.screenshot(full_page=True),
        name="failure_screenshot",
        attachment_type=allure.attachment_type.PNG,
    )
    item.stash[_FAILURE_SCREENSHOT_ATTACHED] = True


@pytest.hookimpl
def pytest_bdd_apply_tag(tag, function):
    if re.fullmatch(r"(?:REQ_\d+|TC_UI_\d+)", tag):
        pytest.mark.req(tag)(function)
        return True


@pytest.hookimpl
def pytest_bdd_step_error(request, step_func_args):
    page = step_func_args.get("page")
    if page is not None:
        _attach_failure_screenshot(request.node, page)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page")
        if page is not None:
            _attach_failure_screenshot(item, page)