"""Tests para mcp-plane con mocks HTTP (respx no disponible, se usa httpx MockTransport)."""

from __future__ import annotations

import httpx
import pytest

from mcp_plane.config import PlaneSettings
from mcp_plane.tools import plane_tools


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("PLANE_API_URL", "http://plane.test/api/v1")
    monkeypatch.setenv("PLANE_API_TOKEN", "test-token")
    monkeypatch.setenv("PLANE_WORKSPACE_SLUG", "eng")
    monkeypatch.setenv("PLANE_ALLOW_WRITE", "true")
    # Reimport settings para que tome las env vars
    from mcp_plane import config
    config.settings = PlaneSettings()
    return config.settings


@pytest.fixture
def mock_client(monkeypatch):
    """Reemplaza _client con un cliente que usa MockTransport."""
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append({
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
        })
        path = request.url.path
        if request.method == "GET" and path.endswith("/projects"):
            return httpx.Response(200, json=[{
                "id": "p1", "name": "Workspace", "identifier": "WS",
                "description": "", "state": "", "created_at": "", "updated_at": "",
            }])
        if request.method == "GET" and "/projects/p1/cycles" in path:
            return httpx.Response(200, json=[{
                "id": "c1", "name": "Sprint 1", "description": "",
                "start_date": "2026-09-01", "end_date": "2026-09-15",
                "is_active": True, "is_favorite": False,
                "created_at": "", "updated_at": "",
            }])
        if request.method == "GET" and "/projects/p1/modules" in path:
            return httpx.Response(200, json=[{
                "id": "m1", "name": "Backend", "description": "",
                "status": "in-progress", "start_date": "", "target_date": "",
                "created_at": "", "updated_at": "",
            }])
        if request.method == "GET" and "/projects/p1/issues" in path:
            return httpx.Response(200, json=[{
                "id": "i1", "name": "Bug X", "sequence_id": 1,
                "state": "open", "priority": "high",
                "assignees": [], "labels": [], "cycle": "", "module": "",
                "created_at": "", "updated_at": "",
            }])
        if request.method == "GET" and "/projects/p1/issues/i1" in path and path.count("issues") == 1:
            return httpx.Response(200, json={
                "id": "i1", "name": "Bug X",
                "description_html": "<p>desc</p>",
                "description_stripped": "desc",
                "sequence_id": 1, "state": "open", "priority": "high",
                "assignees": [], "labels": [], "cycle": "", "module": "",
                "parent": "", "created_at": "", "updated_at": "",
                "created_by": "u1", "updated_by": "u1",
            })
        if request.method == "POST" and path.endswith("/issues"):
            return httpx.Response(201, json={
                "id": "i2", "name": "New issue", "sequence_id": 2, "state": "open",
            })
        if request.method == "PATCH" and "/issues/i1" in path:
            return httpx.Response(200, json={
                "id": "i1", "name": "Bug X", "state": "done",
                "priority": "high", "updated_at": "2026-09-14",
            })
        if request.method == "GET" and "/projects/p1/states" in path:
            return httpx.Response(200, json=[{
                "id": "s1", "name": "Open", "color": "#000",
                "group": "backlog", "default": True, "sequence": 1,
            }])
        if request.method == "GET" and "/projects/p1/labels" in path:
            return httpx.Response(200, json=[{
                "id": "l1", "name": "bug", "color": "#d73a4a",
                "parent": "", "sequence": 1,
            }])
        return httpx.Response(404, json={"error": "not found"})

    transport = httpx.MockTransport(handler)
    original_client = plane_tools._client

    def _mocked_client():
        c = original_client()
        c._transport = transport
        return c

    monkeypatch.setattr(plane_tools, "_client", _mocked_client)
    return calls


def test_list_projects(settings, mock_client):
    result = plane_tools.list_projects()
    assert len(result) == 1
    assert result[0]["id"] == "p1"
    assert result[0]["name"] == "Workspace"


def test_list_cycles(settings, mock_client):
    result = plane_tools.list_cycles("p1")
    assert len(result) == 1
    assert result[0]["id"] == "c1"
    assert result[0]["is_active"] is True


def test_list_modules(settings, mock_client):
    result = plane_tools.list_modules("p1")
    assert len(result) == 1
    assert result[0]["id"] == "m1"


def test_list_issues(settings, mock_client):
    result = plane_tools.list_issues("p1")
    assert len(result) == 1
    assert result[0]["id"] == "i1"
    assert result[0]["name"] == "Bug X"


def test_get_issue(settings, mock_client):
    result = plane_tools.get_issue("p1", "i1")
    assert result["id"] == "i1"
    assert result["description_stripped"] == "desc"


def test_create_issue(settings, mock_client):
    result = plane_tools.create_issue("p1", "New issue")
    assert result["id"] == "i2"
    assert result["name"] == "New issue"


def test_update_issue(settings, mock_client):
    result = plane_tools.update_issue("p1", "i1", state="done")
    assert result["id"] == "i1"
    assert result["state"] == "done"


def test_list_states(settings, mock_client):
    result = plane_tools.list_states("p1")
    assert len(result) == 1
    assert result[0]["id"] == "s1"
    assert result[0]["default"] is True


def test_list_labels(settings, mock_client):
    result = plane_tools.list_labels("p1")
    assert len(result) == 1
    assert result[0]["id"] == "l1"
    assert result[0]["name"] == "bug"


def test_create_issue_requires_write(monkeypatch, settings):
    monkeypatch.setattr(settings, "allow_write", False)
    with pytest.raises(plane_tools.McpError, match="Escritura no permitida"):
        plane_tools.create_issue("p1", "test")


def test_update_issue_requires_write(monkeypatch, settings):
    monkeypatch.setattr(settings, "allow_write", False)
    with pytest.raises(plane_tools.McpError, match="Escritura no permitida"):
        plane_tools.update_issue("p1", "i1", state="done")
