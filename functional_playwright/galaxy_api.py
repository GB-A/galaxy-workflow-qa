from urllib.parse import quote, urljoin

from playwright.sync_api import APIResponse, Page


class GalaxyApi:
    """Read and clean up Galaxy resources through the authenticated API."""

    def __init__(self, page: Page) -> None:
        """Create an API helper bound to the page's authenticated browser context."""
        self.page = page

    def history_id(self, history_name: str) -> str:
        """Return the ID of the uniquely named Galaxy history."""
        records = self._get_records("/api/histories?keys=id,name")
        return self._find_id(records, history_name, "history")

    def workflow_id(self, workflow_name: str) -> str:
        """Return the ID of the uniquely named Galaxy workflow."""
        records = self._get_records("/api/workflows")
        return self._find_id(records, workflow_name, "workflow")

    def dataset_ids(self, history_id: str, dataset_name: str) -> tuple[str, str]:
        """Return the history-content ID and dataset ID for a named dataset."""
        path = f"/api/histories/{quote(history_id, safe='')}/contents"
        records = self._get_records(path)
        matches = [
            record
            for record in records
            if record.get("name") == dataset_name
            and record.get("history_content_type") == "dataset"
        ]
        if len(matches) != 1:
            raise LookupError(
                f"Expected one dataset named {dataset_name!r} in history "
                f"{history_id!r}, found {len(matches)}."
            )

        content_id = self._record_id(matches[0], "id", "dataset content")
        dataset_id = self._record_id(matches[0], "dataset_id", "dataset")
        return content_id, dataset_id

    def delete_history(self, history_id: str) -> None:
        """Delete the specified Galaxy history."""
        self._request("DELETE", f"/api/histories/{quote(history_id, safe='')}")

    def delete_workflow(self, workflow_id: str) -> None:
        """Delete the specified Galaxy workflow."""
        self._request("DELETE", f"/api/workflows/{quote(workflow_id, safe='')}")

    def _get_records(self, path: str) -> list[dict[str, object]]:
        """Fetch and validate a JSON list of Galaxy resource records."""
        data = self._request("GET", path).json()
        if not isinstance(data, list):
            raise TypeError(f"Expected a list of Galaxy records from {path}.")
        records: list[dict[str, object]] = []
        for record in data:
            if not isinstance(record, dict):
                raise TypeError(f"Expected a list of Galaxy records from {path}.")
            records.append(record)
        return records

    def _find_id(
        self, records: list[dict[str, object]], name: str, resource_type: str
    ) -> str:
        """Find the unique resource ID associated with an exact name."""
        matches = [record for record in records if record.get("name") == name]
        if len(matches) != 1:
            raise LookupError(
                f"Expected one {resource_type} named {name!r}, found {len(matches)}."
            )
        return self._record_id(matches[0], "id", resource_type)

    def _record_id(
        self, record: dict[str, object], key: str, resource_type: str
    ) -> str:
        """Validate and normalize an identifier from a Galaxy API record."""
        value = record.get(key)
        if not isinstance(value, (str, int)):
            raise TypeError(f"Galaxy {resource_type} record has no valid {key!r}.")
        return str(value)

    def _request(self, method: str, path: str) -> APIResponse:
        """Send an authenticated API request and raise on unsuccessful responses."""
        response = self.page.context.request.fetch(
            urljoin(self.page.url, path),
            method=method,
        )
        if not response.ok:
            raise RuntimeError(
                f"Galaxy API {method} {path} failed with HTTP "
                f"{response.status}: {response.text()}"
            )
        return response
