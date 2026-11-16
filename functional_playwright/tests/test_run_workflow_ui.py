import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest
from playwright.sync_api import Page
from pytest_bdd import given, scenarios, then, when
from pytest_bdd.parsers import parse

from functional_playwright.galaxy_api import GalaxyApi
from functional_playwright.pages.historypage import HistoryPage
from functional_playwright.pages.loginPO import LoginPage
from functional_playwright.pages.uploadpage import UploadPage
from functional_playwright.pages.workflowpage import WorkflowPage

scenarios("run-workflow-ui.feature")


@dataclass
class WorkflowTestContext:
    """Track test-owned Galaxy resource names and IDs.

    Attributes:
        timestamp: Unique UTC timestamp used in resource names.
        history_name: Timestamped history created by the scenario.
        dataset_name: Input dataset uploaded to the history.
        workflow_name: Timestamped name stored in the imported workflow.
        workflow_display_name: Name shown by Galaxy after importing the workflow.
        history_id: Galaxy ID of the test history.
        workflow_id: Galaxy ID of the imported workflow.
        dataset_content_id: Galaxy history-content ID of the uploaded dataset.
        dataset_id: Galaxy dataset ID of the uploaded dataset.
    """

    timestamp: str
    history_name: str
    dataset_name: str = "reads.tabular"
    workflow_name: str = ""
    workflow_display_name: str = ""
    history_id: str = ""
    workflow_id: str = ""
    dataset_content_id: str = ""
    dataset_id: str = ""


@pytest.fixture(autouse=True)
def workflow_test_context() -> WorkflowTestContext:
    """Create unique names and metadata for this workflow test run."""
    # Include microseconds so parallel or rapid retries get distinct resources.
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return WorkflowTestContext(
        timestamp=timestamp,
        history_name=f"Upload Data {timestamp}",
    )


@given("I am signed in to Galaxy")
def verify_signed_in_to_galaxy(authenticated_page: Page) -> None:
    """Open Galaxy and verify that the authenticated session is active."""
    authenticated_page.goto("/")
    LoginPage(authenticated_page).check_user_signed_in()


@then('I create new history item called "Upload Data" and save it')
def create_new_history_called_upload_data(
    authenticated_page: Page, workflow_test_context: WorkflowTestContext
) -> None:
    """Create and record the ID of this run's timestamped history."""
    # Use the page object to create and rename the history in Galaxy.
    history_page = HistoryPage(authenticated_page)
    history_page.create_history()
    history_page.rename_current_history(workflow_test_context.history_name)

    # Resolve Galaxy's generated ID for dataset lookup, cleanup, and failure reports.
    workflow_test_context.history_id = GalaxyApi(authenticated_page).history_id(
        workflow_test_context.history_name
    )


@then('I upload "reads.tabular" via the UI')
def upload_reads_tabular(
    authenticated_page: Page,
    pytestconfig,
    workflow_test_context: WorkflowTestContext,
) -> None:
    """Upload the input dataset and record its Galaxy identifiers."""
    # Resolve the fixture path from the repository root.
    source_file = pytestconfig.rootpath / "data" / "reads.tabular"
    assert source_file.is_file(), f"Test input file not found: {source_file}"
    UploadPage(authenticated_page).upload_file(source_file)

    # Store both Galaxy IDs: the history-content ID and its underlying dataset ID.
    (
        workflow_test_context.dataset_content_id,
        workflow_test_context.dataset_id,
    ) = GalaxyApi(authenticated_page).dataset_ids(
        workflow_test_context.history_id, workflow_test_context.dataset_name
    )


@when(parse('I import the workflow file "{workflow_file}"'))
def import_workflow_file(
    authenticated_page: Page,
    pytestconfig,
    tmp_path: Path,
    workflow_file: str,
    workflow_test_context: WorkflowTestContext,
) -> None:
    """Timestamp the workflow definition, import it, and record its ID."""
    # Resolve and validate the source workflow before creating a timestamped copy.
    source_file = pytestconfig.rootpath / workflow_file
    assert source_file.is_file(), f"Workflow file not found: {source_file}"

    # Parse the workflow JSON so its name can be changed without editing the fixture.
    workflow_definition = json.loads(source_file.read_text(encoding="utf-8"))
    if not isinstance(workflow_definition, dict):
        raise TypeError(f"Workflow definition must be a JSON object: {source_file}")

    # Preserve the source name as the base for this run's unique workflow name.
    base_workflow_name = workflow_definition.get("name")
    if not isinstance(base_workflow_name, str):
        raise TypeError(f"Workflow definition has no valid name: {source_file}")

    # Keep the source fixture unchanged while giving this imported workflow a unique name.
    workflow_test_context.workflow_name = (
        f"{base_workflow_name} {workflow_test_context.timestamp}"
    )
    # Set the name in the temporary import payload, not the checked-in source file.
    workflow_definition["name"] = workflow_test_context.workflow_name

    # Keep the modified workflow in pytest's temporary directory.
    timestamped_workflow_file = (
        tmp_path / f"workflow-{workflow_test_context.timestamp}.ga"
    )
    timestamped_workflow_file.write_text(
        json.dumps(workflow_definition, indent=4),
        encoding="utf-8",
    )

    # Use the page object for the Galaxy import interaction.
    workflow_page = WorkflowPage(authenticated_page)

    # Galaxy appends an import suffix. Retain the displayed name for exact API lookup.
    workflow_test_context.workflow_display_name = workflow_page.import_workflow(
        timestamped_workflow_file,
        workflow_test_context.workflow_name,
    )

    # Save the Galaxy-generated ID for targeted execution, cleanup, and failure reports.
    workflow_test_context.workflow_id = GalaxyApi(authenticated_page).workflow_id(
        workflow_test_context.workflow_display_name
    )


