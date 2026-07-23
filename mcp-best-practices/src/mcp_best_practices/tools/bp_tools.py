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


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def generate_architecture_doc(project_path: Path, docs_path: Path) -> dict[str, Any]:
    """Genera docs/architecture.md con un diagrama de la arquitectura."""
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)

    arch_file = docs_path / "architecture.md"
    servers = sorted([d.name for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-")])

    content = [
        "# Architecture",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "## Overview",
        "This document describes the MCP architecture.",
        "",
        "## Servers",
        "",
        "```mermaid",
        "graph TD",
    ]

    for srv in servers:
        content.append(f"    {srv}[{srv}]")

    content.extend(["", "## Shared Components", "- mcp-shared: common library", ""])

    arch_file.write_text("\n".join(content), encoding="utf-8")

    return {
        "file_updated": str(arch_file),
        "servers_documented": len(servers),
    }


def generate_dependencies_doc(project_path: Path, docs_path: Path) -> dict[str, Any]:
    """Genera docs/dependencies.md con un mapa de dependencias."""
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)

    dep_file = docs_path / "dependencies.md"
    servers = sorted([d.name for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-")])

    content = [
        "# Dependencies",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "## Shared",
        "- mcp-shared (all servers depend on this)",
        "",
        "## Per-Server Dependencies",
    ]

    for srv in servers:
        pyproject = project_path / srv / "pyproject.toml"
        deps: list[str] = []
        if pyproject.exists():
            in_deps = False
            for line in pyproject.read_text(encoding="utf-8").splitlines():
                if "dependencies" in line and "[" in line:
                    in_deps = True
                    continue
                if in_deps:
                    if "]" in line:
                        break
                    dep = line.strip().strip('"').strip("'")
                    if dep:
                        deps.append(dep)

        content.append(f"\n### {srv}")
        if deps:
            for dep in deps:
                content.append(f"- {dep}")
        else:
            content.append("- (no dependencies found)")

    dep_file.write_text("\n".join(content), encoding="utf-8")

    return {
        "file_updated": str(dep_file),
        "servers_documented": len(servers),
    }


def scan_code_quality(project_path: Path, target: str = "") -> dict[str, Any]:
    """Escanea calidad basica del codigo en un directorio."""
    scan_path = project_path / target if target else project_path
    if not scan_path.exists() or not scan_path.is_dir():
        return {"files_scanned": 0, "issues": []}

    issues: list[dict[str, Any]] = []
    files_scanned = 0

    for f in scan_path.rglob("*.py"):
        files_scanned += 1
        try:
            content = f.read_text(encoding="utf-8")
            lines = content.splitlines()

            if len(lines) > 300:
                issues.append({"file": str(f.relative_to(project_path)), "type": "LONG_FILE", "lines": len(lines)})

            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if len(stripped) > 120 and not stripped.startswith("#"):
                    issues.append({"file": str(f.relative_to(project_path)), "type": "LONG_LINE", "line": i, "length": len(stripped)})

                if "TODO" in stripped or "FIXME" in stripped or "HACK" in stripped:
                    issues.append({"file": str(f.relative_to(project_path)), "type": "TODO", "line": i, "content": stripped})

        except Exception:
            continue

    return {
        "files_scanned": files_scanned,
        "total_issues": len(issues),
        "issues": issues[:50],
    }


def generate_readme(project_path: Path, docs_path: Path) -> dict[str, Any]:
    """Genera un README.md basico para el proyecto."""
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)

    readme_file = docs_path / "README.md"
    servers = sorted([d.name for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-")])

    content = [
        "# MCP Project",
        "",
        "## Overview",
        "Collection of MCP (Model Context Protocol) servers.",
        "",
        "## Servers",
        "",
    ]

    for srv in servers:
        content.append(f"- [{srv}](./{srv}/)")

    content.extend([
        "",
        "## Quick Start",
        "```bash",
        "docker compose up -d",
        "```",
        "",
        "## Documentation",
        "- [Project State](./project-state.md)",
        "- [Servers Reference](./servers-reference.md)",
        "- [Architecture](./architecture.md)",
    ])

    readme_file.write_text("\n".join(content), encoding="utf-8")

    return {
        "file_updated": str(readme_file),
        "servers_listed": len(servers),
    }


def check_env_consistency(project_path: Path) -> dict[str, Any]:
    """Verifica consistencia de variables .env entre servidores."""
    servers = sorted([d.name for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-")])
    env_vars: dict[str, list[str]] = {}
    issues: list[str] = []

    for srv in servers:
        env_file = project_path / srv / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key = line.split("=")[0]
                    env_vars.setdefault(key, []).append(srv)

    for key, srvs in env_vars.items():
        if len(srvs) > 1 and not key.startswith(("MCP_", "LOG_")):
            issues.append(f"Variable '{key}' definida en multiples servidores: {srvs}")

    return {
        "total_env_vars": len(env_vars),
        "shared_vars": {k: v for k, v in env_vars.items() if len(v) > 1},
        "issues": issues,
    }


def generate_changelog(project_path: Path, docs_path: Path) -> dict[str, Any]:
    """Genera un CHANGELOG.md basico."""
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)

    changelog_file = docs_path / "CHANGELOG.md"

    content = [
        "# Changelog",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "## [Unreleased]",
        "",
        "### Added",
        "- New MCP servers",
        "",
        "### Changed",
        "- Updated dependencies",
        "",
        "### Fixed",
        "- Bug fixes",
        "",
    ]

    changelog_file.write_text("\n".join(content), encoding="utf-8")

    return {
        "file_updated": str(changelog_file),
    }


def validate_dockerfiles(project_path: Path) -> dict[str, Any]:
    """Valida que todos los Dockerfiles tengan configuracion estandar."""
    servers = sorted([d.name for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-")])
    results: list[dict[str, Any]] = []

    for srv in servers:
        dockerfile = project_path / srv / "Dockerfile"
        if not dockerfile.exists():
            results.append({"server": srv, "exists": False, "issues": ["Dockerfile not found"]})
            continue

        content = dockerfile.read_text(encoding="utf-8")
        issues: list[str] = []

        if "python:3.12-slim" not in content:
            issues.append("Missing python:3.12-slim base image")
        if "mcpuser" not in content:
            issues.append("Missing non-root user (mcpuser)")
        if "HEALTHCHECK" not in content:
            issues.append("Missing HEALTHCHECK")
        if "PYTHONPATH=/app/src" not in content:
            issues.append("Missing PYTHONPATH=/app/src")
        if "uv" not in content:
            issues.append("Missing uv for package installation")

        results.append({"server": srv, "exists": True, "issues": issues, "valid": len(issues) == 0})

    return {
        "total_servers": len(servers),
        "results": results,
        "valid_count": sum(1 for r in results if r.get("valid")),
    }


def count_lines_of_code(project_path: Path, target: str = "") -> dict[str, Any]:
    """Cuenta lineas de codigo por lenguaje."""
    scan_path = project_path / target if target else project_path
    if not scan_path.exists():
        return {"total_lines": 0, "by_extension": {}}

    by_ext: dict[str, dict[str, int]] = {}

    for f in scan_path.rglob("*"):
        if f.is_file() and not any(part.startswith(".") for part in f.parts):
            ext = f.suffix or "no_ext"
            if ext not in by_ext:
                by_ext[ext] = {"files": 0, "lines": 0}
            by_ext[ext]["files"] += 1
            try:
                lines = len(f.read_text(encoding="utf-8").splitlines())
                by_ext[ext]["lines"] += lines
            except Exception:
                continue

    total_lines = sum(v["lines"] for v in by_ext.values())

    return {
        "total_lines": total_lines,
        "total_files": sum(v["files"] for v in by_ext.values()),
        "by_extension": by_ext,
    }


def generate_api_docs(project_path: Path, docs_path: Path) -> dict[str, Any]:
    """Genera documentacion de API de los servidores MCP."""
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)

    api_file = docs_path / "api-reference.md"
    servers = sorted([d.name for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-")])

    content = [
        "# API Reference",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "## MCP Servers",
        "",
    ]

    for srv in servers:
        content.append(f"### {srv}")
        content.append(f"- Path: `./{srv}/`")
        pyproject = project_path / srv / "pyproject.toml"
        if pyproject.exists():
            for line in pyproject.read_text(encoding="utf-8").splitlines():
                if "version" in line and "=" in line:
                    content.append(f"- Version: {line.split('=', 1)[1].strip().strip(chr(34))}")
                    break
        content.append("")

    api_file.write_text("\n".join(content), encoding="utf-8")

    return {
        "file_updated": str(api_file),
        "servers_documented": len(servers),
    }


def check_test_coverage(project_path: Path) -> dict[str, Any]:
    """Verifica cobertura basica de tests por servidor."""
    servers = sorted([d.name for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-")])
    results: list[dict[str, Any]] = []

    for srv in servers:
        srv_path = project_path / srv
        src_files = list((srv_path / "src").rglob("*.py")) if (srv_path / "src").exists() else []
        test_files = list((srv_path / "tests").rglob("*.py")) if (srv_path / "tests").exists() else []

        src_count = len([f for f in src_files if f.name != "__init__.py"])
        test_count = len([f for f in test_files if f.name != "__init__.py"])

        has_test_server = any(f.name == "test_server.py" for f in test_files)

        results.append({
            "server": srv,
            "src_files": src_count,
            "test_files": test_count,
            "has_test_server": has_test_server,
            "ratio": round(test_count / max(src_count, 1), 2),
        })

    return {
        "total_servers": len(servers),
        "results": results,
        "servers_with_tests": sum(1 for r in results if r["test_files"] > 0),
    }


def generate_health_report(project_path: Path) -> dict[str, Any]:
    """Genera un reporte de salud del proyecto."""
    servers = sorted([d.name for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-")])

    health: list[dict[str, Any]] = []
    for srv in servers:
        srv_path = project_path / srv
        checks: dict[str, bool] = {
            "has_dockerfile": (srv_path / "Dockerfile").exists(),
            "has_pyproject": (srv_path / "pyproject.toml").exists(),
            "has_src": (srv_path / "src").exists(),
            "has_tests": (srv_path / "tests").exists(),
            "has_resources": (srv_path / "src" / f"mcp_{srv.replace('-', '_')}" / "resources.py").exists() if (srv_path / "src").exists() else False,
        }
        health.append({
            "server": srv,
            "checks": checks,
            "health_score": sum(checks.values()) / len(checks) * 100,
        })

    avg_score = sum(h["health_score"] for h in health) / max(len(health), 1)

    return {
        "total_servers": len(servers),
        "average_health": round(avg_score, 2),
        "report": health,
    }


def list_project_files(project_path: Path, pattern: str = "*.py") -> list[dict[str, Any]]:
    """Lista archivos del proyecto que coinciden con un patron."""
    results: list[dict[str, Any]] = []
    for f in project_path.rglob(pattern):
        if any(part.startswith(".") for part in f.parts):
            continue
        if "node_modules" in f.parts or "__pycache__" in f.parts:
            continue
        try:
            stat = f.stat()
            results.append({
                "path": str(f.relative_to(project_path)),
                "size": stat.st_size,
                "lines": len(f.read_text(encoding="utf-8").splitlines()),
            })
        except Exception:
            continue

    return sorted(results, key=lambda x: x["path"])


def get_project_summary(project_path: Path) -> dict[str, Any]:
    """Genera un resumen rapido del proyecto."""
    servers = sorted([d.name for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-")])
    loc_result = count_lines_of_code(project_path)
    health_result = generate_health_report(project_path)

    return {
        "total_servers": len(servers),
        "servers": servers,
        "total_lines_of_code": loc_result["total_lines"],
        "total_files": loc_result["total_files"],
        "average_health": health_result["average_health"],
        "timestamp": datetime.now().isoformat(),
    }
