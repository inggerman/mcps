"""Encrypted SQLite storage for personal context."""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from cryptography.fernet import Fernet, InvalidToken
from mcp_shared.errors import NotFoundError, ValidationError

Sensitivity = Literal["public", "private", "highly_sensitive"]
_SENSITIVITIES = {"public", "private", "highly_sensitive"}
_SECRET_PATTERN = re.compile(
    r"(password|passwd|passphrase|api[_ -]?key|access[_ -]?token|refresh[_ -]?token|"
    r"private[_ -]?key|seed[_ -]?phrase|mnemonic|cvv|cvc|pin)",
    re.IGNORECASE,
)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def load_or_create_key(key_file: Path, configured_key: str | None = None) -> bytes:
    """Load an environment-provided key or create a local key file."""
    if configured_key:
        key = configured_key.encode("ascii")
        try:
            Fernet(key)
        except (ValueError, TypeError) as exc:
            raise ValidationError(
                field="encryption_key",
                message="PERSONAL_VAULT_ENCRYPTION_KEY no es una clave Fernet válida.",
            ) from exc
        return key

    if key_file.exists():
        key = key_file.read_bytes().strip()
        try:
            Fernet(key)
        except (ValueError, TypeError) as exc:
            raise ValidationError(
                field="key_file",
                message="El archivo de clave no contiene una clave Fernet válida.",
            ) from exc
        return key

    key_file.parent.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key()
    key_file.write_bytes(key)
    try:
        key_file.chmod(0o600)
    except OSError:
        pass
    return key


