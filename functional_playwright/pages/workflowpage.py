import re
from pathlib import Path

from playwright.sync_api import Locator, Page, expect

from functional_playwright.pages.data_peek import assert_data_peek_matches_file


class WorkflowPage:
    """Page object for importing, running, and checking Galaxy workflows."""

    def __init__(self, page: Page) -> None:
        """Bind workflow controls to the supplied Playwright page."""
        self.page = page
        self.workflows_link = page.get_by_role("link", name="Workflows", exact=True)
        self.my_workflows_link = page.get_by_role("link", name="My workflows")
        self.create_workflow_button = page.get_by_role(
            "button", name=re.compile(r"Create Create new workflow")
        )
        self.import_workflow_button = page.get_by_role(
            "button", name=re.compile(r"Import Import workflow from")
        )
        self.upload_workflow_button = page.get_by_role(
            "button", name=re.compile(r"Upload file Upload a")
        )
        self.browse_for_file_group = page.get_by_role(
            "group", name="Browse for a file"
        )
        self.workflow_file_input = self.browse_for_file_group.get_by_role(
            "button", name=re.compile(r"No file chosen Browse")
        )
        self.workflow_file_group = page.get_by_role("group", name="Workflow File")
        self.confirm_import_button = page.get_by_role(
            "button", name="Import", exact=True
        )
        self.edit_workflow_link = page.get_by_role("link", name="Edit Workflow")
        self.execute_workflow_button = page.get_by_role(
            "button", name=re.compile(r"Run Workflow Execute this")
        )
        self.job_progress = page.get_by_role(
            "progressbar", name=re.compile(r"jobs complete", re.IGNORECASE)
        ).first
        self.successful_steps_message = page.get_by_text(
            re.compile(r"\d+ of \d+ steps successfully")
        ).first

    def import_workflow(self, file_path: Path, workflow_name: str) -> str:
        """Import a workflow file and return its displayed workflow name."""
        self.workflows_link.click()
        expect(self.create_workflow_button).to_be_visible()
        self.my_workflows_link.click()
        expect(self.import_workflow_button).to_be_visible()

        self.import_workflow_button.click()
        self.upload_workflow_button.click()
        expect(self.browse_for_file_group).to_be_visible()
        self.workflow_file_input.set_input_files(str(file_path))
        expect(self.workflow_file_group).to_be_visible()
        expect(self.workflow_file_group).to_contain_text(file_path.name)

        self.confirm_import_button.click()
        workflow_link = self.page.get_by_role(
            "link", name=re.compile(re.escape(workflow_name))
        ).first
        expect(workflow_link).to_be_visible()
        return workflow_link.inner_text().strip()

    def assert_workflow_visible(self, workflow_name: str) -> None:
        """Assert that the named workflow appears in the workflow list."""
        expect(
            self.page.get_by_role(
                "link", name=re.compile(re.escape(workflow_name))
            ).first
        ).to_be_visible()

    def run_workflow(self, input_name: str, workflow_id: str) -> None:
        """Start the specified workflow using the named dataset input."""
        run_workflow_link = self.page.locator(
            f"#g-card-action-workflow-run-{workflow_id}"
        )
        expect(run_workflow_link).to_be_visible()
        run_workflow_link.click()
        expect(self.edit_workflow_link).to_be_visible()
        expect(self.page.get_by_text(input_name, exact=True)).to_be_visible()

        self.execute_workflow_button.click()
        expect(self.successful_steps_message).to_be_visible()

    def assert_run_started(self) -> None:
        """Assert that Galaxy confirms successful workflow step scheduling."""
        expect(self.successful_steps_message).to_be_visible()

    def assert_job_progress_visible(self) -> None:
        """Assert that Galaxy displays job progress for the invocation."""
        expect(self.job_progress).to_be_visible()

    def wait_for_outputs_ok(self, output_names: list[str]) -> None:
        """Wait until every named workflow output reaches the successful state."""
        for output_name in output_names:
            output = self._history_item(output_name)
            expect(output).to_have_attribute("data-state", "ok")
            expect(output).to_have_class(re.compile(r"\balert-success\b"))

    def assert_no_history_errors(self) -> None:
        """Assert that the history contains no failed items."""
        expect(self.page.locator('.content-item[data-state="error"]')).to_have_count(0)

    def assert_outputs_visible(self, output_names: list[str]) -> None:
        """Assert that each named output appears in the history."""
        for output_name in output_names:
            expect(self._history_item(output_name)).to_be_visible()

    def open_output(self, output_name: str) -> None:
        """Open a successful history output and verify its data peek is visible."""
        output = self._history_item(output_name)
        expect(output).to_have_attribute("data-state", "ok")
        output.click()
        expect(output.locator(".dataset-peek")).to_be_visible()

    def assert_output_matches_file(self, output_name: str, file_path: Path) -> None:
        """Compare a successful workflow output's data peek with a golden file."""
        output = self._history_item(output_name)
        expect(output).to_have_attribute("data-state", "ok")
        data_peek = output.locator(".dataset-peek")
        expect(data_peek).to_be_visible()
        assert_data_peek_matches_file(data_peek, file_path)

    def _history_item(self, item_name: str) -> Locator:
        """Locate the history item whose visible text contains the given name."""
        return self.page.locator(".content-item").filter(has_text=item_name)
