from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from mcp_personal_vault.tools.vault_tools import (
    delete_entry,
    get_entry,
    get_vault_status,
    list_entries,
    load_or_create_key,
    search_entries,
    upsert_entry,
)
from mcp_shared.errors import NotFoundError, ValidationError


@pytest.fixture
def vault(tmp_path: Path) -> tuple[Path, Path, Fernet]:
    database_path = tmp_path / "vault" / "personal.db"
    key_file = tmp_path / "vault" / "vault.key"
    key = load_or_create_key(key_file)
    return database_path, key_file, Fernet(key)


def test_key_is_persistent(vault: tuple[Path, Path, Fernet]) -> None:
    _, key_file, _ = vault
    first = load_or_create_key(key_file)
    second = load_or_create_key(key_file)
    assert first == second


def test_upsert_get_list_and_search(vault: tuple[Path, Path, Fernet]) -> None:
    database_path, key_file, fernet = vault
    result = upsert_entry(
        database_path,
        fernet,
        "preferences",
        "editor",
        {"name": "VS Code", "theme": "dark"},
        tags=["technology", "tools"],
        allow_write=True,
    )
    assert result["status"] == "saved"
    assert get_entry(database_path, fernet, "preferences", "editor", False, False)[
        "value"
    ]["theme"] == "dark"
    assert list_entries(database_path)[0]["key"] == "editor"
    assert search_entries(
        database_path, fernet, "dark", None, False, False, 10
    )[0]["category"] == "preferences"
    assert get_vault_status(database_path, key_file)["entries"] == 1


def test_highly_sensitive_requires_both_flags(vault: tuple[Path, Path, Fernet]) -> None:
    database_path, _, fernet = vault
    upsert_entry(
        database_path,
        fernet,
        "identity",
        "government_id",
        {"type": "example", "last_four": "1234"},
        sensitivity="highly_sensitive",
        allow_write=True,
    )
    hidden = get_entry(database_path, fernet, "identity", "government_id", True, False)
    assert hidden["redacted"] is True
    visible = get_entry(database_path, fernet, "identity", "government_id", True, True)
    assert visible["value"]["last_four"] == "1234"


@pytest.mark.parametrize(
    ("entry_key", "value"),
    [
        ("password", "secret-value"),
        ("banking", {"pin": "1234"}),
        ("developer", {"api_key": "abc"}),
    ],
)
def test_rejects_secrets(
    vault: tuple[Path, Path, Fernet],
    entry_key: str,
    value: object,
) -> None:
    database_path, _, fernet = vault
    with pytest.raises(ValidationError, match="gestor de secretos"):
        upsert_entry(
            database_path,
            fernet,
            "credentials",
            entry_key,
            value,
            allow_write=True,
        )


def test_write_guard_and_delete(vault: tuple[Path, Path, Fernet]) -> None:
    database_path, _, fernet = vault
    with pytest.raises(ValidationError, match="escritura"):
        upsert_entry(database_path, fernet, "profile", "name", "Ada", allow_write=False)
    upsert_entry(
        database_path,
        fernet,
        "profile",
        "name",
        "Ada",
        allow_write=True,
    )
    assert delete_entry(database_path, "profile", "name", True)["status"] == "deleted"
    with pytest.raises(NotFoundError):
        get_entry(database_path, fernet, "profile", "name", False, False)
