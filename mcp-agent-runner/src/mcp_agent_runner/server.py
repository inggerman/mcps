"""
Servidor FastMCP para mcp-agent-runner.

Orquesta la delegación de tareas a sub-agentes.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_agent_runner import __version__
from mcp_agent_runner.config import settings
from mcp_agent_runner.tools import (
    agent_cancel,
    agent_create_task,
    agent_delete_task,
    agent_get_config,
    agent_health_check,
    agent_list_scripts,
    agent_list_tasks,
    agent_logs,
    agent_results,
    agent_run_batch,
    agent_run_local,
    agent_run_with_timeout,
    agent_status,
    agent_trigger_n8n_workflow,
    agent_trigger_webhook,
)
from mcp_agent_runner import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-agent-runner",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-agent-runner")
    logger.info(
        "mcp-agent-runner iniciando",
        version=__version__,
        project_path=str(settings.project_path),
    )
    yield
    logger.info("mcp-agent-runner detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-agent-runner",
    instructions=(
        "Servidor MCP para orquestar la delegación a sub-agentes o herramientas externas. "
        "Permite disparar webhooks (ej. n8n) o correr scripts de Python en local."
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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de Agent Runner.")) from exc


async def _ahandle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return await fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__, error=str(exc))
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de Agent Runner.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="agent_trigger_webhook",
    description="Dispara un webhook REST HTTP (ej. n8n) enviando un payload en JSON."
)
async def tool_agent_trigger_webhook(payload_json: str) -> dict[str, Any]:
    logger.info("agent_trigger_webhook llamado")
    try:
        payload = json.loads(payload_json)
    except Exception as exc:
        raise SdkMcpError(ErrorData(code=-32602, message="Invalid JSON payload")) from exc

    return await _ahandle(
        agent_trigger_webhook,
        settings.n8n_webhook_base_url,
        payload,
        settings.n8n_auth_token
    )


@mcp.tool(
    name="agent_run_local_script",
    description="Ejecuta un sub-agente o script Python en local y espera su resultado."
)
def tool_agent_run_local(script_path: str, args: str = "") -> dict[str, Any]:
    logger.info("agent_run_local called", script=script_path)
    return _handle(agent_run_local, settings.project_path, script_path, args)


@mcp.tool(name="agent_list_scripts", description="Lista scripts Python disponibles en el proyecto.")
def tool_agent_list_scripts() -> dict[str, Any]:
    return _handle(agent_list_scripts, settings.project_path)


@mcp.tool(name="agent_status", description="Consulta el estado de un job por ID.")
def tool_agent_status(job_id: str) -> dict[str, Any]:
    return _handle(agent_status, job_id)


@mcp.tool(name="agent_cancel", description="Cancela un job por ID.")
def tool_agent_cancel(job_id: str) -> dict[str, Any]:
    return _handle(agent_cancel, job_id)


@mcp.tool(name="agent_logs", description="Obtiene logs de un job.")
def tool_agent_logs(job_id: str, lines: int = 50) -> dict[str, Any]:
    return _handle(agent_logs, job_id, lines)


@mcp.tool(name="agent_results", description="Obtiene resultados de un job completado.")
def tool_agent_results(job_id: str) -> dict[str, Any]:
    return _handle(agent_results, job_id)


@mcp.tool(name="agent_create_task", description="Crea una nueva tarea de agente.")
def tool_agent_create_task(name: str, description: str, script_path: str) -> dict[str, Any]:
    return _handle(agent_create_task, name, description, script_path)


@mcp.tool(name="agent_list_tasks", description="Lista tareas de agentes.")
def tool_agent_list_tasks() -> dict[str, Any]:
    return _handle(agent_list_tasks)


@mcp.tool(name="agent_delete_task", description="Elimina una tarea por ID.")
def tool_agent_delete_task(task_id: str) -> dict[str, Any]:
    return _handle(agent_delete_task, task_id)


@mcp.tool(name="agent_trigger_n8n_workflow", description="Dispara un workflow especifico de n8n.")
async def tool_agent_trigger_n8n_workflow(workflow_id: str, payload_json: str) -> dict[str, Any]:
    try:
        payload = json.loads(payload_json)
    except Exception as exc:
        raise SdkMcpError(ErrorData(code=-32602, message="Invalid JSON payload")) from exc
    return await _ahandle(agent_trigger_n8n_workflow, workflow_id, payload, settings.n8n_webhook_base_url, settings.n8n_auth_token)


@mcp.tool(name="agent_run_batch", description="Ejecuta multiples scripts en secuencia.")
def tool_agent_run_batch(scripts: list[str], args: str = "") -> dict[str, Any]:
    return _handle(agent_run_batch, settings.project_path, scripts, args)


@mcp.tool(name="agent_health_check", description="Verifica salud del servicio de agentes.")
def tool_agent_health_check() -> dict[str, Any]:
    return _handle(agent_health_check, settings.n8n_webhook_base_url)


@mcp.tool(name="agent_get_config", description="Retorna la configuracion actual del agent runner.")
def tool_agent_get_config() -> dict[str, Any]:
    return _handle(agent_get_config)


@mcp.tool(name="agent_run_with_timeout", description="Ejecuta un script local con timeout personalizado.")
def tool_agent_run_with_timeout(script_path: str, args: str = "", timeout: int = 30) -> dict[str, Any]:
    return _handle(agent_run_with_timeout, settings.project_path, script_path, args, timeout)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("agent://configuration")
def res_config() -> str:
    return res.agent_configuration()


@mcp.resource("agent://basics")
def res_basics() -> str:
    return res.agent_basics()


@mcp.resource("agent://best-practices")
def res_best() -> str:
    return res.agent_best_practices()


@mcp.resource("agent://quick-reference")
def res_quick() -> str:
    return res.agent_quick_reference()


@mcp.resource("agent://error-codes")
def res_errors() -> str:
    return res.agent_error_codes()


@mcp.resource("agent://troubleshooting")
def res_trouble() -> str:
    return res.agent_troubleshooting()


@mcp.resource("agent://examples")
def res_examples() -> str:
    return res.agent_examples()


@mcp.resource("agent://n8n-guide")
def res_n8n() -> str:
    return res.agent_n8n_guide()


@mcp.resource("agent://patterns")
def res_patterns() -> str:
    return res.agent_patterns()


@mcp.resource("agent://security")
def res_security() -> str:
    return res.agent_security()


@mcp.resource("agent://monitoring")
def res_monitoring() -> str:
    return res.agent_monitoring()


@mcp.resource("agent://scripting")
def res_scripting() -> str:
    return res.agent_scripting()


@mcp.resource("agent://ci-cd")
def res_cicd() -> str:
    return res.agent_ci_cd()


@mcp.resource("agent://architecture")
def res_arch() -> str:
    return res.agent_architecture()


@mcp.resource("agent://scaling")
def res_scaling() -> str:
    return res.agent_scaling()


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