@then(parse('the workflow "{workflow_name}" is visible in My workflows'))
def imported_workflow_is_visible(
    authenticated_page: Page,
    workflow_test_context: WorkflowTestContext,
) -> None:
    """Verify that this run's imported workflow is listed in Galaxy."""
    WorkflowPage(authenticated_page).assert_workflow_visible(
        workflow_test_context.workflow_name
    )


@when(parse('I run the workflow "{workflow_name}" on "{input_name}"'))
def run_imported_workflow(
    authenticated_page: Page,
    input_name: str,
    workflow_test_context: WorkflowTestContext,
) -> None:
    """Start this run's workflow with the requested input dataset."""
    # Use the page object to assert workflow visibility and start the run.
    workflow_page = WorkflowPage(authenticated_page)
    workflow_page.assert_workflow_visible(workflow_test_context.workflow_name)
    workflow_page.run_workflow(input_name, workflow_test_context.workflow_id)


@then("the UI confirms that the workflow run has started")
def workflow_run_has_started(authenticated_page: Page) -> None:
    """Verify Galaxy reports that the workflow steps were scheduled."""
    WorkflowPage(authenticated_page).assert_run_started()


@then("workflow job progress is visible")
def workflow_job_progress_is_visible(authenticated_page: Page) -> None:
    """Verify that the workflow invocation displays job progress."""
    WorkflowPage(authenticated_page).assert_job_progress_visible()


@then('every workflow output reaches the "ok" state')
def every_workflow_output_reaches_ok(authenticated_page: Page) -> None:
    """Wait for each expected workflow output to complete successfully."""
    WorkflowPage(authenticated_page).wait_for_outputs_ok(
        ["Filter on dataset", "Sort on dataset", "Count on dataset"]
    )


@then("no history item enters the error state")
def no_history_item_is_in_error(authenticated_page: Page) -> None:
    """Verify that the workflow run produced no failed history items."""
    WorkflowPage(authenticated_page).assert_no_history_errors()


@then(parse('the history panel lists the outputs "{output_names}"'))
def workflow_outputs_are_visible(
    authenticated_page: Page, output_names: str
) -> None:
    """Verify that all expected output items are listed in the history."""
    # Convert the comma-separated feature parameter into individual output names.
    names = [name.strip() for name in output_names.split(",")]
    WorkflowPage(authenticated_page).assert_outputs_visible(names)


@when(parse('I open the output "{output_name}" from the history panel'))
def open_workflow_output(authenticated_page: Page, output_name: str) -> None:
    """Open the requested output so its data peek can be inspected."""
    WorkflowPage(authenticated_page).open_output(output_name)


@then(parse('the "{output_name}" dataset shown in the UI matches the golden file "{golden_file}"'))
def workflow_output_matches_golden(
    authenticated_page: Page, pytestconfig, output_name: str, golden_file: str
) -> None:
    """Compare the selected workflow output with the named golden file."""
    # Resolve the golden fixture relative to the repository root.
    expected_file = pytestconfig.rootpath / "data" / golden_file
    assert expected_file.is_file(), f"Golden file not found: {expected_file}"
    WorkflowPage(authenticated_page).assert_output_matches_file(
        output_name, expected_file
    )


@then("I delete the test history and workflow")
def delete_successful_test_resources(
    authenticated_page: Page,
    workflow_test_context: WorkflowTestContext,
) -> None:
    """Delete the test history and workflow after every assertion has passed."""
    # This step runs only after successful assertions. Failures retain both resources.
    galaxy_api = GalaxyApi(authenticated_page)
    galaxy_api.delete_history(workflow_test_context.history_id)
    galaxy_api.delete_workflow(workflow_test_context.workflow_id)
