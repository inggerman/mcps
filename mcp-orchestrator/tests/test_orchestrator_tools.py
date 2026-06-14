"""Tests para mcp-orchestrator."""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_orchestrator.tools.orchestrator_tools import (
    generate_boilerplate_dag,
    parse_airflow_dag,
    validate_dag_acyclicity,
)
from mcp_shared.errors import FileNotFoundError, ValidationError


@pytest.fixture
def dags_dir(tmp_path: Path) -> Path:
    d_dir = tmp_path / "dags"
    d_dir.mkdir()

    code = """
from airflow import DAG
from airflow.operators.empty import EmptyOperator

dag = DAG("test_dag")

task1 = EmptyOperator(task_id="t1", dag=dag)
task2 = EmptyOperator(task_id="t2", dag=dag)

task1 >> task2
"""
    (d_dir / "sample_dag.py").write_text(code, encoding="utf-8")

    return d_dir


def test_parse_airflow_dag(dags_dir: Path) -> None:
    res = parse_airflow_dag(dags_dir / "sample_dag.py")
    assert res["dag_id"] == "test_dag"
    assert res["tasks_found"] == 2
    assert res["dependencies"][0] == "task1 -> task2"


def test_parse_airflow_dag_not_found(dags_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_airflow_dag(dags_dir / "missing.py")


def test_validate_dag_acyclicity_valid() -> None:
    edges = [("A", "B"), ("B", "C"), ("A", "C")]
    res = validate_dag_acyclicity(edges)
    assert res["is_valid"] is True
    assert res["has_cycle"] is False


def test_validate_dag_acyclicity_invalid() -> None:
    edges = [("A", "B"), ("B", "C"), ("C", "A")]
    res = validate_dag_acyclicity(edges)
    assert res["is_valid"] is False
    assert res["has_cycle"] is True


def test_generate_boilerplate_dag() -> None:
    code = generate_boilerplate_dag("my_dag", ["extract data", "transform data", "load data"])
    assert "dag_id='my_dag'" in code
    assert "extract_data >> transform_data >> load_data" in code


def test_generate_boilerplate_dag_invalid() -> None:
    with pytest.raises(ValidationError):
        generate_boilerplate_dag("", [])
