import re
from pathlib import Path

from playwright.sync_api import Page, expect

from functional_playwright.pages.data_peek import assert_data_peek_matches_file


class UploadPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.load_data_link = page.get_by_role(
            "link", name="You can load your own data"
        )
        self.browse_files_button = page.get_by_role("button", name="Browse Files")
        self.start_upload_button = page.locator(
            '[data-test-id="upload-method-inline-start"]'
        )

    def upload_file(self, file_path: Path) -> None:
        self.load_data_link.click()
        with self.page.expect_file_chooser() as file_chooser_info:
            self.browse_files_button.click()
        file_chooser_info.value.set_files(str(file_path))
        self.start_upload_button.click()

        dataset_item = self.page.locator(".content-item").filter(
            has_text=file_path.name
        )
        expect(dataset_item).to_have_attribute("data-state", "ok")
        expect(dataset_item).to_have_class(re.compile(r"\balert-success\b"))

        dataset_item.click()
        data_peek = dataset_item.locator(".dataset-peek")
        expect(data_peek).to_be_visible()

        assert_data_peek_matches_file(data_peek, file_path)
