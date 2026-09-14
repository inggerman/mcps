"""Tests para mcp-openproject con httpx MockTransport."""

from __future__ import annotations

import httpx
import pytest

from mcp_openproject.config import OpenProjectSettings
from mcp_openproject.tools import openproject_tools


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("OPENPROJECT_API_URL", "http://op.test/api/v3")
    monkeypatch.setenv("OPENPROJECT_API_TOKEN", "test-token")
    monkeypatch.setenv("OPENPROJECT_ALLOW_WRITE", "true")
    from mcp_openproject import config
    config.settings = OpenProjectSettings()
    return config.settings


@pytest.fixture
def mock_client(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path.endswith("/projects"):
            return httpx.Response(200, json={
                "_embedded": {"elements": [{
                    "id": 1, "identifier": "eng", "name": "Engineering",
                    "description": {"raw": "desc"}, "status": "active",
                    "createdAt": "", "updatedAt": "",
                }]}
            })
        if request.method == "GET" and path.endswith("/work_packages"):
            return httpx.Response(200, json={
                "_embedded": {"elements": [{
                    "id": 10, "subject": "Bug X",
                    "_links": {"type": {"title": "Bug"}, "status": {"title": "Open"},
                               "priority": {"title": "High"}, "assignee": {"title": "german"},
                               "project": {"title": "Engineering"}},
                    "createdAt": "", "updatedAt": "", "startDate": "", "dueDate": "",
                }]}
            })
        if request.method == "GET" and "/work_packages/10" == path.split("/api/v3")[-1]:
            return httpx.Response(200, json={
                "id": 10, "subject": "Bug X",
                "description": {"raw": "desc", "html": "<p>desc</p>"},
                "_links": {"type": {"title": "Bug"}, "status": {"title": "Open"},
                           "priority": {"title": "High"}, "assignee": {"title": "german"},
                           "project": {"title": "Engineering"}},
                "createdAt": "", "updatedAt": "", "startDate": "", "dueDate": "",
                "estimatedTime": "", "spentTime": "",
            })
        if request.method == "POST" and path.endswith("/work_packages"):
            return httpx.Response(201, json={
                "id": 11, "subject": "New WP",
                "_links": {"type": {"title": "Task"}, "status": {"title": "New"}},
            })
        if request.method == "PATCH" and "/work_packages/10" in path:
            return httpx.Response(200, json={
                "id": 10, "subject": "Bug X",
                "_links": {"type": {"title": "Bug"}, "status": {"title": "Done"}},
                "updatedAt": "2026-09-14",
            })
        if request.method == "GET" and path.endswith("/types"):
            return httpx.Response(200, json={
                "_embedded": {"elements": [{
                    "id": 1, "name": "Task", "color": "#000",
                    "isDefault": True, "isMilestone": False,
                }]}
            })
        if request.method == "GET" and path.endswith("/statuses"):
            return httpx.Response(200, json={
                "_embedded": {"elements": [{
                    "id": 1, "name": "Open", "color": "#000",
                    "isDefault": True, "isClosed": False,
                }]}
            })
        if request.method == "GET" and "/work_packages/10/relations" in path:
            return httpx.Response(200, json={
                "_embedded": {"elements": [{
                    "id": 5, "type": "blocks", "fromId": 10, "toId": 20,
                    "_links": {"from": {"title": "Bug X"}, "to": {"title": "Feature Y"}},
                }]}
            })
        if request.method == "POST" and path.endswith("/relations"):
            return httpx.Response(201, json={
                "id": 6, "type": "relates", "fromId": 10, "toId": 20,
            })
        if request.method == "GET" and path.endswith("/time_entries"):
            return httpx.Response(200, json={
                "_embedded": {"elements": [{
                    "id": 1, "hours": "2h", "spentOn": "2026-09-14",
                    "_links": {"activity": {"title": "Development"},
                               "workPackage": {"title": "Bug X"},
                               "user": {"title": "german"}},
                    "comment": {"raw": "fixed"}, "createdAt": "",
                }]}
            })
        if request.method == "POST" and path.endswith("/time_entries"):
            return httpx.Response(201, json={
                "id": 2, "hours": "1h", "spentOn": "2026-09-14",
            })
        return httpx.Response(404, json={"error": "not found"})

    transport = httpx.MockTransport(handler)
    original_client = openproject_tools._client

    def _mocked_client():
        c = original_client()
        c._transport = transport
        return c

    monkeypatch.setattr(openproject_tools, "_client", _mocked_client)


def test_list_projects(settings, mock_client):
    result = openproject_tools.list_projects()
    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["name"] == "Engineering"


def test_list_work_packages(settings, mock_client):
    result = openproject_tools.list_work_packages()
    assert len(result) == 1
    assert result[0]["id"] == 10
    assert result[0]["subject"] == "Bug X"


def test_get_work_package(settings, mock_client):
    result = openproject_tools.get_work_package(10)
    assert result["id"] == 10
    assert result["description"] == "desc"


def test_create_work_package(settings, mock_client):
    result = openproject_tools.create_work_package(1, "New WP")
    assert result["id"] == 11
    assert result["subject"] == "New WP"


def test_update_work_package(settings, mock_client):
    result = openproject_tools.update_work_package(10, status_id=2)
    assert result["id"] == 10
    assert result["status"] == "Done"


def test_list_types(settings, mock_client):
    result = openproject_tools.list_types()
    assert len(result) == 1
    assert result[0]["name"] == "Task"


def test_list_statuses(settings, mock_client):
    result = openproject_tools.list_statuses()
    assert len(result) == 1
    assert result[0]["name"] == "Open"


def test_list_relations(settings, mock_client):
    result = openproject_tools.list_relations(10)
    assert len(result) == 1
    assert result[0]["type"] == "blocks"


def test_create_relation(settings, mock_client):
    result = openproject_tools.create_relation(10, 20, "relates")
    assert result["id"] == 6
    assert result["type"] == "relates"


def test_list_time_entries(settings, mock_client):
    result = openproject_tools.list_time_entries()
    assert len(result) == 1
    assert result[0]["hours"] == "2h"


def test_create_time_entry(settings, mock_client):
    result = openproject_tools.create_time_entry(10, 1.0, "2026-09-14")
    assert result["id"] == 2
    assert result["hours"] == "1h"


def test_create_work_package_requires_write(monkeypatch, settings):
    monkeypatch.setattr(settings, "allow_write", False)
    with pytest.raises(openproject_tools.McpError, match="Escritura no permitida"):
        openproject_tools.create_work_package(1, "test")


def test_update_work_package_requires_write(monkeypatch, settings):
    monkeypatch.setattr(settings, "allow_write", False)
    with pytest.raises(openproject_tools.McpError, match="Escritura no permitida"):
        openproject_tools.update_work_package(10, status_id=2)
