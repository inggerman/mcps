"""Tests para la configuración del servidor mcp-markdown."""

from __future__ import annotations

import os

import pytest

from mcp_markdown.config import Settings, settings


class TestSettings:
    def test_default_server_name(self) -> None:
        assert settings.server_name == "mcp-markdown"

    def test_default_version(self) -> None:
        assert settings.server_version == "1.0.0"

    def test_allowed_extensions(self) -> None:
        assert ".md" in settings.allowed_extensions
        assert ".markdown" in settings.allowed_extensions
        assert ".mdx" in settings.allowed_extensions

    def test_max_file_size_bytes(self) -> None:
        assert settings.max_file_size_bytes == int(settings.max_file_size_mb * 1024 * 1024)

    def test_is_markdown_file_true(self, tmp_path):
        p = tmp_path / "test.md"
        p.touch()
        assert settings.is_markdown_file(p) is True

    def test_is_markdown_file_false(self, tmp_path):
        p = tmp_path / "test.txt"
        p.touch()
        assert settings.is_markdown_file(p) is False

    def test_is_markdown_file_mdx(self, tmp_path):
        p = tmp_path / "component.mdx"
        p.touch()
        assert settings.is_markdown_file(p) is True

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_MARKDOWN_LOG_LEVEL", "DEBUG")
        s = Settings()
        assert s.log_level == "DEBUG"

    def test_default_toc_depth(self) -> None:
        assert 1 <= settings.default_max_toc_depth <= 6
