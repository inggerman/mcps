from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_tabular import resources as res


@pytest.fixture
def sample_csv(tmp_path: Path) -> str:
    path = tmp_path / "sample.csv"
    path.write_text(
        "name,category,amount\n"
        "alpha,A,10\n"
        "beta,B,20\n"
        "gamma,A,\n",
        encoding="utf-8",
    )
    return str(path)


# ---------------------------------------------------------------------------
# Resources estáticos
# ---------------------------------------------------------------------------


def test_supported_formats() -> None:
    result = json.loads(res.supported_formats())
    assert "formats" in result
    assert len(result["formats"]) > 0


def test_supported_encodings() -> None:
    result = json.loads(res.supported_encodings())
    assert "utf-8" in result["encodings"]


def test_filter_operators() -> None:
    result = json.loads(res.filter_operators())
    assert len(result["operators"]) == 8


def test_tips_encoding() -> None:
    result = res.tips_encoding()
    assert "UTF-8" in result


def test_tips_large_files() -> None:
    result = res.tips_large_files()
    assert "Parquet" in result


def test_tips_data_types() -> None:
    result = res.tips_data_types()
    assert "int64" in result


def test_best_practices_csv() -> None:
    result = res.best_practices_csv()
    assert "CSV" in result


def test_best_practices_excel() -> None:
    result = res.best_practices_excel()
    assert "xlsx" in result


def test_best_practices_parquet() -> None:
    result = res.best_practices_parquet()
    assert "Parquet" in result


def test_example_sample_csv() -> None:
    result = res.example_sample_csv()
    assert "id,nombre" in result


def test_example_sample_json() -> None:
    result = json.loads(res.example_sample_json())
    assert "columns" in result
    assert len(result["records"]) == 3


def test_pandas_cheatsheet() -> None:
    result = res.pandas_cheatsheet()
    assert "pd.read_csv" in result


# ---------------------------------------------------------------------------
# Resources dinámicos
# ---------------------------------------------------------------------------


def test_file_schema(sample_csv: str) -> None:
    result = json.loads(res.file_schema(sample_csv))
    assert "columns" in result
    assert len(result["columns"]) == 3


def test_file_columns(sample_csv: str) -> None:
    result = json.loads(res.file_columns(sample_csv))
    assert "name" in result["columns"]


def test_file_shape(sample_csv: str) -> None:
    result = json.loads(res.file_shape(sample_csv))
    assert result["rows"] == 3
    assert result["columns"] == 3


def test_file_dtypes(sample_csv: str) -> None:
    result = json.loads(res.file_dtypes(sample_csv))
    assert "amount" in result["dtypes"]


def test_file_nulls(sample_csv: str) -> None:
    result = json.loads(res.file_nulls(sample_csv))
    assert result["null_counts"]["amount"] == 1


def test_file_summary(sample_csv: str) -> None:
    result = json.loads(res.file_summary(sample_csv))
    assert "shape" in result


def test_file_preview(sample_csv: str) -> None:
    result = res.file_preview(sample_csv)
    assert "name" in result
    assert "|" in result


def test_file_head(sample_csv: str) -> None:
    result = res.file_head(sample_csv, n=2)
    assert "alpha" in result


def test_file_tail(sample_csv: str) -> None:
    result = res.file_tail(sample_csv, n=2)
    assert "gamma" in result


def test_file_csv(sample_csv: str) -> None:
    result = res.file_csv(sample_csv)
    assert "name,category,amount" in result


def test_file_unique(sample_csv: str) -> None:
    result = json.loads(res.file_unique(sample_csv, column="category"))
    assert result["unique_count"] == 2


def test_file_unique_missing_column(sample_csv: str) -> None:
    with pytest.raises(ValueError):
        res.file_unique(sample_csv, column="nonexistent")
