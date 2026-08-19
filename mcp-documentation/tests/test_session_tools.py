"""Tests para Session Tools y session_tracker."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_documentation.session_tracker import (
    end_session,
    generate_session_report,
    get_session_history,
    log_session_event,
    start_session,
    track_change,
)
from mcp_documentation.tools.session_tools import (
    detect_problems_tool,
    end_session_tool,
    generate_session_report_tool,
    get_session_history_tool,
    log_session_event_tool,
    start_session_tool,
    suggest_solutions_tool,
    track_change_tool,
)


class TestStartSession:
    def test_start(self, mock_settings, tmp_root):
        result = start_session(tmp_root, project="test", context="Testing")
        assert "session_id" in result
        assert result["status"] == "active"
        assert result["session_id"].startswith("SES-")

    def test_session_file_created(self, mock_settings, tmp_root):
        result = start_session(tmp_root, project="test")
        session_file = tmp_root / "sessions" / f"{result['session_id']}.json"
        assert session_file.exists()


class TestLogSessionEvent:
    def test_log_problem(self, mock_settings, tmp_root):
        session = start_session(tmp_root, project="test")
        result = log_session_event(tmp_root, session["session_id"], "problem", "Cluster down", "high")
        assert result["total_events"] == 1

    def test_log_invalid_type(self, mock_settings, tmp_root):
        session = start_session(tmp_root)
        with pytest.raises(Exception, match="Tipos válidos"):
            log_session_event(tmp_root, session["session_id"], "invalid", "desc")

    def test_log_short_description(self, mock_settings, tmp_root):
        session = start_session(tmp_root)
        with pytest.raises(Exception, match="descripción"):
            log_session_event(tmp_root, session["session_id"], "note", "ab")


class TestTrackChange:
    def test_track_modify(self, mock_settings, tmp_root):
        session = start_session(tmp_root)
        result = track_change(tmp_root, session["session_id"], "src/app.py", "modify", "Updated function")
        assert result["total_events"] == 1

    def test_track_invalid_type(self, mock_settings, tmp_root):
        session = start_session(tmp_root)
        with pytest.raises(Exception, match="Tipos válidos"):
            track_change(tmp_root, session["session_id"], "file.py", "invalid")


class TestDetectProblems:
    def test_no_problems(self, mock_settings, tmp_root):
        session = start_session(tmp_root)
        result = detect_problems_tool(session["session_id"])
        assert result["total_problems"] == 0
        assert len(result["patterns_detected"]) == 0

    def test_recurring_problems(self, mock_settings, tmp_root):
        session = start_session(tmp_root)
        sid = session["session_id"]
        log_session_event(tmp_root, sid, "problem", "Cluster down", "high")
        log_session_event(tmp_root, sid, "problem", "Cluster down", "high")
        result = detect_problems_tool(sid)
        assert any(p["type"] == "recurring" for p in result["patterns_detected"])

    def test_blockage_detection(self, mock_settings, tmp_root):
        session = start_session(tmp_root)
        sid = session["session_id"]
        log_session_event(tmp_root, sid, "problem", "Error 1", "medium")
        log_session_event(tmp_root, sid, "problem", "Error 2", "medium")
        log_session_event(tmp_root, sid, "problem", "Error 3", "medium")
        result = detect_problems_tool(sid)
        assert any(p["type"] == "blockage" for p in result["patterns_detected"])


class TestSuggestSolutions:
    def test_no_problems(self, mock_settings, tmp_root):
        session = start_session(tmp_root)
        result = suggest_solutions_tool(session["session_id"])
        assert result["total_suggestions"] == 0


class TestEndSession:
    def test_end_generates_bitacora(self, mock_settings, tmp_root):
        session = start_session(tmp_root, project="test", context="Working")
        sid = session["session_id"]
        log_session_event(tmp_root, sid, "problem", "Found bug", "high")
        log_session_event(tmp_root, sid, "solution", "Applied fix")
        track_change(tmp_root, sid, "file.py", "modify", "Fixed bug")

        result = end_session(tmp_root, sid, summary="Fixed critical bug")
        assert result["ended_at"] is not None
        assert result["bitacora_path"] is not None
        assert Path(result["bitacora_path"]).exists()
        assert result["stats"]["problems"] == 1
        assert result["stats"]["solutions"] == 1
        assert result["stats"]["changes"] == 1

    def test_end_already_closed(self, mock_settings, tmp_root):
        session = start_session(tmp_root)
        end_session(tmp_root, session["session_id"])
        with pytest.raises(Exception, match="ya está cerrada"):
            end_session(tmp_root, session["session_id"])


class TestGetSessionHistory:
    def test_history(self, mock_settings, tmp_root):
        start_session(tmp_root, project="proj-a")
        start_session(tmp_root, project="proj-b")
        history = get_session_history_tool(limit=10)
        assert len(history) == 2

    def test_history_with_filter(self, mock_settings, tmp_root):
        start_session(tmp_root, project="proj-a")
        start_session(tmp_root, project="proj-b")
        history = get_session_history_tool(limit=10, project="proj-a")
        assert len(history) == 1
        assert history[0]["project"] == "proj-a"


class TestGenerateSessionReport:
    def test_report(self, mock_settings, tmp_root):
        session = start_session(tmp_root, project="test")
        sid = session["session_id"]
        log_session_event(tmp_root, sid, "note", "Working on feature")
        report = generate_session_report_tool(sid)
        assert "Reporte de Sesión" in report
        assert sid in report
        assert "Eventos" in report
