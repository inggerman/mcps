"""Tests para mcp-plane con httpx MockTransport.

Sigue el patrón de mcp-comfyui: patchea `_client` y `settings` directamente
en el módulo de tools, no en `config` (las tools ya importaron `settings`).
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from mcp_plane.config import PlaneSettings
from mcp_plane.tools import plane_tools


def _mock_transport(handler):
    return httpx.MockTransport(handler)


def _patch_client(handler):
    """Context manager que reemplaza _client con un MockTransport."""
    transport = _mock_transport(handler)

    def _mocked_client():
        return httpx.Client(transport=transport, base_url="http://plane.test")

    return patch("mcp_plane.tools.plane_tools._client", _mocked_client)


def _write_settings(**overrides):
    """Crea un PlaneSettings con valores de test."""
    defaults = {
        "api_url": "http://plane.test/api/v1",
        "api_token": "test-token",
        "workspace_slug": "eng",
        "allow_write": True,
    }
    defaults.update(overrides)
    return PlaneSettings(**defaults)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def _handler(request: httpx.Request) -> httpx.Response:
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
    if request.method == "GET" and "/projects/p1/issues/i1" in path:
        return httpx.Response(200, json={
            "id": "i1", "name": "Bug X",
            "description_html": "<p>desc</p>",
            "description_stripped": "desc",
            "sequence_id": 1, "state": "open", "priority": "high",
            "assignees": [], "labels": [], "cycle": "", "module": "",
            "parent": "", "created_at": "", "updated_at": "",
            "created_by": "u1", "updated_by": "u1",
        })
    if request.method == "GET" and "/projects/p1/issues" in path and path.count("issues") == 1:
        return httpx.Response(200, json=[{
            "id": "i1", "name": "Bug X", "sequence_id": 1,
            "state": "open", "priority": "high",
            "assignees": [], "labels": [], "cycle": "", "module": "",
            "created_at": "", "updated_at": "",
        }])
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


# ---------------------------------------------------------------------------
# Tests de lectura
# ---------------------------------------------------------------------------


def test_list_projects():
    with _patch_client(_handler), patch("mcp_plane.tools.plane_tools.settings", _write_settings()):
        result = plane_tools.list_projects()
    assert len(result) == 1
    assert result[0]["id"] == "p1"
    assert result[0]["name"] == "Workspace"


def test_list_cycles():
    with _patch_client(_handler), patch("mcp_plane.tools.plane_tools.settings", _write_settings()):
        result = plane_tools.list_cycles("p1")
    assert len(result) == 1
    assert result[0]["id"] == "c1"
    assert result[0]["is_active"] is True


def test_list_modules():
    with _patch_client(_handler), patch("mcp_plane.tools.plane_tools.settings", _write_settings()):
        result = plane_tools.list_modules("p1")
    assert len(result) == 1
    assert result[0]["id"] == "m1"


def test_list_issues():
    with _patch_client(_handler), patch("mcp_plane.tools.plane_tools.settings", _write_settings()):
        result = plane_tools.list_issues("p1")
    assert len(result) == 1
    assert result[0]["id"] == "i1"
    assert result[0]["name"] == "Bug X"


def test_get_issue():
    with _patch_client(_handler), patch("mcp_plane.tools.plane_tools.settings", _write_settings()):
        result = plane_tools.get_issue("p1", "i1")
    assert result["id"] == "i1"
    assert result["description_stripped"] == "desc"


# ---------------------------------------------------------------------------
# Tests de escritura
# ---------------------------------------------------------------------------


def test_create_issue():
    with _patch_client(_handler), patch("mcp_plane.tools.plane_tools.settings", _write_settings()):
        result = plane_tools.create_issue("p1", "New issue")
    assert result["id"] == "i2"
    assert result["name"] == "New issue"


def test_update_issue():
    with _patch_client(_handler), patch("mcp_plane.tools.plane_tools.settings", _write_settings()):
        result = plane_tools.update_issue("p1", "i1", state="done")
    assert result["id"] == "i1"
    assert result["state"] == "done"


def test_list_states():
    with _patch_client(_handler), patch("mcp_plane.tools.plane_tools.settings", _write_settings()):
        result = plane_tools.list_states("p1")
    assert len(result) == 1
    assert result[0]["id"] == "s1"
    assert result[0]["default"] is True


def test_list_labels():
    with _patch_client(_handler), patch("mcp_plane.tools.plane_tools.settings", _write_settings()):
        result = plane_tools.list_labels("p1")
    assert len(result) == 1
    assert result[0]["id"] == "l1"
    assert result[0]["name"] == "bug"


# ---------------------------------------------------------------------------
# Tests de write-gate
# ---------------------------------------------------------------------------


def test_create_issue_requires_write():
    settings = _write_settings(allow_write=False)
    with patch("mcp_plane.tools.plane_tools.settings", settings):
        with pytest.raises(plane_tools.McpError, match="Escritura no permitida"):
            plane_tools.create_issue("p1", "test")


def test_update_issue_requires_write():
    settings = _write_settings(allow_write=False)
    with patch("mcp_plane.tools.plane_tools.settings", settings):
        with pytest.raises(plane_tools.McpError, match="Escritura no permitida"):
            plane_tools.update_issue("p1", "i1", state="done")
