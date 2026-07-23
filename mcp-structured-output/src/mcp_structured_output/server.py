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
    check_schema_compatibility,
    count_schema_fields,
    extract_schema_fields,
    flatten_schema,
    generate_schema,
    invoke_structured,
    list_schema_keywords,
    merge_schemas,
    sanitize_schema,
    schema_complexity,
    schema_diff,
    schema_to_json_example,
    schema_to_markdown,
    schema_to_openapi,
    schema_to_python,
    schema_to_table,
    schema_to_typescript,
    simplify_schema,
    validate_json_against_schema,
    validate_schema,
)
from mcp_structured_output import resources as res

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

# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def _handle(name: str, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception(f"Error inesperado en {name}", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="schema_to_typescript", description="Convierte un JSON Schema a interfaces TypeScript.")
def tool_schema_to_typescript(schema: dict[str, Any]) -> str:
    return _handle("schema_to_typescript", schema_to_typescript, schema=schema)


@mcp.tool(name="schema_to_python", description="Convierte un JSON Schema a una clase Pydantic.")
def tool_schema_to_python(schema: dict[str, Any], class_name: str = "RootModel") -> str:
    return _handle("schema_to_python", schema_to_python, schema=schema, class_name=class_name)


@mcp.tool(name="flatten_schema", description="Aplana un schema resolviendo $ref internos.")
def tool_flatten_schema(schema: dict[str, Any]) -> dict[str, Any]:
    return _handle("flatten_schema", flatten_schema, schema=schema)


@mcp.tool(name="merge_schemas", description="Combina multiples schemas en uno solo.")
def tool_merge_schemas(schemas: list[dict[str, Any]]) -> dict[str, Any]:
    return _handle("merge_schemas", merge_schemas, schemas=schemas)


@mcp.tool(name="extract_schema_fields", description="Lista todos los campos de un schema con tipo y ruta.")
def tool_extract_schema_fields(schema: dict[str, Any]) -> list[dict[str, Any]]:
    return _handle("extract_schema_fields", extract_schema_fields, schema=schema)


@mcp.tool(name="schema_to_markdown", description="Genera documentacion Markdown desde un JSON Schema.")
def tool_schema_to_markdown(schema: dict[str, Any]) -> str:
    return _handle("schema_to_markdown", schema_to_markdown, schema=schema)


@mcp.tool(name="validate_json_against_schema", description="Valida una instancia JSON contra un JSON Schema.")
def tool_validate_json_against_schema(instance: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    return _handle("validate_json_against_schema", validate_json_against_schema, instance=instance, schema=schema)


@mcp.tool(name="schema_diff", description="Compara dos schemas y retorna las diferencias.")
def tool_schema_diff(schema_a: dict[str, Any], schema_b: dict[str, Any]) -> dict[str, Any]:
    return _handle("schema_diff", schema_diff, schema_a=schema_a, schema_b=schema_b)


@mcp.tool(name="schema_complexity", description="Calcula metricas de complejidad de un schema.")
def tool_schema_complexity(schema: dict[str, Any]) -> dict[str, Any]:
    return _handle("schema_complexity", schema_complexity, schema=schema)


@mcp.tool(name="simplify_schema", description="Simplifica un schema removiendo metadatos innecesarios.")
def tool_simplify_schema(schema: dict[str, Any]) -> dict[str, Any]:
    return _handle("simplify_schema", simplify_schema, schema=schema)


@mcp.tool(name="schema_to_json_example", description="Genera un ejemplo JSON desde un JSON Schema.")
def tool_schema_to_json_example(schema: dict[str, Any]) -> dict[str, Any]:
    return _handle("schema_to_json_example", schema_to_json_example, schema=schema)


@mcp.tool(name="list_schema_keywords", description="Lista todas las keywords usadas en un schema.")
def tool_list_schema_keywords(schema: dict[str, Any]) -> list[str]:
    return _handle("list_schema_keywords", list_schema_keywords, schema=schema)


@mcp.tool(name="count_schema_fields", description="Cuenta el numero total de campos recursivamente.")
def tool_count_schema_fields(schema: dict[str, Any]) -> dict[str, Any]:
    return _handle("count_schema_fields", count_schema_fields, schema=schema)


@mcp.tool(name="schema_to_table", description="Genera una representacion en tabla de un schema.")
def tool_schema_to_table(schema: dict[str, Any]) -> str:
    return _handle("schema_to_table", schema_to_table, schema=schema)


@mcp.tool(name="check_schema_compatibility", description="Verifica compatibilidad con Bedrock y retorna un score.")
def tool_check_schema_compatibility(schema: dict[str, Any]) -> dict[str, Any]:
    return _handle("check_schema_compatibility", check_schema_compatibility, schema=schema)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.tool(name="schema_to_openapi", description="Convierte un JSON Schema a un componente OpenAPI 3.1.")
def tool_schema_to_openapi(schema: dict[str, Any], path: str = "/data") -> dict[str, Any]:
    return _handle("schema_to_openapi", schema_to_openapi, schema=schema, path=path)


@mcp.resource("structured-output://configuration")
def res_config() -> str:
    return res.structured_output_configuration()


@mcp.resource("structured-output://supported-providers")
def res_providers() -> str:
    return res.supported_providers()


@mcp.resource("structured-output://json-schema-basics")
def res_basics() -> str:
    return res.json_schema_basics()


@mcp.resource("structured-output://bedrock-compatibility")
def res_bedrock() -> str:
    return res.bedrock_compatibility_guide()


@mcp.resource("structured-output://validation-tips")
def res_validation() -> str:
    return res.schema_validation_tips()


@mcp.resource("structured-output://generation-tips")
def res_generation() -> str:
    return res.schema_generation_tips()


@mcp.resource("structured-output://sanitization-tips")
def res_sanitization() -> str:
    return res.schema_sanitization_tips()


@mcp.resource("structured-output://common-workflows")
def res_workflows() -> str:
    return res.common_structured_output_workflows()


@mcp.resource("structured-output://error-codes")
def res_errors() -> str:
    return res.structured_output_error_codes()


@mcp.resource("structured-output://json-schema-types")
def res_types() -> str:
    return res.json_schema_types_reference()


@mcp.resource("structured-output://bedrock-models")
def res_models() -> str:
    return res.bedrock_models_reference()


@mcp.resource("structured-output://openai-compatible-guide")
def res_openai() -> str:
    return res.openai_compatible_guide()


@mcp.resource("structured-output://schema-keywords")
def res_keywords() -> str:
    return res.schema_keywords_reference()


@mcp.resource("structured-output://examples/generate-schema")
def res_example_gen() -> str:
    return res.example_generate_schema()


@mcp.resource("structured-output://examples/invoke-structured")
def res_example_invoke() -> str:
    return res.example_invoke_structured()


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")
