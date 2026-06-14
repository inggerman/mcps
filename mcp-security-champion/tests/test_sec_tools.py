"""Tests para mcp-security-champion."""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_security_champion.tools.sec_tools import (
    sec_audit_code,
    sec_financial_compliance,
)
from mcp_shared.errors import FileNotFoundError


@pytest.fixture
def vulnerable_file(tmp_path: Path) -> Path:
    f = tmp_path / "vuln.py"
    code = """
import hashlib

def login():
    password = 'super_secret_password'
    # TODO: remove eval
    eval("print('hello')")

def process_payment():
    credit_card = "1234-5678-9012-3456"
    url = "http://api.payment.com"
"""
    f.write_text(code, encoding="utf-8")
    return f


def test_sec_audit_code(vulnerable_file: Path) -> None:
    res = sec_audit_code(vulnerable_file)
    assert res["vulnerabilities_found"] == 2
    vulns = [f["vulnerability"] for f in res["findings"]]
    assert "Hardcoded Password/Token" in vulns
    assert "Unsafe Function (eval)" in vulns


def test_sec_financial_compliance(vulnerable_file: Path) -> None:
    res = sec_financial_compliance(vulnerable_file)
    assert res["compliance"]["pci_dss"]["status"] == "FAIL"
    notes = " ".join(res["compliance"]["pci_dss"]["notes"])
    assert "PAN" in notes
    assert "HTTP" in notes


def test_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        sec_audit_code(tmp_path / "missing.py")
