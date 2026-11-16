import re
from pathlib import Path

from playwright.sync_api import Locator, Page, expect

from functional_playwright.pages.data_peek import assert_data_peek_matches_file


class UploadPage:
    def __init__(self, page: Page) -> None:
        """Create locators for Galaxy's upload dialog and its file controls."""
        self.page = page
        self.load_data_link = page.get_by_role(
            "link", name="You can load your own data"
        )
        self.upload_dialog = page.get_by_role("dialog")
        self.new_upload_beta_button = self.upload_dialog.get_by_role(
            "button", name=re.compile(r"^New upload\s+Beta$", re.IGNORECASE)
        )
        self.browse_files_button = self.upload_dialog.get_by_role(
            "button", name="Browse Files", exact=True
        )
        self.browse_button = self.upload_dialog.get_by_role(
            "button", name="Browse", exact=True
        )
        self.choose_local_file_button = self.upload_dialog.get_by_role(
            "button", name="Choose local file", exact=True
        )
        self.start_upload_button = page.locator(
            '[data-test-id="upload-method-inline-start"]'
        )

    def upload_file(self, file_path: Path) -> None:
        """Upload a local file through the active Galaxy upload dialog."""
        self.load_data_link.click()

        local_file_button = self._local_file_button()
        with self.page.expect_file_chooser() as file_chooser_info:
            local_file_button.click()
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

    def _local_file_button(self) -> Locator:
        """Return the visible local-file control in either upload-dialog version."""
        expect(self.upload_dialog).to_be_visible()
        if self.new_upload_beta_button.is_visible():
            self.new_upload_beta_button.click()

        for button in (
            self.browse_files_button,
            self.browse_button,
            self.choose_local_file_button,
        ):
            if button.is_visible():
                return button

        expect(self.browse_files_button).to_be_visible()
        return self.browse_files_button
