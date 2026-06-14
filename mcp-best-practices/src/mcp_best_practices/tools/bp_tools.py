"""
Lógica de negocio de mcp-best-practices.

Genera documentación retroactiva (Project State y Servers Reference).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def update_project_state(project_path: Path, docs_path: Path) -> dict[str, Any]:
    """Genera/actualiza docs/project-state.md."""
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)

    state_file = docs_path / "project-state.md"

    # Recolectar información básica
    servers = [d.name for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-")]

    # Leer pyproject.toml principal
    version = "Unknown"
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        for line in pyproject.read_text(encoding="utf-8").splitlines():
            if line.startswith("version ="):
                version = line.split("=")[1].strip().strip('"')
                break

    content = [
        "# Project State",
        f"**Última actualización:** {datetime.now().isoformat()}",
        f"**Versión global:** {version}",
        "",
        "## Resumen",
        "Este documento mantiene el estado actual del proyecto de forma retroactiva. "
        "Debe ser consultado al inicio de cualquier conversación para entender el contexto.",
        "",
        "## Servidores MCP Activos",
    ]

    for srv in sorted(servers):
        content.append(f"- `{srv}`")

    content.extend(
        [
            "",
            "## Reglas Generales",
            "- Todos los servidores usan `FastMCP`.",
            "- Comparten lógica mediante el paquete `mcp-shared`.",
            "- Pruebas ejecutadas con `pytest` y empaquetado manejado por `uv`.",
        ]
    )

    state_file.write_text("\n".join(content), encoding="utf-8")

    return {
        "file_updated": str(state_file),
        "servers_found": len(servers),
        "timestamp": datetime.now().isoformat(),
    }


def update_servers_reference(project_path: Path, docs_path: Path) -> dict[str, Any]:
    """Genera/actualiza docs/servers-reference.md leyendo claude_desktop_config.json."""
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)

    ref_file = docs_path / "servers-reference.md"
    claude_cfg = project_path / "claude_desktop_config.json"

    content = [
        "# Servers Reference",
        f"**Última actualización:** {datetime.now().isoformat()}",
        "",
        "Documentación autogenerada basada en la configuración de Claude Desktop.",
        "",
    ]

    servers_found = 0
    if claude_cfg.exists():
        try:
            data = json.loads(claude_cfg.read_text(encoding="utf-8"))
            mcp_servers = data.get("mcpServers", {})
            servers_found = len(mcp_servers)

            for name, cfg in mcp_servers.items():
                content.extend(
                    [
                        f"## {name}",
                        f"- **Comando:** `{cfg.get('command')} {' '.join(cfg.get('args', []))}`",
                        "- **Variables de entorno (Locales):**",
                    ]
                )
                for k, v in cfg.get("env", {}).items():
                    # Ocultar tokens
                    display_v = "********" if "TOKEN" in k else v
                    content.append(f"  - `{k}`: {display_v}")
                content.append("")
        except json.JSONDecodeError:
            content.append(
                "> [!WARNING]\n> El archivo claude_desktop_config.json no es un JSON válido.\n"
            )
    else:
        content.append("> [!WARNING]\n> No se encontró claude_desktop_config.json en la raíz.\n")

    ref_file.write_text("\n".join(content), encoding="utf-8")

    return {
        "file_updated": str(ref_file),
        "servers_documented": servers_found,
    }
