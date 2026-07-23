"""
Servidor FastMCP para mcp-event-driven.

Expone herramientas para analizar esquemas de eventos y simular flujos.
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

from mcp_event_driven import __version__
from mcp_event_driven.config import settings
from mcp_event_driven.tools.event_tools import (
    analyze_choreography,
    analyze_event_dependencies,
    compare_event_schemas,
    create_event_schema,
    export_event_catalog,
    generate_event_documentation,
    generate_event_payload,
    generate_event_test_cases,
    generate_saga_template,
    get_event_stats,
    list_event_schemas,
    parse_event_schema,
    trace_event_flow,
    validate_asyncapi_spec,
    validate_event_payload,
)
from mcp_event_driven import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-event-driven",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-event-driven")
    logger.info(
        "mcp-event-driven iniciando",
        version=__version__,
        schemas_path=str(settings.schemas_path),
    )
    yield
    logger.info("mcp-event-driven detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-event-driven",
    instructions=(
        "Servidor MCP para analizar esquemas de eventos (JSON Schema, AsyncAPI) "
        "y simular flujos de datos en arquitecturas coreografiadas."
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
        raise SdkMcpError(
            ErrorData(code=-32603, message="Error interno del servidor de eventos.")
        ) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="event_parse_schema",
    description="Parsea un esquema de evento (JSON Schema o AsyncAPI) para extraer metadata y propiedades.",
)
def tool_parse_schema(filename: str) -> dict[str, Any]:
    file_path = settings.schemas_path / filename
    logger.info("event_parse_schema llamado", file=filename)
    return _handle(parse_event_schema, file_path)


@mcp.tool(
    name="event_analyze_choreography",
    description="Escanea el directorio de esquemas configurado para encontrar todos los eventos registrados.",
)
def tool_analyze_choreography() -> dict[str, Any]:
    logger.info("event_analyze_choreography llamado")
    return _handle(analyze_choreography, settings.schemas_path)


@mcp.tool(
    name="event_generate_mock_payload",
    description="Genera un payload JSON simulado para un evento, dado un arreglo de sus propiedades.",
)
def tool_generate_payload(properties: list[str]) -> dict[str, Any]:
    logger.info("event_generate_mock_payload llamado")
    return _handle(generate_event_payload, properties)


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="event_validate_payload",
    description="Valida un payload contra un schema JSON. Parametros: schema_file, payload (dict).",
)
def tool_validate_payload(schema_file: str, payload: dict[str, Any]) -> dict[str, Any]:
    logger.info("event_validate_payload llamado", schema_file=schema_file)
    return _handle(validate_event_payload, settings.schemas_path, schema_file, payload)


@mcp.tool(
    name="event_list_schemas",
    description="Lista todos los schemas de eventos disponibles.",
)
def tool_list_schemas() -> list[dict[str, Any]]:
    logger.info("event_list_schemas llamado")
    return _handle(list_event_schemas, settings.schemas_path)


@mcp.tool(
    name="event_create_schema",
    description="Crea un nuevo schema JSON basico. Parametros: name, properties (list), required (list, opcional).",
)
def tool_create_schema(name: str, properties: list[str], required: list[str] | None = None) -> dict[str, Any]:
    logger.info("event_create_schema llamado", name=name)
    return _handle(create_event_schema, settings.schemas_path, name, properties, required)


@mcp.tool(
    name="event_trace_flow",
    description="Traza el flujo de un evento. Parametros: event_name.",
)
def tool_trace_flow(event_name: str) -> dict[str, Any]:
    logger.info("event_trace_flow llamado", event_name=event_name)
    return _handle(trace_event_flow, settings.schemas_path, event_name)


@mcp.tool(
    name="event_compare_schemas",
    description="Compara dos schemas de eventos. Parametros: file_a, file_b.",
)
def tool_compare_schemas(file_a: str, file_b: str) -> dict[str, Any]:
    logger.info("event_compare_schemas llamado", file_a=file_a, file_b=file_b)
    return _handle(compare_event_schemas, settings.schemas_path, file_a, file_b)


@mcp.tool(
    name="event_generate_documentation",
    description="Genera documentacion markdown para un schema. Parametros: filename.",
)
def tool_generate_documentation(filename: str) -> str:
    logger.info("event_generate_documentation llamado", filename=filename)
    return _handle(generate_event_documentation, settings.schemas_path, filename)


@mcp.tool(
    name="event_analyze_dependencies",
    description="Analiza dependencias entre eventos basado en propiedades compartidas.",
)
def tool_analyze_dependencies() -> dict[str, Any]:
    logger.info("event_analyze_dependencies llamado")
    return _handle(analyze_event_dependencies, settings.schemas_path)


@mcp.tool(
    name="event_generate_saga_template",
    description="Genera plantilla de Saga. Parametros: steps (list de strings).",
)
def tool_generate_saga(steps: list[str]) -> dict[str, Any]:
    logger.info("event_generate_saga_template llamado", steps=len(steps))
    return _handle(generate_saga_template, steps)


@mcp.tool(
    name="event_validate_asyncapi",
    description="Valida un spec AsyncAPI. Parametros: filename.",
)
def tool_validate_asyncapi(filename: str) -> dict[str, Any]:
    logger.info("event_validate_asyncapi llamado", filename=filename)
    return _handle(validate_asyncapi_spec, settings.schemas_path, filename)


@mcp.tool(
    name="event_generate_test_cases",
    description="Genera casos de prueba para un schema. Parametros: schema_file.",
)
def tool_generate_test_cases(schema_file: str) -> list[dict[str, Any]]:
    logger.info("event_generate_test_cases llamado", schema_file=schema_file)
    return _handle(generate_event_test_cases, schema_file, settings.schemas_path)


@mcp.tool(
    name="event_export_catalog",
    description="Exporta un catalogo completo de todos los eventos.",
)
def tool_export_catalog() -> dict[str, Any]:
    logger.info("event_export_catalog llamado")
    return _handle(export_event_catalog, settings.schemas_path)


@mcp.tool(
    name="event_get_stats",
    description="Genera estadisticas rapidas del catalogo de eventos.",
)
def tool_get_stats() -> dict[str, Any]:
    logger.info("event_get_stats llamado")
    return _handle(get_event_stats, settings.schemas_path)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("event://configuration")
def res_config() -> str:
    return res.event_configuration()


@mcp.resource("event://json-schema-guide")
def res_json_schema() -> str:
    return res.event_json_schema_guide()


@mcp.resource("event://asyncapi-guide")
def res_asyncapi() -> str:
    return res.event_asyncapi_guide()


@mcp.resource("event://choreography-guide")
def res_choreo() -> str:
    return res.event_choreography_guide()


@mcp.resource("event://orchestration-guide")
def res_orch() -> str:
    return res.event_orchestration_guide()


@mcp.resource("event://sourcing-guide")
def res_sourcing() -> str:
    return res.event_sourcing_guide()


@mcp.resource("event://cqrs-guide")
def res_cqrs() -> str:
    return res.event_cqrs_guide()


@mcp.resource("event://quick-reference")
def res_quick() -> str:
    return res.event_quick_reference()


@mcp.resource("event://error-codes")
def res_errors() -> str:
    return res.event_error_codes()


@mcp.resource("event://troubleshooting")
def res_trouble() -> str:
    return res.event_troubleshooting()


@mcp.resource("event://examples")
def res_examples() -> str:
    return res.event_examples()


@mcp.resource("event://message-patterns")
def res_patterns() -> str:
    return res.event_message_patterns()


@mcp.resource("event://dlq-guide")
def res_dlq() -> str:
    return res.event_dead_letter_queue()


@mcp.resource("event://idempotency-guide")
def res_idem() -> str:
    return res.event_idempotency()


@mcp.resource("event://best-practices")
def res_best() -> str:
    return res.event_best_practices()


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
