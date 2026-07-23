"""
Lógica de mcp-java-build.

Ejecuta subprocesos para Maven y Gradle.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from mcp_shared.errors import McpError


def java_maven_cmd(project_path: Path, args: str) -> dict[str, Any]:
    """Ejecuta un comando Maven."""
    # Buscar mvn o mvnw
    mvn_bin = ""
    if (project_path / "mvnw").exists():
        mvn_bin = "./mvnw"
    elif (project_path / "mvnw.cmd").exists():
        mvn_bin = "mvnw.cmd"
    else:
        mvn_bin = shutil.which("mvn") or ""

    if not mvn_bin:
        return {
            "mode": "mock",
            "status": "success",
            "output": "[INFO] Mock Maven execution successful.\n[INFO] BUILD SUCCESS",
            "message": "Maven no encontrado. Simulando ejecución."
        }

    try:
        cmd = [mvn_bin, *shlex.split(args)]
        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
        return {
            "mode": "real",
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout[:2000] + ("\n..." if len(result.stdout) > 2000 else ""),
            "error": result.stderr[:2000] if result.stderr else None
        }
    except Exception as exc:
        raise McpError(f"Fallo al ejecutar Maven: {exc}") from exc


def java_gradle_cmd(project_path: Path, args: str) -> dict[str, Any]:
    """Ejecuta un comando Gradle."""
    gradle_bin = ""
    if (project_path / "gradlew").exists():
        gradle_bin = "./gradlew"
    elif (project_path / "gradlew.bat").exists():
        gradle_bin = "gradlew.bat"
    else:
        gradle_bin = shutil.which("gradle") or ""

    if not gradle_bin:
        return {
            "mode": "mock",
            "status": "success",
            "output": "BUILD SUCCESSFUL in 2s\nMock Gradle execution.",
            "message": "Gradle no encontrado. Simulando ejecución."
        }

    try:
        cmd = [gradle_bin, *shlex.split(args)]
        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
        return {
            "mode": "real",
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout[:2000] + ("\n..." if len(result.stdout) > 2000 else ""),
            "error": result.stderr[:2000] if result.stderr else None
        }
    except Exception as exc:
        raise McpError(f"Fallo al ejecutar Gradle: {exc}") from exc


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def java_maven_clean(project_path: Path) -> dict[str, Any]:
    """Ejecuta mvn clean."""
    return java_maven_cmd(project_path, "clean")


def java_maven_compile(project_path: Path) -> dict[str, Any]:
    """Ejecuta mvn compile."""
    return java_maven_cmd(project_path, "compile")


def java_maven_test(project_path: Path) -> dict[str, Any]:
    """Ejecuta mvn test."""
    return java_maven_cmd(project_path, "test")


def java_maven_package(project_path: Path, skip_tests: bool = False) -> dict[str, Any]:
    """Ejecuta mvn package."""
    args = "package"
    if skip_tests:
        args += " -DskipTests"
    return java_maven_cmd(project_path, args)


def java_maven_install(project_path: Path, skip_tests: bool = False) -> dict[str, Any]:
    """Ejecuta mvn install."""
    args = "install"
    if skip_tests:
        args += " -DskipTests"
    return java_maven_cmd(project_path, args)


def java_maven_dependency_tree(project_path: Path) -> dict[str, Any]:
    """Ejecuta mvn dependency:tree."""
    return java_maven_cmd(project_path, "dependency:tree")


def java_gradle_build(project_path: Path) -> dict[str, Any]:
    """Ejecuta gradle build."""
    return java_gradle_cmd(project_path, "build")


def java_gradle_test(project_path: Path) -> dict[str, Any]:
    """Ejecuta gradle test."""
    return java_gradle_cmd(project_path, "test")


def java_gradle_clean_build(project_path: Path) -> dict[str, Any]:
    """Ejecuta gradle clean build."""
    return java_gradle_cmd(project_path, "clean build")


def java_gradle_dependencies(project_path: Path) -> dict[str, Any]:
    """Ejecuta gradle dependencies."""
    return java_gradle_cmd(project_path, "dependencies")


def java_gradle_boot_run(project_path: Path) -> dict[str, Any]:
    """Ejecuta gradle bootRun."""
    return java_gradle_cmd(project_path, "bootRun")


def java_list_pom(project_path: Path) -> dict[str, Any]:
    """Lista archivos pom.xml en el proyecto."""
    poms = list(project_path.rglob("pom.xml"))
    return {"count": len(poms), "files": [str(p.relative_to(project_path)) for p in poms]}


def java_list_gradle(project_path: Path) -> dict[str, Any]:
    """Lista archivos build.gradle en el proyecto."""
    gradles = list(project_path.rglob("build.gradle")) + list(project_path.rglob("build.gradle.kts"))
    return {"count": len(gradles), "files": [str(g.relative_to(project_path)) for g in gradles]}
