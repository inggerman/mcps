"""Servidor FastMCP para mcp-credential-broker.

Broker local de credenciales. Permite que agentes de IA ejecuten comandos con
credenciales inyectadas localmente sin que el valor viaje al LLM. Tambien
permite revelar credenciales al usuario con confirmacion HITL.

Seguridad: NINGUNA tool retorna valores de credenciales al llamador.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import MCPError as SdkMcpError
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_credential_broker.config import settings
from mcp_credential_broker.tools import (
    list_credentials,
    process_with_local_llm,
    reveal_secret,
    run_with_creds,
    store_credential,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-credential-broker",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-credential-broker")
    logger.info("Credential broker iniciando", **settings.to_log_context())
    yield
    logger.info("Credential broker detenido")
    structlog.contextvars.clear_contextvars()


mcp = FastMCP(
    name="mcp-credential-broker",
    instructions=(
        "Broker local de credenciales para agentes de IA. "
        "Ejecuta comandos con credenciales inyectadas localmente (run_with_creds), "
        "revela credenciales al usuario con confirmacion HITL (reveal_secret), "
        "lista credenciales disponibles (list_credentials), "
        "almacena nuevas credenciales desde env var o archivo (store_credential). "
        "NUNCA expone valores de credenciales al agente. "
        "Refs: vault:<path>#<key>, env:<VAR>, file:<path>, keychain:<service>:<account>."
    ),
    lifespan=lifespan,
)


@mcp.tool(
    name="run_with_creds",
    description=(
        "Ejecuta un comando con una credencial inyectada como env var. "
        "La credencial se resuelve localmente (Vault/env/file/keychain) y se inyecta "
        "como variable de entorno 'inject_as' en el subprocess. "
        "El valor NUNCA se retorna en la respuesta. "
        "Parametros: command (str), credential_ref (str), inject_as (str, default 'CRED'), "
        "timeout (int, segundos), cwd (str, opcional)."
    ),
)
def tool_run_with_creds(
    command: str,
    credential_ref: str,
    inject_as: str = "CRED",
    timeout: int | None = None,
    cwd: str | None = None,
) -> dict[str, Any]:
    logger.info("run_with_creds llamado", credential_ref=credential_ref, inject_as=inject_as)
    try:
        return run_with_creds(
            command=command,
            credential_ref=credential_ref,
            inject_as=inject_as,
            timeout=timeout,
            cwd=cwd,
        )
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en run_with_creds", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del broker.") from exc


@mcp.tool(
    name="reveal_secret",
    description=(
        "Revela una credencial al usuario (NO al agente). Requiere confirmacion humana "
        "via dialogo nativo (HITL). Si se aprueba, el valor se imprime al terminal del "
        "usuario. El agente solo recibe {revealed: true/false}, nunca el valor. "
        "Parametros: credential_ref (str), reason (str, motivo para mostrar al usuario)."
    ),
)
def tool_reveal_secret(credential_ref: str, reason: str = "") -> dict[str, Any]:
    logger.info("reveal_secret llamado", credential_ref=credential_ref)
    try:
        return reveal_secret(credential_ref=credential_ref, reason=reason)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en reveal_secret", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del broker.") from exc


@mcp.tool(
    name="list_credentials",
    description=(
        "Lista las credenciales disponibles (sin valores). "
        "Parametros: backend (str, opcional: vault|env|file|keychain). "
        "Retorna lista de {ref, backend, type, metadata}."
    ),
)
def tool_list_credentials(backend: str | None = None) -> list[dict[str, Any]]:
    logger.info("list_credentials llamado", backend=backend)
    try:
        return list_credentials(backend=backend)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_credentials", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del broker.") from exc


@mcp.tool(
    name="store_credential",
    description=(
        "Almacena una credencial en un backend que soporta escritura (keychain). "
        "El valor se lee de una env var o archivo LOCAL, nunca del chat. "
        "Parametros: ref (str, ej. 'keychain:portal-x:admin'), "
        "from_env (str, nombre de env var) o from_file (str, ruta de archivo)."
    ),
)
def tool_store_credential(
    ref: str,
    from_env: str | None = None,
    from_file: str | None = None,
) -> dict[str, Any]:
    logger.info("store_credential llamado", ref=ref)
    try:
        return store_credential(ref=ref, from_env=from_env, from_file=from_file)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en store_credential", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del broker.") from exc


@mcp.tool(
    name="process_with_local_llm",
    description=(
        "Procesa datos sensibles con un LLM local (LM Studio) sin enviarlos al cloud. "
        "Resuelve la credencial localmente, la incluye en el prompt enviado a LM Studio, "
        "y retorna solo la respuesta del modelo. El valor sensible NUNCA entra en la "
        "conversacion con el agente cloud. "
        "Parametros: prompt (str, instruccion sin el valor sensible), "
        "credential_ref (str, ref al dato sensible), "
        "model (str, opcional, default qwen3-8b), "
        "max_tokens (int, default 2000)."
    ),
)
def tool_process_with_local_llm(
    prompt: str,
    credential_ref: str,
    model: str | None = None,
    max_tokens: int = 2000,
) -> dict[str, Any]:
    logger.info("process_with_local_llm llamado", credential_ref=credential_ref, model=model)
    try:
        return process_with_local_llm(
            prompt=prompt,
            credential_ref=credential_ref,
            model=model,
            max_tokens=max_tokens,
        )
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en process_with_local_llm", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del broker.") from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
