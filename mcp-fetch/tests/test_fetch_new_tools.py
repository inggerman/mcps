"""Tests for new mcp-fetch tools (no network required)."""

from __future__ import annotations

import pytest
from mcp_fetch.tools.fetch_tools import (
    batch_fetch_json,
    check_url,
    fetch_with_auth,
)
from mcp_shared.errors import ValidationError


def test_check_url_invalid_scheme() -> None:
    result = check_url("ftp://example.com")
    assert result["accessible"] is False
    assert "error" in result


def test_check_url_empty_url() -> None:
    result = check_url("")
    assert result["accessible"] is False
    assert "error" in result


def test_fetch_with_auth_invalid_type() -> None:
    with pytest.raises(ValidationError, match="no soportado"):
        fetch_with_auth(url="https://example.com", auth_type="invalid", token="x")


def test_batch_fetch_json_invalid_urls() -> None:
    results = batch_fetch_json(["ftp://bad", "https://nonexistent.invalid.domain.xyz"])
    assert len(results) == 2
    assert results[0]["success"] is False
    assert results[1]["success"] is False
