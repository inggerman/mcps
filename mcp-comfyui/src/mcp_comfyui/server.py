"""Servidor FastMCP para mcp-comfyui."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import MCPError as SdkMcpError
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_comfyui.config import settings
from mcp_comfyui.tools import (
    get_history,
    get_output_images,
    get_prompt_result,
    get_system_stats,
    get_workflow_status,
    interrupt_generation,
    list_embeddings,
    list_loras,
    list_models,
    queue_prompt,
    upload_image,
)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-comfyui",
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-comfyui")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()


# ---------------------------------------------------------------------------
# Instancia del servidor
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-comfyui",
    instructions=(
        "Servidor MCP para ComfyUI — generación de imágenes y video via workflow API. "
        "Herramientas: get_system_stats (estado del servidor, GPU, VRAM), "
        "list_models (checkpoints disponibles), list_loras (LoRAs disponibles), "
        "list_embeddings (embeddings disponibles), "
        "queue_prompt (encolar workflow para ejecución), "
        "get_workflow_status (estado de un prompt encolado), "
        "get_prompt_result (resultado completo con polling), "
        "get_history (historial de ejecuciones), "
        "get_output_images (URL de imagen generada), "
        "upload_image (subir imagen para img2img/ControlNet), "
        "interrupt_generation (cancelar generación en curso). "
        "El workflow debe estar en formato API de ComfyUI (no el formato UI)."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="get_system_stats",
    description=(
        "Obtiene estadísticas del sistema ComfyUI: GPU, VRAM, queue, devices. "
        "Útil para verificar que el servidor está corriendo y ver recursos disponibles. "
        "Retorna: system_stats con devices, queue_remaining, etc."
    ),
)
def tool_get_system_stats() -> dict[str, Any]:
    logger.info("get_system_stats llamado")
    try:
        result = get_system_stats()
        logger.info("get_system_stats completado", devices=len(result.get("devices", [])))
        return result
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_system_stats", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(
    name="list_models",
    description=(
        "Lista los modelos (checkpoints) disponibles en ComfyUI. "
        "Retorna: checkpoints (lista de nombres de modelos en models/checkpoints). "
        "Usa el endpoint /object_info/CheckpointLoaderSimple."
    ),
)
def tool_list_models() -> dict[str, Any]:
    logger.info("list_models llamado")
    try:
        result = list_models()
        logger.info("list_models completado", count=len(result.get("checkpoints", [])))
        return result
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_models", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(
    name="list_loras",
    description=(
        "Lista los LoRAs disponibles en ComfyUI. "
        "Retorna: loras (lista de nombres en models/loras). "
        "Usa el endpoint /object_info/LoraLoader."
    ),
)
def tool_list_loras() -> dict[str, Any]:
    logger.info("list_loras llamado")
    try:
        result = list_loras()
        logger.info("list_loras completado", count=len(result.get("loras", [])))
        return result
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_loras", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(
    name="list_embeddings",
    description=(
        "Lista los embeddings (textual inversion) disponibles en ComfyUI. "
        "Retorna: embeddings (lista de nombres)."
    ),
)
def tool_list_embeddings() -> dict[str, Any]:
    logger.info("list_embeddings llamado")
    try:
        result = list_embeddings()
        logger.info("list_embeddings completado", count=len(result.get("embeddings", [])))
        return result
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_embeddings", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(
    name="queue_prompt",
    description=(
        "Encola un workflow (prompt) para ejecución en ComfyUI. "
        "Parámetros: workflow (dict, grafo de nodos en formato API de ComfyUI), "
        "client_id (str opcional para tracking). "
        "El workflow debe ser un dict donde cada key es un ID de nodo y el valor "
        "tiene class_type e inputs. Ejemplo: "
        '{"3": {"class_type": "KSampler", "inputs": {"seed": 42, ...}}}. '
        "Retorna: prompt_id (UUID), number (posición en cola), node_errors."
    ),
)
def tool_queue_prompt(
    workflow: dict[str, Any],
    client_id: str | None = None,
) -> dict[str, Any]:
    logger.info("queue_prompt llamado", nodes=len(workflow) if workflow else 0)
    try:
        result = queue_prompt(workflow=workflow, client_id=client_id)
        logger.info("queue_prompt completado", prompt_id=result.get("prompt_id"))
        return result
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en queue_prompt", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(
    name="get_workflow_status",
    description=(
        "Consulta el estado de un prompt encolado en ComfyUI. "
        "Parámetros: prompt_id (UUID devuelto por queue_prompt). "
        "Retorna: status ('queued' | 'executing' | 'completed' | 'unknown'), "
        "queue_position (si está en cola)."
    ),
)
def tool_get_workflow_status(prompt_id: str) -> dict[str, Any]:
    logger.info("get_workflow_status llamado", prompt_id=prompt_id)
    try:
        result = get_workflow_status(prompt_id=prompt_id)
        logger.info("get_workflow_status completado", status=result.get("status"))
        return result
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_workflow_status", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(
    name="get_prompt_result",
    description=(
        "Obtiene el resultado completo de un prompt en ComfyUI, con polling opcional. "
        "Parámetros: prompt_id (UUID), poll (bool, default True — hace polling "
        "hasta completar o timeout de 10min). "
        "Retorna: status ('completed' | 'error' | 'timeout' | 'unknown'), "
        "outputs (dict de outputs por nodo), images (lista de {filename, subfolder, type})."
    ),
)
def tool_get_prompt_result(
    prompt_id: str,
    poll: bool = True,
) -> dict[str, Any]:
    logger.info("get_prompt_result llamado", prompt_id=prompt_id, poll=poll)
    try:
        result = get_prompt_result(prompt_id=prompt_id, poll=poll)
        logger.info(
            "get_prompt_result completado",
            prompt_id=prompt_id,
            status=result.get("status"),
            images=len(result.get("images", [])),
        )
        return result
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_prompt_result", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(
    name="get_history",
    description=(
        "Obtiene el historial de ejecuciones de ComfyUI. "
        "Parámetros: prompt_id (str opcional — filtra a un prompt específico), "
        "max_items (int, default 50 — límite si no hay prompt_id). "
        "Retorna: history (dict de {prompt_id: {status, outputs, ...}})."
    ),
)
def tool_get_history(
    prompt_id: str | None = None,
    max_items: int = 50,
) -> dict[str, Any]:
    logger.info("get_history llamado", prompt_id=prompt_id)
    try:
        result = get_history(prompt_id=prompt_id, max_items=max_items)
        logger.info("get_history completado", entries=len(result.get("history", {})))
        return result
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_history", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(
    name="get_output_images",
    description=(
        "Construye la URL para descargar una imagen generada por ComfyUI. "
        "Parámetros: filename (nombre del archivo, de get_prompt_result.images), "
        "subfolder (str, default ''), image_type ('output' | 'temp', default 'output'). "
        "Retorna: url (URL completa para descargar la imagen), filename, type."
    ),
)
def tool_get_output_images(
    filename: str,
    subfolder: str = "",
    image_type: str = "output",
) -> dict[str, Any]:
    logger.info("get_output_images llamado", filename=filename)
    try:
        result = get_output_images(filename=filename, subfolder=subfolder, image_type=image_type)
        logger.info("get_output_images completado", url=result.get("url"))
        return result
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_output_images", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(
    name="upload_image",
    description=(
        "Sube una imagen a ComfyUI para usar como input (img2img, ControlNet, inpainting). "
        "Parámetros: image_path (ruta local al archivo), overwrite (bool, default False). "
        "Retorna: name (nombre del archivo subido), subfolder, type ('input')."
    ),
)
def tool_upload_image(
    image_path: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    logger.info("upload_image llamado", image_path=image_path)
    try:
        result = upload_image(image_path=image_path, overwrite=overwrite)
        logger.info("upload_image completado", name=result.get("name"))
        return result
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en upload_image", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(
    name="interrupt_generation",
    description=(
        "Interrumpe la generación en curso de ComfyUI. "
        "Útil para cancelar una generación larga o atascada. "
        "Retorna: status ('interrupted')."
    ),
)
def tool_interrupt_generation() -> dict[str, Any]:
    logger.info("interrupt_generation llamado")
    try:
        result = interrupt_generation()
        logger.info("interrupt_generation completado")
        return result
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en interrupt_generation", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


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
