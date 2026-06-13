from __future__ import annotations

from pathlib import Path

import pytest
from mcp_shared.errors import InvalidValueError, ValidationError
from mcp_tabular.tools.tabular_reader import (
    filter_rows,
    get_column_stats,
    read_tabular_file,
    search_in_file,
)


@pytest.fixture
def sample_csv(tmp_path: Path) -> str:
    path = tmp_path / "sample.csv"
    path.write_text("name,amount\nalpha,10\nbeta,20\nalphabet,30\n", encoding="utf-8")
    return str(path)


def test_read_csv(sample_csv: str) -> None:
    result = read_tabular_file(sample_csv)
    assert result["total_rows"] == 3
    assert result["records"][1]["name"] == "beta"


def test_filter_rows(sample_csv: str) -> None:
    result = filter_rows(sample_csv, "amount", "gt", "10")
    assert result["total_rows"] == 2


def test_search_in_file(sample_csv: str) -> None:
    result = search_in_file(sample_csv, "alpha")
    assert len(result) == 2


def test_column_stats(sample_csv: str) -> None:
    result = get_column_stats(sample_csv, "amount")
    assert result["numeric"]["sum"] == 60.0


def test_invalid_operator(sample_csv: str) -> None:
    with pytest.raises(InvalidValueError):
        filter_rows(sample_csv, "amount", "bad", "10")


def test_missing_column(sample_csv: str) -> None:
    with pytest.raises(ValidationError):
        get_column_stats(sample_csv, "missing")
