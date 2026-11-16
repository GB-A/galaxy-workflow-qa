import re
from pathlib import Path

from playwright.sync_api import Locator, expect


def assert_data_peek_matches_file(data_peek: Locator, file_path: Path) -> None:
    rows = [
        line.split("\t")
        for line in file_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows, f"Expected data rows in fixture file: {file_path}"

    for row in rows:
        row_pattern = re.compile(r"\s*".join(re.escape(value) for value in row))
        expect(data_peek).to_contain_text(row_pattern)
