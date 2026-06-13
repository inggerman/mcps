"""Servidor FastMCP para mcp-docker."""

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

from mcp_docker.config import settings
from mcp_docker.tools import (
    container_exec,
    container_logs,
    containers_list,
    containers_stats,
    image_pull,
    images_list,
    run_container,
    stop_container,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-docker",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-docker")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()


mcp = FastMCP(
    name="mcp-docker",
    instructions=(
        "Servidor MCP para gestión de Docker. "
        "Herramientas: containers_list, containers_stats, container_logs, container_exec, "
        "run_container, stop_container, images_list, image_pull. "
        "Requiere acceso al daemon Docker (socket o TCP). "
        "Ideal para inspeccionar y operar contenedores en entornos de desarrollo, "
        "CI/CD, Kubernetes local (Docker Desktop) y aplicaciones Compose."
    ),
    lifespan=lifespan,
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Wrapper común de manejo de errores para todos los tools."""
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__, exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="containers_list",
    description=(
        "Lista contenedores Docker. "
        "Parámetros: all_containers (bool, default false = solo running), "
        'filters (dict opcional, ej: {"name": "web", "status": "running"}). '
        "Retorna: containers[], count, showing."
    ),
)
def tool_containers_list(
    all_containers: bool = False,
    filters: dict[str, str] | None = None,
) -> dict[str, Any]:
    logger.info("containers_list llamado", all_containers=all_containers)
    result = _handle(containers_list, all_containers=all_containers, filters=filters)
    logger.info("containers_list completado", count=result["count"])
    return result


@mcp.tool(
    name="containers_stats",
    description=(
        "Estadísticas de recursos de un contenedor: CPU %, memoria MB, red, disco. "
        "Parámetros: container_id (ID o nombre, requerido). "
        "Retorna: cpu_percent, memory_mb, memory_limit_mb, memory_percent, "
        "net_rx_mb, net_tx_mb, block_read_mb, block_write_mb."
    ),
)
def tool_containers_stats(container_id: str) -> dict[str, Any]:
    logger.info("containers_stats llamado", container_id=container_id)
    result = _handle(containers_stats, container_id=container_id)
    logger.info("containers_stats completado", container_id=container_id, cpu=result["cpu_percent"])
    return result


@mcp.tool(
    name="container_logs",
    description=(
        "Obtiene los logs de un contenedor. "
        "Parámetros: container_id (requerido), lines (int, default 100), "
        "since (str opcional, ej: '1h', '30m', '2024-01-01T10:00:00'), "
        "timestamps (bool, default false). "
        "Retorna: logs (texto), container_id, container_name, lines_requested, status."
    ),
)
def tool_container_logs(
    container_id: str,
    lines: int | None = None,
    since: str | None = None,
    timestamps: bool = False,
) -> dict[str, Any]:
    logger.info("container_logs llamado", container_id=container_id, lines=lines)
    result = _handle(
        container_logs, container_id=container_id, lines=lines, since=since, timestamps=timestamps
    )
    logger.info("container_logs completado", container_id=container_id)
    return result


@mcp.tool(
    name="container_exec",
    description=(
        "Ejecuta un comando dentro de un contenedor en ejecución (debe estar running). "
        "Parámetros: container_id (requerido), command (string, requerido), "
        "workdir (string opcional), user (string opcional, ej: 'root'), "
        "environment (dict opcional). "
        "Retorna: exit_code, output, success, container_id, command."
    ),
)
def tool_container_exec(
    container_id: str,
    command: str,
    workdir: str | None = None,
    user: str | None = None,
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    logger.info("container_exec llamado", container_id=container_id, command=command)
    result = _handle(
        container_exec,
        container_id=container_id,
        command=command,
        workdir=workdir,
        user=user,
        environment=environment,
    )
    logger.info(
        "container_exec completado", container_id=container_id, exit_code=result["exit_code"]
    )
    return result


@mcp.tool(
    name="run_container",
    description=(
        "Crea y arranca un contenedor Docker. "
        "Parámetros: image (requerido, ej: 'nginx:latest'), command (string opcional), "
        "name (string opcional), detach (bool, default true = background), "
        "ports (dict container→host, ej: {'80': '8080'}), "
        "environment (dict), volumes (dict host_path→container_path), "
        "remove_on_exit (bool, default false). "
        "Retorna: id, name, status, image, ports."
    ),
)
def tool_run_container(
    image: str,
    command: str | None = None,
    name: str | None = None,
    detach: bool = True,
    ports: dict[str, str] | None = None,
    environment: dict[str, str] | None = None,
    volumes: dict[str, str] | None = None,
    remove_on_exit: bool = False,
) -> dict[str, Any]:
    logger.info("run_container llamado", image=image, name=name, detach=detach)
    result = _handle(
        run_container,
        image=image,
        command=command,
        name=name,
        detach=detach,
        ports=ports,
        environment=environment,
        volumes=volumes,
        remove_on_exit=remove_on_exit,
    )
    logger.info("run_container completado", image=image, status=result.get("status"))
    return result


@mcp.tool(
    name="stop_container",
    description=(
        "Detiene un contenedor Docker en ejecución. "
        "Parámetros: container_id (ID o nombre, requerido), "
        "timeout (int segundos antes de SIGKILL, default 10), "
        "remove (bool, si True elimina tras detener, default false). "
        "Retorna: container_id, name, action, removed."
    ),
)
def tool_stop_container(
    container_id: str,
    timeout: int = 10,
    remove: bool = False,
) -> dict[str, Any]:
    logger.info("stop_container llamado", container_id=container_id, remove=remove)
    result = _handle(stop_container, container_id=container_id, timeout=timeout, remove=remove)
    logger.info("stop_container completado", container_id=container_id, action=result["action"])
    return result


@mcp.tool(
    name="images_list",
    description=(
        "Lista imágenes Docker locales. "
        "Parámetros: name (string opcional, filtrar por nombre/tag), "
        "dangling (bool, incluir imágenes sin tag, default false). "
        "Retorna: images[], count."
    ),
)
def tool_images_list(
    name: str | None = None,
    dangling: bool = False,
) -> dict[str, Any]:
    logger.info("images_list llamado", name=name)
    result = _handle(images_list, name=name, dangling=dangling)
    logger.info("images_list completado", count=result["count"])
    return result


@mcp.tool(
    name="image_pull",
    description=(
        "Descarga una imagen Docker desde un registry (Docker Hub, ECR, GHCR, etc.). "
        "Parámetros: image (requerido, ej: 'nginx', 'python', 'my-registry/app'), "
        "tag (string, default 'latest'). "
        "Retorna: image, tag, id, tags[], size_mb."
    ),
)
def tool_image_pull(
    image: str,
    tag: str = "latest",
) -> dict[str, Any]:
    logger.info("image_pull llamado", image=image, tag=tag)
    result = _handle(image_pull, image=image, tag=tag)
    logger.info("image_pull completado", image=image, tag=tag, size_mb=result["size_mb"])
    return result


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
