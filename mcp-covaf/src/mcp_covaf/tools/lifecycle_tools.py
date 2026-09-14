"""Tools de ciclo de vida para componentes COVAF.

Información transversal: estado de componentes, Git, dependencias, comandos de
test, manifests de despliegue.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from mcp_shared.errors import McpError

# Componentes COVAF canónicos.
COMPONENTS = [
    {
        "key": "covaf-back",
        "name": "CovafDataRefineryBack",
        "path": "covaf/CovafDataRefineryBack",
        "language": "Java 21",
        "framework": "Spring Boot 3.2.1",
        "domain": "Motor de extracción Cartas + Oficios PLD",
        "test_command": "mvn test",
        "build_command": "mvn clean package -DskipTests",
        "deploy": "Docker (ECR), docker-compose puerto 7220",
    },
    {
        "key": "covaf-ia",
        "name": "DataRefineryIA",
        "path": "covaf/IA_IMPL_COVAF/datarefineryia-api",
        "language": "Python 3.11",
        "framework": "FastAPI + MongoDB",
        "domain": "Motor de extracción Prospectos CNBV + Cartas",
        "test_command": "python -m pytest",
        "build_command": "docker build -t datarefineryia-api .",
        "deploy": "Docker Compose (API + Worker + Mongo)",
    },
    {
        "key": "covaf-front",
        "name": "CovafAlternativosFront",
        "path": "covaf/CovafAlternativosFront",
        "language": "JavaScript + TypeScript",
        "framework": "Vue 3.2.47 + Module Federation",
        "domain": "Portal Alternativos (instrumentos, cartas, monitor, catálogos)",
        "test_command": "npm run lint",
        "build_command": "npm run build",
        "deploy": "Docker (nginx), AWS CodeBuild → ECR → ECS",
    },
    {
        "key": "covaf-derechos",
        "name": "ServicioDerechos",
        "path": "covaf/ServicioDerechos",
        "language": "Python",
        "framework": "Flask + Lambda",
        "domain": "Servicio de Derechos",
        "test_command": "unverified",
        "build_command": "unverified",
        "deploy": "unverified",
    },
]


def lifecycle_list_components(workspace: Path) -> dict[str, Any]:
    """Lista todos los componentes COVAF con su metadata."""
    verified: list[dict[str, Any]] = []
    for c in COMPONENTS:
        full = workspace / c["path"]
        v = dict(c)
        v["exists"] = full.exists()
        v["has_git"] = (full / ".git").exists() if full.exists() else False
        verified.append(v)
    return {"components": verified, "count": len(verified)}


def lifecycle_get_status(workspace: Path) -> dict[str, Any]:
    """Retorna el estado consolidado de todos los componentes COVAF."""
    statuses: list[dict[str, Any]] = []
    for c in COMPONENTS:
        full = workspace / c["path"]
        status: dict[str, Any] = {"key": c["key"], "name": c["name"]}
        if not full.exists():
            status["status"] = "missing"
            status["exists"] = False
        else:
            status["exists"] = True
            status["has_git"] = (full / ".git").exists()
            # Verificar si hay cambios sin commitear
            if status["has_git"]:
                try:
                    result = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=str(full),
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    dirty = len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
                    status["dirty_files"] = dirty
                    status["status"] = "dirty" if dirty > 0 else "clean"
                except (subprocess.TimeoutExpired, OSError):
                    status["status"] = "unverified"
            else:
                status["status"] = "no_git"
        statuses.append(status)
    return {"components": statuses, "count": len(statuses)}


def lifecycle_get_git_info(workspace: Path, component_key: str) -> dict[str, Any]:
    """Obtiene información de Git para un componente específico."""
    comp = next((c for c in COMPONENTS if c["key"] == component_key), None)
    if comp is None:
        raise McpError(f"Componente desconocido: {component_key}")
    full = workspace / comp["path"]
    if not full.exists() or not (full / ".git").exists():
        raise McpError(f"Git no disponible para {component_key}")
    info: dict[str, Any] = {"key": component_key}
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h %s %cI"],
            cwd=str(full), capture_output=True, text=True, timeout=10,
        )
        info["head"] = result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError) as exc:
        info["error"] = str(exc)
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(full), capture_output=True, text=True, timeout=10,
        )
        dirty = result.stdout.strip().splitlines() if result.stdout.strip() else []
        info["dirty_files"] = len(dirty)
        info["dirty_list"] = [d.strip() for d in dirty[:10]]
    except (subprocess.TimeoutExpired, OSError) as exc:
        info["error"] = str(exc)
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(full), capture_output=True, text=True, timeout=10,
        )
        info["branch"] = result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        info["branch"] = "unverified"
    return info


def lifecycle_get_dependencies(workspace: Path, component_key: str) -> dict[str, Any]:
    """Obtiene las dependencias clave de un componente."""
    comp = next((c for c in COMPONENTS if c["key"] == component_key), None)
    if comp is None:
        raise McpError(f"Componente desconocido: {component_key}")
    full = workspace / comp["path"]
    if not full.exists():
        raise McpError(f"Componente no encontrado: {component_key}")
    deps: dict[str, Any] = {"key": component_key, "dependencies": []}
    if component_key == "covaf-back":
        pom = full / "pom.xml"
        if pom.exists():
            text = pom.read_text(encoding="utf-8", errors="ignore")
            import re
            for m in re.finditer(r"<artifactId>([^<]+)</artifactId>", text):
                deps["dependencies"].append(m.group(1))
    elif component_key == "covaf-ia":
        req = full / "requirements.txt"
        if req.exists():
            for line in req.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    deps["dependencies"].append(line)
    elif component_key == "covaf-front":
        pkg = full / "package.json"
        if pkg.exists():
            import json
            data = json.loads(pkg.read_text(encoding="utf-8", errors="ignore"))
            deps["dependencies"] = list(data.get("dependencies", {}).keys())
            deps["dev_dependencies"] = list(data.get("devDependencies", {}).keys())
    return deps


def lifecycle_get_test_command(workspace: Path, component_key: str) -> dict[str, Any]:
    """Retorna el comando de test para un componente."""
    comp = next((c for c in COMPONENTS if c["key"] == component_key), None)
    if comp is None:
        raise McpError(f"Componente desconocido: {component_key}")
    return {
        "key": component_key,
        "test_command": comp["test_command"],
        "build_command": comp["build_command"],
        "language": comp["language"],
        "framework": comp["framework"],
    }


def lifecycle_get_deploy_manifests(workspace: Path, component_key: str) -> dict[str, Any]:
    """Lista los manifests de despliegue de un componente."""
    comp = next((c for c in COMPONENTS if c["key"] == component_key), None)
    if comp is None:
        raise McpError(f"Componente desconocido: {component_key}")
    full = workspace / comp["path"]
    if not full.exists():
        raise McpError(f"Componente no encontrado: {component_key}")
    manifests: list[str] = []
    for name in ["Dockerfile", "Dockerfile.local", "docker-compose.yml",
                 "docker-compose.local.yml", "buildspec.yml", ".github/workflows"]:
        f = full / name
        if f.exists():
            manifests.append(name)
    return {
        "key": component_key,
        "manifests": manifests,
        "deploy_info": comp["deploy"],
    }
