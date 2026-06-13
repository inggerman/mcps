"""Servidor FastMCP para mcp-structured-output."""

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

from mcp_structured_output.config import settings
from mcp_structured_output.tools import (
    generate_schema,
    invoke_structured,
    sanitize_schema,
    validate_schema,
)

# ---------------------------------------------------------------------------
# Setup (antes de crear FastMCP)
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-structured-output",
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-structured-output")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()


# ---------------------------------------------------------------------------
# Instancia del servidor
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-structured-output",
    instructions=(
        "Servidor MCP para trabajar con salidas estructuradas (JSON Schema). "
        "Soporta Amazon Bedrock (Converse, InvokeModel Claude, InvokeModel open-weight) "
        "y cualquier endpoint OpenAI-compatible. "
        "Incluye herramientas locales para validar, generar y sanear JSON Schemas."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Tool: invoke_structured
# ---------------------------------------------------------------------------


@mcp.tool(
    name="invoke_structured",
    description=(
        "Llama a un LLM y garantiza que la respuesta cumpla un JSON Schema. "
        "Proveedores: bedrock-converse | bedrock-invoke-claude | "
        "bedrock-invoke-openweight | openai-compatible. "
        "Credenciales AWS vía entorno/perfil boto3. "
        "Parámetros: prompt, schema, schema_name (default 'response'), provider, model_id, "
        "system_prompt, max_tokens (default 2048), temperature (default 0.0), "
        "region (AWS), base_url (solo openai-compatible)."
    ),
)
def tool_invoke_structured(
    prompt: str,
    schema: dict[str, Any],
    schema_name: str = "response",
    provider: str = settings.default_provider,
    model_id: str = settings.default_model_id,
    system_prompt: str | None = None,
    max_tokens: int = settings.default_max_tokens,
    temperature: float = settings.default_temperature,
    region: str | None = settings.aws_region,
    base_url: str | None = settings.openai_base_url,
) -> dict[str, Any]:
    logger.info(
        "invoke_structured llamado",
        provider=provider,
        model_id=model_id,
        schema_name=schema_name,
        prompt_length=len(prompt),
    )
    try:
        result = invoke_structured(
            prompt=prompt,
            schema=schema,
            schema_name=schema_name,
            provider=provider,
            model_id=model_id,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            region=region,
            base_url=base_url,
        )
        logger.info(
            "invoke_structured completado",
            provider=provider,
            input_tokens=result["usage"]["input_tokens"],
            output_tokens=result["usage"]["output_tokens"],
        )
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en invoke_structured", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Tool: validate_schema
# ---------------------------------------------------------------------------


@mcp.tool(
    name="validate_schema",
    description=(
        "Valida localmente que un JSON Schema sea compatible con Bedrock structured output "
        "(Draft 2020-12). Detecta: schemas recursivos, $ref externos, "
        "additionalProperties != false, constraints numéricas/string no soportadas, "
        "minItems fuera de [0,1], enum con tipos complejos. "
        "No hace llamadas a AWS. "
        "Retorna: valid (bool), issues (lista con path, message, severity)."
    ),
)
def tool_validate_schema(schema: dict[str, Any]) -> dict[str, Any]:
    logger.info("validate_schema llamado")
    try:
        result = validate_schema(schema=schema)
        logger.info(
            "validate_schema completado",
            valid=result["valid"],
            issue_count=len(result["issues"]),
        )
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en validate_schema", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Tool: generate_schema
# ---------------------------------------------------------------------------


@mcp.tool(
    name="generate_schema",
    description=(
        "Genera un JSON Schema Bedrock-compatible a partir de un objeto JSON de ejemplo. "
        "Infiere tipos automáticamente y aplica additionalProperties: false. "
        "Parámetros: example (dict JSON), name (nombre del schema, default 'schema'), "
        "description (opcional), strict (bool, default true — marca todos los campos como required). "
        "Retorna: schema (dict), field_count (int), warnings (list)."
    ),
)
def tool_generate_schema(
    example: dict[str, Any],
    name: str = "schema",
    description: str | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    logger.info("generate_schema llamado", field_count=len(example), name=name)
    try:
        result = generate_schema(
            example=example,
            name=name,
            description=description,
            strict=strict,
        )
        logger.info(
            "generate_schema completado",
            field_count=result["field_count"],
            warnings=len(result["warnings"]),
        )
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en generate_schema", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Tool: sanitize_schema
# ---------------------------------------------------------------------------


@mcp.tool(
    name="sanitize_schema",
    description=(
        "Transforma un JSON Schema para que sea compatible con Bedrock structured output. "
        "Elimina/transforma automáticamente: constraints numéricas (minimum, maximum, multipleOf), "
        "constraints de string (minLength, maxLength), "
        "additionalProperties != false, $ref externos, minItems fuera de [0,1], "
        "valores complejos en enum. "
        "El schema original NO se modifica. "
        "Retorna: sanitized (dict), changes (lista con path, action, reason), was_valid (bool)."
    ),
)
def tool_sanitize_schema(schema: dict[str, Any]) -> dict[str, Any]:
    logger.info("sanitize_schema llamado")
    try:
        result = sanitize_schema(schema=schema)
        logger.info(
            "sanitize_schema completado",
            was_valid=result["was_valid"],
            changes=len(result["changes"]),
        )
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en sanitize_schema", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


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
