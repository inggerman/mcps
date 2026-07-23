from __future__ import annotations

import json
from pathlib import Path

import pytest
from mcp_filesystem.tools.filesystem_tools import (
    append_text_file,
    copy_path,
    count_lines,
    create_directory,
    delete_path,
    directory_tree,
    get_directory_size,
    get_file_hash,
    get_file_info,
    head_lines,
    move_path,
    read_text_file,
    tail_lines,
)
from mcp_shared.errors import ValidationError


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    (tmp_path / "notes.txt").write_text("line1\nline2\nline3\nline4\nline5\n", encoding="utf-8", newline="\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "data.json").write_text('{"key": "value"}', encoding="utf-8")
    return tmp_path


def test_head_lines(sandbox: Path) -> None:
    result = head_lines(sandbox, "notes.txt", n=2)
    assert result["returned_lines"] == 2
    assert result["lines"][0].strip() == "line1"


def test_tail_lines(sandbox: Path) -> None:
    result = tail_lines(sandbox, "notes.txt", n=2)
    assert result["lines"][-2].strip() == "line5"


def test_get_file_info(sandbox: Path) -> None:
    result = get_file_info(sandbox, "notes.txt")
    assert result["type"] == "file"
    assert result["extension"] == ".txt"


def test_get_file_info_directory(sandbox: Path) -> None:
    result = get_file_info(sandbox, "sub")
    assert result["type"] == "directory"


def test_directory_tree(sandbox: Path) -> None:
    result = directory_tree(sandbox, ".", max_depth=3)
    assert "notes.txt" in result
    assert "data.json" in result


def test_directory_size(sandbox: Path) -> None:
    result = get_directory_size(sandbox, ".")
    assert result["file_count"] >= 2
    assert result["total_size_bytes"] > 0


def test_file_hash(sandbox: Path) -> None:
    result = get_file_hash(sandbox, "notes.txt")
    assert result["algorithm"] == "sha256"
    assert len(result["hash"]) == 64


def test_file_hash_md5(sandbox: Path) -> None:
    result = get_file_hash(sandbox, "notes.txt", algorithm="md5")
    assert len(result["hash"]) == 32


def test_file_hash_invalid_algo(sandbox: Path) -> None:
    with pytest.raises(ValidationError):
        get_file_hash(sandbox, "notes.txt", algorithm="invalid")


def test_count_lines(sandbox: Path) -> None:
    result = count_lines(sandbox, "notes.txt")
    assert result["lines"] == 6  # 5 lines + trailing empty
    assert result["words"] == 5


def test_append_text_file(sandbox: Path) -> None:
    result = append_text_file(sandbox, "notes.txt", "line6\n", allow_write=True)
    assert result["bytes_appended"] == 6
    content = read_text_file(sandbox, "notes.txt", 10000)["content"]
    assert "line6" in content


def test_append_text_file_write_disabled(sandbox: Path) -> None:
    with pytest.raises(ValidationError, match="deshabilitada"):
        append_text_file(sandbox, "notes.txt", "x", allow_write=False)


def test_append_creates_new_file(sandbox: Path) -> None:
    result = append_text_file(sandbox, "new.txt", "hello", allow_write=True)
    assert result["bytes_appended"] == 5
    assert (sandbox / "new.txt").exists()


def test_create_directory(sandbox: Path) -> None:
    result = create_directory(sandbox, "newdir", allow_write=True)
    assert result["created"] is True
    assert (sandbox / "newdir").is_dir()


def test_create_directory_exists(sandbox: Path) -> None:
    with pytest.raises(ValidationError, match="ya existe"):
        create_directory(sandbox, "sub", allow_write=True)


def test_delete_path_file(sandbox: Path) -> None:
    result = delete_path(sandbox, "notes.txt", allow_write=True)
    assert result["deleted"] is True
    assert not (sandbox / "notes.txt").exists()


def test_delete_path_recursive(sandbox: Path) -> None:
    result = delete_path(sandbox, "sub", allow_write=True, recursive=True)
    assert result["deleted"] is True
    assert not (sandbox / "sub").exists()


def test_delete_path_non_recursive_dir(sandbox: Path) -> None:
    with pytest.raises(ValidationError, match="no está vacío"):
        delete_path(sandbox, "sub", allow_write=True, recursive=False)


def test_copy_path(sandbox: Path) -> None:
    result = copy_path(sandbox, "notes.txt", "notes_copy.txt", allow_write=True)
    assert result["copied"] is True
    assert (sandbox / "notes_copy.txt").exists()


def test_move_path(sandbox: Path) -> None:
    result = move_path(sandbox, "notes.txt", "notes_moved.txt", allow_write=True)
    assert result["moved"] is True
    assert not (sandbox / "notes.txt").exists()
    assert (sandbox / "notes_moved.txt").exists()
