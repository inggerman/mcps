from __future__ import annotations

import json
from pathlib import Path

import pytest
from mcp_shared.errors import InvalidValueError, ValidationError

from mcp_tabular.tools.tabular_transform import (
    convert_to_json,
    convert_to_markdown,
    drop_columns,
    drop_duplicates,
    drop_nulls,
    fill_nulls,
    get_correlation,
    get_duplicates_info,
    groupby_agg,
    head_rows,
    melt_table,
    pivot_table,
    rename_columns,
    sample_rows,
    select_columns,
    sort_rows,
    tail_rows,
)


@pytest.fixture
def sample_csv(tmp_path: Path) -> str:
    path = tmp_path / "sample.csv"
    path.write_text(
        "name,category,amount\n"
        "alpha,A,10\n"
        "beta,B,20\n"
        "alpha,A,30\n"
        "gamma,B,\n"
        "beta,A,40\n",
        encoding="utf-8",
    )
    return str(path)


# ---------------------------------------------------------------------------
# sort_rows
# ---------------------------------------------------------------------------


def test_sort_rows_ascending(sample_csv: str) -> None:
    result = sort_rows(sample_csv, by="amount")
    assert result["total_rows"] == 5
    assert result["records"][0]["name"] == "alpha"


def test_sort_rows_descending(sample_csv: str) -> None:
    result = sort_rows(sample_csv, by="amount", ascending=False)
    assert result["records"][0]["amount"] == 40


def test_sort_rows_missing_column(sample_csv: str) -> None:
    with pytest.raises(ValidationError):
        sort_rows(sample_csv, by="nonexistent")


# ---------------------------------------------------------------------------
# drop_columns / select_columns
# ---------------------------------------------------------------------------


def test_drop_columns(sample_csv: str) -> None:
    result = drop_columns(sample_csv, columns="amount")
    assert "amount" not in [c["name"] for c in result["columns"]]


def test_drop_columns_missing(sample_csv: str) -> None:
    with pytest.raises(ValidationError):
        drop_columns(sample_csv, columns="nonexistent")


def test_select_columns(sample_csv: str) -> None:
    result = select_columns(sample_csv, columns=["name", "category"])
    assert len(result["columns"]) == 2


# ---------------------------------------------------------------------------
# rename_columns
# ---------------------------------------------------------------------------


def test_rename_columns(sample_csv: str) -> None:
    result = rename_columns(sample_csv, mapping={"amount": "price"})
    assert any(c["name"] == "price" for c in result["columns"])


def test_rename_columns_empty_mapping(sample_csv: str) -> None:
    with pytest.raises(ValidationError):
        rename_columns(sample_csv, mapping={})


# ---------------------------------------------------------------------------
# fill_nulls / drop_nulls
# ---------------------------------------------------------------------------


def test_fill_nulls(sample_csv: str) -> None:
    result = fill_nulls(sample_csv, value=0)
    amounts = [r["amount"] for r in result["records"]]
    assert 0 in amounts


def test_fill_nulls_specific_columns(sample_csv: str) -> None:
    result = fill_nulls(sample_csv, value=-1, columns="amount")
    amounts = [r["amount"] for r in result["records"]]
    assert -1 in amounts


def test_drop_nulls_any(sample_csv: str) -> None:
    result = drop_nulls(sample_csv, how="any")
    assert result["total_rows"] == 4


def test_drop_nulls_invalid_how(sample_csv: str) -> None:
    with pytest.raises(InvalidValueError):
        drop_nulls(sample_csv, how="invalid")


# ---------------------------------------------------------------------------
# drop_duplicates
# ---------------------------------------------------------------------------


def test_drop_duplicates(sample_csv: str) -> None:
    result = drop_duplicates(sample_csv, subset=["name", "category"])
    assert result["total_rows"] < 5


def test_drop_duplicates_invalid_keep(sample_csv: str) -> None:
    with pytest.raises(InvalidValueError):
        drop_duplicates(sample_csv, keep="invalid")


# ---------------------------------------------------------------------------
# groupby_agg
# ---------------------------------------------------------------------------


def test_groupby_agg_mean(sample_csv: str) -> None:
    result = groupby_agg(sample_csv, by="category", agg_func="mean")
    assert result["total_rows"] == 2


def test_groupby_agg_count(sample_csv: str) -> None:
    result = groupby_agg(sample_csv, by="category", agg_func="count")
    assert result["total_rows"] == 2


def test_groupby_agg_invalid_func(sample_csv: str) -> None:
    with pytest.raises(InvalidValueError):
        groupby_agg(sample_csv, by="category", agg_func="invalid")


# ---------------------------------------------------------------------------
# pivot_table / melt_table
# ---------------------------------------------------------------------------


def test_pivot_table(sample_csv: str) -> None:
    result = pivot_table(
        sample_csv, index="name", columns="category", values="amount", aggfunc="sum",
    )
    assert result["total_rows"] > 0


def test_pivot_table_missing_column(sample_csv: str) -> None:
    with pytest.raises(ValidationError):
        pivot_table(sample_csv, index="bad", columns="category", values="amount")


def test_melt_table(sample_csv: str) -> None:
    result = melt_table(sample_csv, id_vars="name", value_vars=["amount"])
    assert "variable" in [c["name"] for c in result["columns"]]


# ---------------------------------------------------------------------------
# sample_rows / head_rows / tail_rows
# ---------------------------------------------------------------------------


def test_sample_rows(sample_csv: str) -> None:
    result = sample_rows(sample_csv, n=2, random_state=42)
    assert result["total_rows"] == 2


def test_head_rows(sample_csv: str) -> None:
    result = head_rows(sample_csv, n=2)
    assert result["total_rows"] == 2
    assert result["records"][0]["name"] == "alpha"


def test_tail_rows(sample_csv: str) -> None:
    result = tail_rows(sample_csv, n=2)
    assert result["total_rows"] == 2
    assert result["records"][-1]["name"] == "beta"


# ---------------------------------------------------------------------------
# convert_to_json / convert_to_markdown
# ---------------------------------------------------------------------------


def test_convert_to_json(sample_csv: str) -> None:
    result = convert_to_json(sample_csv)
    parsed = json.loads(result)
    assert len(parsed) == 5


def test_convert_to_markdown(sample_csv: str) -> None:
    result = convert_to_markdown(sample_csv)
    assert "name" in result
    assert "|" in result


# ---------------------------------------------------------------------------
# get_duplicates_info / get_correlation
# ---------------------------------------------------------------------------


def test_get_duplicates_info(sample_csv: str) -> None:
    result = get_duplicates_info(sample_csv, subset=["name", "category"])
    assert result["total_rows"] == 5
    assert result["duplicate_rows"] >= 1


def test_get_correlation(sample_csv: str) -> None:
    result = get_correlation(sample_csv)
    assert "correlation" in result
    assert "amount" in result["correlation"]


def test_get_correlation_invalid_method(sample_csv: str) -> None:
    with pytest.raises(InvalidValueError):
        get_correlation(sample_csv, method="invalid")