def initialize_database(database_path: Path) -> None:
    """Create the encrypted vault schema when needed."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                entry_key TEXT NOT NULL,
                encrypted_value BLOB NOT NULL,
                sensitivity TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                source TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(category, entry_key)
            )
            """
        )
        connection.commit()
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                category TEXT,
                entry_key TEXT,
                occurred_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def _validate_name(field: str, value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 100:
        raise ValidationError(field=field, message="Debe contener entre 1 y 100 caracteres.")
    return normalized


def _validate_value(value: Any, entry_key: str, allow_secrets: bool) -> None:
    if not allow_secrets:
        serialized = json.dumps(value, ensure_ascii=False)
        if _SECRET_PATTERN.search(entry_key) or _SECRET_PATTERN.search(serialized):
            raise ValidationError(
                field="value",
                message=(
                    "La bóveda personal no almacena contraseñas, tokens, PIN, CVV, "
                    "frases semilla ni llaves privadas. Usa un gestor de secretos."
                ),
            )


def _encrypt(fernet: Fernet, value: Any) -> bytes:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
    return fernet.encrypt(payload)


def _decrypt(fernet: Fernet, payload: bytes) -> Any:
    try:
        return json.loads(fernet.decrypt(payload).decode())
    except (InvalidToken, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(
            field="vault",
            message="No se pudo descifrar la entrada. Verifica la clave de la bóveda.",
        ) from exc


def _audit(
    connection: sqlite3.Connection,
    action: str,
    category: str | None = None,
    entry_key: str | None = None,
) -> None:
    connection.execute(
        "INSERT INTO audit_log(action, category, entry_key, occurred_at) VALUES (?, ?, ?, ?)",
        (action, category, entry_key, _now_iso()),
    )


def _can_reveal(sensitivity: str, include_sensitive: bool, allow_highly_sensitive: bool) -> bool:
    return sensitivity != "highly_sensitive" or (
        include_sensitive and allow_highly_sensitive
    )


def get_vault_status(database_path: Path, key_file: Path) -> dict[str, Any]:
    initialize_database(database_path)
    with closing(sqlite3.connect(database_path)) as connection:
        total = connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        categories = connection.execute(
            "SELECT category, COUNT(*) FROM entries GROUP BY category ORDER BY category"
        ).fetchall()
        last_updated = connection.execute("SELECT MAX(updated_at) FROM entries").fetchone()[0]
    return {
        "initialized": True,
        "database_path": str(database_path),
        "key_file_exists": key_file.exists(),
        "entries": total,
        "categories": {row[0]: row[1] for row in categories},
        "last_updated": last_updated,
    }


def upsert_entry(
    database_path: Path,
    fernet: Fernet,
    category: str,
    entry_key: str,
    value: Any,
    sensitivity: Sensitivity = "private",
    tags: list[str] | None = None,
    source: str = "user",
    allow_write: bool = False,
    allow_secrets: bool = False,
) -> dict[str, Any]:
    if not allow_write:
        raise ValidationError(
            field="allow_write",
            message="La escritura está deshabilitada. Activa PERSONAL_VAULT_ALLOW_WRITE.",
        )
    category = _validate_name("category", category)
    entry_key = _validate_name("entry_key", entry_key)
    if sensitivity not in _SENSITIVITIES:
        raise ValidationError(
            field="sensitivity",
            message="Valores válidos: public, private, highly_sensitive.",
        )
    _validate_value(value, entry_key, allow_secrets)
    clean_tags = sorted({_validate_name("tag", tag) for tag in tags or []})
    now = _now_iso()
    initialize_database(database_path)
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            INSERT INTO entries(
                category, entry_key, encrypted_value, sensitivity, tags, source,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(category, entry_key) DO UPDATE SET
                encrypted_value=excluded.encrypted_value,
                sensitivity=excluded.sensitivity,
                tags=excluded.tags,
                source=excluded.source,
                updated_at=excluded.updated_at
            """,
            (
                category,
                entry_key,
                _encrypt(fernet, value),
                sensitivity,
                json.dumps(clean_tags),
                source.strip() or "user",
                now,
                now,
            ),
        )
        _audit(connection, "upsert", category, entry_key)
        connection.commit()
    return {
        "category": category,
        "key": entry_key,
        "sensitivity": sensitivity,
        "tags": clean_tags,
        "updated_at": now,
        "status": "saved",
    }


def get_entry(
    database_path: Path,
    fernet: Fernet,
    category: str,
    entry_key: str,
    include_sensitive: bool,
    allow_highly_sensitive: bool,
) -> dict[str, Any]:
    initialize_database(database_path)
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM entries WHERE category = ? AND entry_key = ?",
            (category.strip(), entry_key.strip()),
        ).fetchone()
        if row is None:
            raise NotFoundError(resource="personal_entry", identifier=f"{category}/{entry_key}")
        _audit(connection, "read", row["category"], row["entry_key"])
        connection.commit()
        reveal = _can_reveal(
            row["sensitivity"], include_sensitive, allow_highly_sensitive
        )
        value = _decrypt(fernet, row["encrypted_value"]) if reveal else "[REDACTED]"
        return {
            "category": row["category"],
            "key": row["entry_key"],
            "value": value,
            "redacted": not reveal,
            "sensitivity": row["sensitivity"],
            "tags": json.loads(row["tags"]),
            "source": row["source"],
            "updated_at": row["updated_at"],
        }


def list_entries(
    database_path: Path,
    category: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    initialize_database(database_path)
    query = (
        "SELECT category, entry_key, sensitivity, tags, source, updated_at "
        "FROM entries"
    )
    parameters: list[Any] = []
    if category:
        query += " WHERE category = ?"
        parameters.append(category.strip())
    query += " ORDER BY category, entry_key LIMIT ?"
    parameters.append(limit)
    with closing(sqlite3.connect(database_path)) as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [
        {
            "category": row[0],
            "key": row[1],
            "sensitivity": row[2],
            "tags": json.loads(row[3]),
            "source": row[4],
            "updated_at": row[5],
        }
        for row in rows
    ]


def search_entries(
    database_path: Path,
    fernet: Fernet,
    query: str,
    categories: list[str] | None,
    include_sensitive: bool,
    allow_highly_sensitive: bool,
    limit: int,
) -> list[dict[str, Any]]:
    term = query.strip().lower()
    if len(term) < 2:
        raise ValidationError(field="query", message="Debe contener al menos 2 caracteres.")
    initialize_database(database_path)
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM entries ORDER BY updated_at DESC").fetchall()
        matches: list[dict[str, Any]] = []
        allowed_categories = {item.lower() for item in categories or []}
        for row in rows:
            if allowed_categories and row["category"].lower() not in allowed_categories:
                continue
            reveal = _can_reveal(
                row["sensitivity"], include_sensitive, allow_highly_sensitive
            )
            value = _decrypt(fernet, row["encrypted_value"]) if reveal else "[REDACTED]"
            searchable = " ".join(
                [
                    row["category"],
                    row["entry_key"],
                    row["tags"],
                    json.dumps(value, ensure_ascii=False),
                ]
            ).lower()
            if term not in searchable:
                continue
            matches.append(
                {
                    "category": row["category"],
                    "key": row["entry_key"],
                    "value": value,
                    "redacted": not reveal,
                    "sensitivity": row["sensitivity"],
                    "tags": json.loads(row["tags"]),
                    "updated_at": row["updated_at"],
                }
            )
            if len(matches) >= limit:
                break
        _audit(connection, "search")
        connection.commit()
    return matches


def delete_entry(
    database_path: Path,
    category: str,
    entry_key: str,
    allow_write: bool,
) -> dict[str, str]:
    if not allow_write:
        raise ValidationError(
            field="allow_write",
            message="La escritura está deshabilitada. Activa PERSONAL_VAULT_ALLOW_WRITE.",
        )
    initialize_database(database_path)
    with closing(sqlite3.connect(database_path)) as connection:
        cursor = connection.execute(
            "DELETE FROM entries WHERE category = ? AND entry_key = ?",
            (category.strip(), entry_key.strip()),
        )
        if cursor.rowcount == 0:
            raise NotFoundError(resource="personal_entry", identifier=f"{category}/{entry_key}")
        _audit(connection, "delete", category, entry_key)
        connection.commit()
    return {"category": category, "key": entry_key, "status": "deleted"}
