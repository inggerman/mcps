"""Tests para mcp-github tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from mcp_github.tools.github_tools import (
    add_issue_comment,
    create_issue,
    create_pull_request,
    get_issue,
    get_pull_request_diff,
)
from mcp_shared.errors import ApiAuthenticationError, ValidationError


# Fixture simplificado usando unittest.mock
@pytest.fixture
def mock_client():
    with patch("mcp_github.tools.github_tools._get_client") as mock_get_client:
        client_instance = MagicMock()
        # setup context manager
        client_instance.__enter__.return_value = client_instance
        mock_get_client.return_value = client_instance
        yield client_instance


def test_create_issue_success(mock_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.text = '{"number": 1, "html_url": "http://github.com/a/b/issues/1", "title": "Test"}'
    mock_resp.json.return_value = {
        "number": 1,
        "html_url": "http://github.com/a/b/issues/1",
        "title": "Test",
    }
    mock_client.post.return_value = mock_resp

    result = create_issue("token", "https://api.github.com", 30, "owner", "repo", "Test", "Body")

    assert result["number"] == 1
    assert result["title"] == "Test"
    mock_client.post.assert_called_once()


def test_create_issue_missing_token():
    with pytest.raises(ValidationError, match="No hay token"):
        create_issue("", "https://api.github.com", 30, "owner", "repo", "Test", "Body")


def test_get_issue_auth_error(mock_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.url = "https://api.github.com/repos/a/b/issues/1"
    mock_client.get.return_value = mock_resp

    with pytest.raises(ApiAuthenticationError):
        get_issue("token", "https://api.github.com", 30, "owner", "repo", 1)


def test_create_pull_request(mock_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.text = '{"number": 42, "state": "open"}'
    mock_resp.json.return_value = {"number": 42, "state": "open"}
    mock_client.post.return_value = mock_resp

    result = create_pull_request(
        "token", "https://api.github.com", 30, "owner", "repo", "PR", "feature", "main"
    )

    assert result["number"] == 42
    assert result["state"] == "open"


def test_get_pull_request_diff(mock_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "diff --git a/file b/file"
    mock_client.get.return_value = mock_resp
    mock_client.headers = {}

    result = get_pull_request_diff("token", "https://api.github.com", 30, "owner", "repo", 42)

    assert "diff --git" in result


def test_add_issue_comment(mock_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.text = '{"id": 123}'
    mock_resp.json.return_value = {"id": 123}
    mock_client.post.return_value = mock_resp

    result = add_issue_comment("token", "https://api.github.com", 30, "owner", "repo", 1, "LGTM")

    assert result["id"] == 123
