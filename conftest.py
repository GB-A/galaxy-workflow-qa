import pytest 
import re
import allure



@pytest.hookimpl
def pytest_bdd_apply_tag(tag, function):
    if re.fullmatch(r"(?:REQ_\d+|TC_UI_\d+)", tag):
        pytest.mark.req(tag)(function)
        return True

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page")
        if page:
            allure.attach(
                page.screenshot(full_page=True),
                name="failure_screenshot",
                attachment_type=allure.attachment_type.PNG,
            )