"""
Servidor FastMCP para mcp-java-build.

Expone comandos Maven y Gradle.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_java_build import __version__
from mcp_java_build.config import settings
from mcp_java_build.tools import (
    java_gradle_boot_run,
    java_gradle_build,
    java_gradle_clean_build,
    java_gradle_cmd,
    java_gradle_dependencies,
    java_gradle_test,
    java_list_gradle,
    java_list_pom,
    java_maven_clean,
    java_maven_cmd,
    java_maven_compile,
    java_maven_dependency_tree,
    java_maven_install,
    java_maven_package,
    java_maven_test,
)
from mcp_java_build import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-java-build",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-java-build")
    logger.info(
        "mcp-java-build iniciando",
        version=__version__,
        project_path=str(settings.project_path),
    )
    yield
    logger.info("mcp-java-build detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-java-build",
    instructions=(
        "Servidor MCP para ecosistemas Java. "
        "Úsalo para ejecutar comandos de Maven (`mvn`) o Gradle (`gradlew`)."
    ),
    lifespan=lifespan,
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__, error=str(exc))
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de Java Build.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="java_mvn",
    description="Ejecuta un comando Maven en el proyecto. Provee los argumentos (ej. 'clean install')."
)
def tool_java_mvn(args: str) -> dict[str, Any]:
    logger.info("java_mvn llamado", args=args)
    return _handle(java_maven_cmd, settings.project_path, args)


@mcp.tool(
    name="java_gradle",
    description="Ejecuta un comando Gradle en el proyecto. Provee los argumentos (ej. 'build')."
)
def tool_java_gradle(args: str) -> dict[str, Any]:
    logger.info("java_gradle llamado", args=args)
    return _handle(java_gradle_cmd, settings.project_path, args)


@mcp.tool(name="java_maven_clean", description="Ejecuta mvn clean.")
def tool_java_maven_clean() -> dict[str, Any]:
    return _handle(java_maven_clean, settings.project_path)


@mcp.tool(name="java_maven_compile", description="Ejecuta mvn compile.")
def tool_java_maven_compile() -> dict[str, Any]:
    return _handle(java_maven_compile, settings.project_path)


@mcp.tool(name="java_maven_test", description="Ejecuta mvn test.")
def tool_java_maven_test() -> dict[str, Any]:
    return _handle(java_maven_test, settings.project_path)


@mcp.tool(name="java_maven_package", description="Ejecuta mvn package.")
def tool_java_maven_package(skip_tests: bool = False) -> dict[str, Any]:
    return _handle(java_maven_package, settings.project_path, skip_tests)


@mcp.tool(name="java_maven_install", description="Ejecuta mvn install.")
def tool_java_maven_install(skip_tests: bool = False) -> dict[str, Any]:
    return _handle(java_maven_install, settings.project_path, skip_tests)


@mcp.tool(name="java_maven_dependency_tree", description="Ejecuta mvn dependency:tree.")
def tool_java_maven_dependency_tree() -> dict[str, Any]:
    return _handle(java_maven_dependency_tree, settings.project_path)


@mcp.tool(name="java_gradle_build", description="Ejecuta gradle build.")
def tool_java_gradle_build() -> dict[str, Any]:
    return _handle(java_gradle_build, settings.project_path)


@mcp.tool(name="java_gradle_test", description="Ejecuta gradle test.")
def tool_java_gradle_test() -> dict[str, Any]:
    return _handle(java_gradle_test, settings.project_path)


@mcp.tool(name="java_gradle_clean_build", description="Ejecuta gradle clean build.")
def tool_java_gradle_clean_build() -> dict[str, Any]:
    return _handle(java_gradle_clean_build, settings.project_path)


@mcp.tool(name="java_gradle_dependencies", description="Ejecuta gradle dependencies.")
def tool_java_gradle_dependencies() -> dict[str, Any]:
    return _handle(java_gradle_dependencies, settings.project_path)


@mcp.tool(name="java_gradle_boot_run", description="Ejecuta gradle bootRun (Spring Boot).")
def tool_java_gradle_boot_run() -> dict[str, Any]:
    return _handle(java_gradle_boot_run, settings.project_path)


@mcp.tool(name="java_list_pom", description="Lista archivos pom.xml en el proyecto.")
def tool_java_list_pom() -> dict[str, Any]:
    return _handle(java_list_pom, settings.project_path)


@mcp.tool(name="java_list_gradle", description="Lista archivos build.gradle en el proyecto.")
def tool_java_list_gradle() -> dict[str, Any]:
    return _handle(java_list_gradle, settings.project_path)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("java://configuration")
def res_config() -> str:
    return res.java_configuration()


@mcp.resource("java://basics")
def res_basics() -> str:
    return res.java_basics()


@mcp.resource("java://best-practices")
def res_best() -> str:
    return res.java_best_practices()


@mcp.resource("java://quick-reference")
def res_quick() -> str:
    return res.java_quick_reference()


@mcp.resource("java://error-codes")
def res_errors() -> str:
    return res.java_error_codes()


@mcp.resource("java://troubleshooting")
def res_trouble() -> str:
    return res.java_troubleshooting()


@mcp.resource("java://examples")
def res_examples() -> str:
    return res.java_examples()


@mcp.resource("java://maven-guide")
def res_maven() -> str:
    return res.java_maven_guide()


@mcp.resource("java://gradle-guide")
def res_gradle() -> str:
    return res.java_gradle_guide()


@mcp.resource("java://testing")
def res_testing() -> str:
    return res.java_testing()


@mcp.resource("java://dependencies")
def res_deps() -> str:
    return res.java_dependencies()


@mcp.resource("java://multi-module")
def res_multi() -> str:
    return res.java_multi_module()


@mcp.resource("java://ci-cd")
def res_cicd() -> str:
    return res.java_ci_cd()


@mcp.resource("java://spring-boot")
def res_spring() -> str:
    return res.java_spring_boot()


@mcp.resource("java://performance")
def res_perf() -> str:
    return res.java_performance()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")
