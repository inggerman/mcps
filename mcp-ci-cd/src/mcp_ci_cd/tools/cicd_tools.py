"""
Lógica de negocio de mcp-ci-cd.

Ejecuta un flujo simplificado de CI/CD (lint, test, deploy).
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any


def _run_stage(cmd: str, cwd: Path, stage_name: str) -> dict[str, Any]:
    """Ejecuta una fase del pipeline."""
    try:
        args = shlex.split(cmd)
        result = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        success = result.returncode == 0
        output = result.stdout.strip()
        if result.stderr.strip():
            output += f"\n{result.stderr.strip()}"

        return {
            "stage": stage_name,
            "success": success,
            "output": output[:1000] + ("..." if len(output) > 1000 else ""),
        }
    except Exception as exc:
        return {"stage": stage_name, "success": False, "output": f"Fallo al ejecutar: {exc}"}


def run_pipeline(
    project_path: Path, lint_cmd: str, test_cmd: str, deploy_cmd: str
) -> dict[str, Any]:
    """Ejecuta un pipeline CI/CD completo secuencialmente."""
    stages = []

    # 1. Lint
    lint_res = _run_stage(lint_cmd, project_path, "lint")
    stages.append(lint_res)
    if not lint_res["success"]:
        return {"status": "failed_at_lint", "stages": stages}

    # 2. Test
    test_res = _run_stage(test_cmd, project_path, "test")
    stages.append(test_res)
    if not test_res["success"]:
        return {"status": "failed_at_test", "stages": stages}

    # 3. Deploy
    deploy_res = _run_stage(deploy_cmd, project_path, "deploy")
    stages.append(deploy_res)
    if not deploy_res["success"]:
        return {"status": "failed_at_deploy", "stages": stages}

    return {"status": "success", "stages": stages}


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def run_lint(project_path: Path, cmd: str) -> dict[str, Any]:
    """Ejecuta solo la fase de linting."""
    return _run_stage(cmd, project_path, "lint")


def run_tests(project_path: Path, cmd: str) -> dict[str, Any]:
    """Ejecuta solo la fase de tests."""
    return _run_stage(cmd, project_path, "test")


def run_security_scan(project_path: Path, cmd: str = "python -c 'print(\"security scan placeholder\")'") -> dict[str, Any]:
    """Ejecuta un scan de seguridad."""
    return _run_stage(cmd, project_path, "security")


def validate_ci_config(project_path: Path) -> dict[str, Any]:
    """Valida la configuracion de CI/CD del proyecto."""
    results: list[dict[str, Any]] = []

    configs = [
        (".github/workflows", "GitHub Actions"),
        (".gitlab-ci.yml", "GitLab CI"),
        ("Jenkinsfile", "Jenkins"),
        (".circleci/config.yml", "CircleCI"),
        ("azure-pipelines.yml", "Azure Pipelines"),
    ]

    for path, name in configs:
        full_path = project_path / path
        exists = full_path.exists()
        results.append({"platform": name, "path": path, "exists": exists})

    found_platforms = [r for r in results if r["exists"]]

    return {
        "configs_found": len(found_platforms),
        "platforms": results,
        "has_ci": len(found_platforms) > 0,
    }


def generate_workflow(platform: str, project_name: str = "mcp-project") -> str:
    """Genera un archivo de workflow para la plataforma especificada."""
    if platform.lower() == "github":
        return "\n".join([
            "name: CI",
            f"on: [push, pull_request]",
            "jobs:",
            "  ci:",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - uses: actions/checkout@v4",
            "      - uses: actions/setup-python@v5",
            "        with:",
            "          python-version: '3.12'",
            "      - run: pip install uv",
            "      - run: uv pip install --system -e .",
            "      - run: uv run ruff check .",
            "      - run: uv run pytest -v",
        ])
    elif platform.lower() == "gitlab":
        return "\n".join([
            "stages:",
            "  - lint",
            "  - test",
            "  - deploy",
            "",
            "lint:",
            "  stage: lint",
            "  script:",
            "    - pip install uv",
            f"    - uv run ruff check .",
            "",
            "test:",
            "  stage: test",
            "  script:",
            "    - pip install uv",
            f"    - uv run pytest -v",
            "",
            "deploy:",
            "  stage: deploy",
            "  script:",
            f"    - echo 'Deploying {project_name}'",
            "  only:",
            "    - main",
        ])
    elif platform.lower() == "jenkins":
        return "\n".join([
            "pipeline {",
            "  agent any",
            "  stages {",
            "    stage('Lint') {",
            "      steps {",
            "        sh 'ruff check .'",
            "      }",
            "    }",
            "    stage('Test') {",
            "      steps {",
            "        sh 'pytest -v'",
            "      }",
            "    }",
            "    stage('Deploy') {",
            "      steps {",
            f"        echo 'Deploying {project_name}'",
            "      }",
            "    }",
            "  }",
            "}",
        ])
    else:
        return f"# Platform '{platform}' not supported. Use: github, gitlab, jenkins"


def list_pipeline_stages() -> list[dict[str, Any]]:
    """Lista las stages disponibles en el pipeline."""
    return [
        {"stage": "lint", "description": "Code linting with ruff", "order": 1},
        {"stage": "test", "description": "Run tests with pytest", "order": 2},
        {"stage": "security", "description": "Security scanning", "order": 3},
        {"stage": "build", "description": "Build artifacts", "order": 4},
        {"stage": "deploy", "description": "Deploy to environment", "order": 5},
    ]


def check_dependencies(project_path: Path) -> dict[str, Any]:
    """Verifica que las dependencias del proyecto esten instaladas."""
    pyproject = project_path / "pyproject.toml"
    if not pyproject.exists():
        return {"found": False, "dependencies": []}

    deps: list[str] = []
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

    return {
        "found": True,
        "total_dependencies": len(deps),
        "dependencies": deps,
    }


def generate_docker_compose(project_path: Path) -> str:
    """Genera un docker-compose.yml basico para CI/CD."""
    servers = sorted([d.name for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-")])

    lines = ["services:"]
    port = 8001
    for srv in servers:
        lines.extend([
            f"  {srv}:",
            f"    build: ./{srv}",
            f"    ports:",
            f"      - \"{port}:8000\"",
            f"    env_file: ./{srv}/.env",
            f"    restart: unless-stopped",
            "",
        ])
        port += 1

    return "\n".join(lines)


def analyze_pipeline_health(project_path: Path) -> dict[str, Any]:
    """Analiza la salud del pipeline revisando configuracion."""
    config_check = validate_ci_config(project_path)
    dep_check = check_dependencies(project_path)

    has_dockerfile = any((project_path / d / "Dockerfile").exists() for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-"))
    has_tests = any((project_path / d / "tests").exists() for d in project_path.iterdir() if d.is_dir() and d.name.startswith("mcp-"))

    checks = {
        "has_ci_config": config_check["has_ci"],
        "has_dependencies": dep_check["found"],
        "has_dockerfiles": has_dockerfile,
        "has_tests": has_tests,
    }

    score = sum(checks.values()) / len(checks) * 100

    return {
        "health_score": round(score, 2),
        "checks": checks,
        "recommendations": [
            "Add CI/CD config" if not checks["has_ci_config"] else None,
            "Add pyproject.toml" if not checks["has_dependencies"] else None,
            "Add Dockerfiles" if not checks["has_dockerfiles"] else None,
            "Add tests" if not checks["has_tests"] else None,
        ],
    }


def generate_makefile(project_path: Path) -> str:
    """Genera un Makefile basico para el proyecto."""
    return "\n".join([
        ".PHONY: install lint test build deploy clean",
        "",
        "install:",
        "\tuv pip install --system -e .",
        "",
        "lint:",
        "\tuv run ruff check .",
        "\tuv run ruff format --check .",
        "",
        "test:",
        "\tuv run pytest -v",
        "",
        "build:",
        "\tdocker compose build",
        "",
        "deploy:",
        "\tdocker compose up -d",
        "",
        "clean:",
        "\trm -rf .pytest_cache __pycache__",
        "",
    ])


def check_secrets(project_path: Path) -> dict[str, Any]:
    """Escanea basicamente el proyecto en busca de posibles secrets expuestos."""
    suspicious_patterns = ["api_key", "secret", "password", "token", "private_key"]
    findings: list[dict[str, Any]] = []

    for f in project_path.rglob("*.py"):
        if any(part.startswith(".") for part in f.parts):
            continue
        if "__pycache__" in f.parts:
            continue
        try:
            content = f.read_text(encoding="utf-8")
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                lower = line.lower()
                for pattern in suspicious_patterns:
                    if pattern in lower and "=" in line and not line.strip().startswith("#"):
                        if not any(x in line for x in ["getenv", "environ", "os.getenv", "settings.", "Field("]):
                            findings.append({
                                "file": str(f.relative_to(project_path)),
                                "line": i,
                                "pattern": pattern,
                                "content": line.strip()[:100],
                            })
        except Exception:
            continue

    return {
        "total_findings": len(findings),
        "findings": findings[:50],
        "clean": len(findings) == 0,
    }


def generate_pre_commit_hook() -> str:
    """Genera una configuracion .pre-commit-config.yaml basica."""
    return "\n".join([
        "repos:",
        "  - repo: https://github.com/astral-sh/ruff-pre-commit",
        "    rev: v0.5.0",
        "    hooks:",
        "      - id: ruff",
        "        args: [--fix]",
        "      - id: ruff-format",
        "",
        "  - repo: https://github.com/pre-commit/pre-commit-hooks",
        "    rev: v4.6.0",
        "    hooks:",
        "      - id: trailing-whitespace",
        "      - id: end-of-file-fixer",
        "      - id: check-yaml",
        "      - id: check-added-large-files",
        "",
    ])


def get_pipeline_status(project_path: Path) -> dict[str, Any]:
    """Retorna el estado actual del pipeline."""
    config_check = validate_ci_config(project_path)
    dep_check = check_dependencies(project_path)
    secret_check = check_secrets(project_path)

    return {
        "ci_configured": config_check["has_ci"],
        "platforms": [r["platform"] for r in config_check["platforms"] if r["exists"]],
        "dependencies_count": dep_check.get("total_dependencies", 0),
        "secrets_clean": secret_check["clean"],
        "secrets_found": secret_check["total_findings"],
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }


def export_pipeline_config(project_path: Path) -> dict[str, Any]:
    """Exporta la configuracion completa del pipeline."""
    config_check = validate_ci_config(project_path)
    dep_check = check_dependencies(project_path)
    health = analyze_pipeline_health(project_path)

    return {
        "ci_platforms": [r for r in config_check["platforms"] if r["exists"]],
        "dependencies": dep_check.get("dependencies", []),
        "health_score": health["health_score"],
        "checks": health["checks"],
        "recommendations": [r for r in health["recommendations"] if r is not None],
    }
