from pathlib import Path

import pytest
from mcp_filesystem.tools.filesystem_tools import (
    list_directory,
    read_text_file,
    resolve_path,
    search_files,
    write_text_file,
)
from mcp_shared.errors import ValidationError


def test_read_list_and_search(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("hello MCP", encoding="utf-8")
    assert list_directory(tmp_path)[0]["path"] == "notes.txt"
    assert read_text_file(tmp_path, "notes.txt", 100)["content"] == "hello MCP"
    assert search_files(tmp_path, "*.txt", "mcp")[0]["path"] == "notes.txt"


def test_path_escape_and_write_guard(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        resolve_path(tmp_path, "../outside")
    with pytest.raises(ValidationError, match="deshabilitada"):
        write_text_file(tmp_path, "new.txt", "data", allow_write=False)
    result = write_text_file(tmp_path, "new.txt", "data", allow_write=True)
    assert result["bytes_written"] == 4
