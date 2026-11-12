import pytest 
import re



@pytest.hookimpl
def pytest_bdd_apply_tag(tag, function):
    if re.fullmatch(r"(?:REQ_\d+|TC_UI_\d+)", tag):
        pytest.mark.req(tag)(function)
        return True

