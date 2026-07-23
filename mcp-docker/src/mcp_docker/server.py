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
    container_inspect,
    container_logs,
    container_pause,
    container_restart,
    container_unpause,
    containers_list,
    containers_stats,
    image_inspect,
    image_pull,
    image_remove,
    images_list,
    network_create,
    network_list,
    network_remove,
    run_container,
    stop_container,
    volume_create,
    volume_list,
    volume_remove,
)
from mcp_docker import resources as res

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
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="image_remove",
    description="Elimina una imagen Docker local. Parametros: image_id (ID o nombre), force (bool).",
)
def tool_image_remove(image_id: str, force: bool = False) -> dict[str, Any]:
    logger.info("image_remove llamado", image_id=image_id)
    return _handle(image_remove, image_id=image_id, force=force)


@mcp.tool(
    name="image_inspect",
    description="Inspecciona una imagen Docker retornando metadatos completos. Parametros: image_id (ID o nombre).",
)
def tool_image_inspect(image_id: str) -> dict[str, Any]:
    logger.info("image_inspect llamado", image_id=image_id)
    return _handle(image_inspect, image_id=image_id)


@mcp.tool(
    name="network_list",
    description="Lista redes Docker. Retorna: networks[], count.",
)
def tool_network_list() -> dict[str, Any]:
    logger.info("network_list llamado")
    return _handle(network_list)


@mcp.tool(
    name="network_create",
    description="Crea una red Docker. Parametros: name (requerido), driver (default 'bridge').",
)
def tool_network_create(name: str, driver: str = "bridge") -> dict[str, Any]:
    logger.info("network_create llamado", name=name)
    return _handle(network_create, name=name, driver=driver)


@mcp.tool(
    name="network_remove",
    description="Elimina una red Docker. Parametros: network_id (ID o nombre).",
)
def tool_network_remove(network_id: str) -> dict[str, Any]:
    logger.info("network_remove llamado", network_id=network_id)
    return _handle(network_remove, network_id=network_id)


@mcp.tool(
    name="volume_list",
    description="Lista volumenes Docker. Retorna: volumes[], count.",
)
def tool_volume_list() -> dict[str, Any]:
    logger.info("volume_list llamado")
    return _handle(volume_list)


@mcp.tool(
    name="volume_create",
    description="Crea un volumen Docker. Parametros: name (requerido), driver (default 'local').",
)
def tool_volume_create(name: str, driver: str = "local") -> dict[str, Any]:
    logger.info("volume_create llamado", name=name)
    return _handle(volume_create, name=name, driver=driver)


@mcp.tool(
    name="volume_remove",
    description="Elimina un volumen Docker. Parametros: volume_name (nombre), force (bool).",
)
def tool_volume_remove(volume_name: str, force: bool = False) -> dict[str, Any]:
    logger.info("volume_remove llamado", volume_name=volume_name)
    return _handle(volume_remove, volume_name=volume_name, force=force)


@mcp.tool(
    name="container_inspect",
    description="Inspecciona un contenedor retornando metadatos completos. Parametros: container_id.",
)
def tool_container_inspect(container_id: str) -> dict[str, Any]:
    logger.info("container_inspect llamado", container_id=container_id)
    return _handle(container_inspect, container_id=container_id)


@mcp.tool(
    name="container_restart",
    description="Reinicia un contenedor. Parametros: container_id, timeout (segundos, default 10).",
)
def tool_container_restart(container_id: str, timeout: int = 10) -> dict[str, Any]:
    logger.info("container_restart llamado", container_id=container_id)
    return _handle(container_restart, container_id=container_id, timeout=timeout)


@mcp.tool(
    name="container_pause",
    description="Pausa un contenedor en ejecucion. Parametros: container_id.",
)
def tool_container_pause(container_id: str) -> dict[str, Any]:
    logger.info("container_pause llamado", container_id=container_id)
    return _handle(container_pause, container_id=container_id)


@mcp.tool(
    name="container_unpause",
    description="Reanuda un contenedor pausado. Parametros: container_id.",
)
def tool_container_unpause(container_id: str) -> dict[str, Any]:
    logger.info("container_unpause llamado", container_id=container_id)
    return _handle(container_unpause, container_id=container_id)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("docker://configuration")
def res_config() -> str:
    return res.docker_configuration()


@mcp.resource("docker://container-statuses")
def res_statuses() -> str:
    return res.docker_container_statuses()


@mcp.resource("docker://image-reference")
def res_images() -> str:
    return res.docker_image_reference()


@mcp.resource("docker://run-guide")
def res_run() -> str:
    return res.docker_run_guide()


@mcp.resource("docker://logs-guide")
def res_logs() -> str:
    return res.docker_logs_guide()


@mcp.resource("docker://exec-guide")
def res_exec() -> str:
    return res.docker_exec_guide()


@mcp.resource("docker://stats-guide")
def res_stats() -> str:
    return res.docker_stats_guide()


@mcp.resource("docker://best-practices")
def res_best() -> str:
    return res.docker_best_practices()


@mcp.resource("docker://network-guide")
def res_net() -> str:
    return res.docker_network_guide()


@mcp.resource("docker://volume-guide")
def res_vol() -> str:
    return res.docker_volume_guide()


@mcp.resource("docker://compose-guide")
def res_compose() -> str:
    return res.docker_compose_guide()


@mcp.resource("docker://error-codes")
def res_errors() -> str:
    return res.docker_error_codes()


@mcp.resource("docker://security-tips")
def res_sec() -> str:
    return res.docker_security_tips()


@mcp.resource("docker://troubleshooting")
def res_trouble() -> str:
    return res.docker_troubleshooting()


@mcp.resource("docker://quick-reference")
def res_quick() -> str:
    return res.docker_quick_reference()


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
