"""
Servidor FastMCP para mcp-tabular.

Expone 8 herramientas para leer, filtrar, buscar y analizar archivos tabulares
(Excel, CSV, ODS, TSV, Parquet) como tools del protocolo MCP.

Transporte: stdio (compatible con Claude Desktop, Cursor, Cline).
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

from mcp_tabular import __version__
from mcp_tabular.config import TabularSettings
from mcp_tabular.tools.tabular_reader import (
    convert_to_csv,
    filter_rows,
    get_column_stats,
    get_file_summary,
    get_sheet_names,
    read_specific_sheet,
    read_tabular_file,
    search_in_file,
)

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

settings = TabularSettings()

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-tabular",
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """
    Context manager de ciclo de vida del servidor MCP.

    Se ejecuta al inicio y al shutdown del servidor. Registra eventos de startup
    y shutdown en los logs estructurados para facilitar el monitoreo.
    """
    # Startup
    structlog.contextvars.bind_contextvars(server_name="mcp-tabular")
    logger.info(
        "Servidor mcp-tabular iniciando",
        version=__version__,
        max_rows_preview=settings.max_rows_preview,
        max_file_size_mb=settings.max_file_size_mb,
        default_encoding=settings.default_encoding,
        log_level=settings.log_level,
        log_format=settings.log_format,
    )

    yield

    # Shutdown
    logger.info("Servidor mcp-tabular detenido", version=__version__)


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-tabular",
    instructions=(
        "Servidor MCP especializado en lectura y análisis de archivos tabulares. "
        "Soporta los formatos: Excel (.xlsx, .xls), CSV, TSV, ODS (LibreOffice Calc) y Parquet. "
        "\n\n"
        "Herramientas disponibles:\n"
        "- read_tabular_file: Lee cualquier archivo tabular y retorna datos estructurados. "
        "Detecta automáticamente el encoding para CSV/TSV.\n"
        "- get_sheet_names: Lista las hojas de un archivo Excel u ODS.\n"
        "- get_file_summary: Estadísticas completas (shape, tipos, nulos, describe) del archivo.\n"
        "- read_specific_sheet: Lee una hoja concreta de Excel/ODS por nombre.\n"
        "- filter_rows: Filtra filas por criterio en una columna "
        "(operadores: eq, ne, gt, lt, gte, lte, contains, startswith).\n"
        "- search_in_file: Busca texto en todas las columnas del archivo.\n"
        "- convert_to_csv: Convierte el archivo a formato CSV y retorna el texto.\n"
        "- get_column_stats: Estadísticas detalladas de una columna específica "
        "(numérica, texto o fecha).\n"
        "\n"
        "Todos los datos se retornan en formato JSON estructurado con metadatos completos. "
        "Los archivos deben estar accesibles en el sistema de archivos donde corre el servidor."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Helpers de manejo de errores
# ---------------------------------------------------------------------------


def _handle_mcp_error(tool_name: str, exc: McpError) -> None:
    """
    Registra un McpError estructurado y lo relanza como SdkMcpError.

    Args:
        tool_name: Nombre de la tool que generó el error.
        exc: Excepción McpError del framework.

    Raises:
        SdkMcpError: Versión compatible con el SDK de MCP.
    """
    logger.error(
        "Error en tool MCP",
        tool=tool_name,
        error_code=exc.error_code,
        message=exc.message,
        context=exc.context,
    )
    raise SdkMcpError(ErrorData(code=-32000, message=str(exc)))


def _handle_unexpected_error(tool_name: str, exc: Exception) -> None:
    """
    Registra un error inesperado y lo relanza como SdkMcpError.

    Args:
        tool_name: Nombre de la tool que generó el error.
        exc: Excepción inesperada.

    Raises:
        SdkMcpError: Versión compatible con el SDK de MCP.
    """
    logger.exception(
        "Error inesperado en tool MCP",
        tool=tool_name,
        error_type=type(exc).__name__,
        error=str(exc),
    )
    raise SdkMcpError(ErrorData(code=-32603, message=f"Error interno: {exc}"))


# ---------------------------------------------------------------------------
# Tools registradas
# ---------------------------------------------------------------------------


@mcp.tool(
    name="read_tabular_file",
    description=(
        "Lee un archivo tabular (Excel, CSV, TSV, ODS, Parquet) y retorna los datos en formato JSON. "
        "Detecta automáticamente el encoding para archivos CSV/TSV. "
        "Parámetros: path (ruta al archivo), sheet (nombre de hoja para Excel/ODS, opcional), "
        "encoding ('auto' o nombre de encoding como 'utf-8', 'latin-1'). "
        "Retorna: columns (metadatos de columnas), records (filas como dicts), total_rows, "
        "returned_rows, truncated, metadata, warnings."
    ),
)
def tool_read_tabular_file(
    path: str,
    sheet: str | None = None,
    encoding: str = "auto",
) -> dict[str, Any]:
    """Lee un archivo tabular y retorna datos estructurados."""
    try:
        return read_tabular_file(
            path=path,
            sheet=sheet,
            encoding=encoding,
            max_rows=settings.max_rows_preview,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("read_tabular_file", exc)
    except Exception as exc:
        _handle_unexpected_error("read_tabular_file", exc)
    return {}  # unreachable, satisfies type checker


@mcp.tool(
    name="get_sheet_names",
    description=(
        "Retorna la lista de nombres de hojas de un archivo Excel (.xlsx, .xls) u ODS. "
        "No aplica para CSV, TSV ni Parquet. "
        "Parámetro: path (ruta al archivo). "
        "Retorna: lista de strings con los nombres de las hojas en orden."
    ),
)
def tool_get_sheet_names(path: str) -> list[str]:
    """Lista las hojas disponibles en un archivo Excel u ODS."""
    try:
        return get_sheet_names(path=path)
    except McpError as exc:
        _handle_mcp_error("get_sheet_names", exc)
    except Exception as exc:
        _handle_unexpected_error("get_sheet_names", exc)
    return []


@mcp.tool(
    name="get_file_summary",
    description=(
        "Retorna estadísticas completas de un archivo tabular: shape (filas × columnas), "
        "tipos de datos, conteo de nulos por columna, y estadísticas descriptivas "
        "(mean, std, min, max, percentiles) de columnas numéricas. "
        "Parámetros: path (ruta al archivo), sheet (hoja para Excel/ODS, opcional). "
        "Retorna: dict con shape, columns, dtypes, null_counts, null_percentages, "
        "numeric_describe, size_bytes, size_mb."
    ),
)
def tool_get_file_summary(
    path: str,
    sheet: str | None = None,
) -> dict[str, Any]:
    """Genera un resumen estadístico del archivo tabular."""
    try:
        return get_file_summary(
            path=path,
            sheet=sheet,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("get_file_summary", exc)
    except Exception as exc:
        _handle_unexpected_error("get_file_summary", exc)
    return {}


@mcp.tool(
    name="read_specific_sheet",
    description=(
        "Lee una hoja específica de un archivo Excel (.xlsx, .xls) u ODS por nombre exacto. "
        "Retorna un error descriptivo si la hoja no existe, indicando las hojas disponibles. "
        "Parámetros: path (ruta al archivo), sheet_name (nombre exacto de la hoja). "
        "Retorna: mismo formato que read_tabular_file."
    ),
)
def tool_read_specific_sheet(
    path: str,
    sheet_name: str,
) -> dict[str, Any]:
    """Lee una hoja específica de un archivo Excel u ODS."""
    try:
        return read_specific_sheet(
            path=path,
            sheet_name=sheet_name,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("read_specific_sheet", exc)
    except Exception as exc:
        _handle_unexpected_error("read_specific_sheet", exc)
    return {}


@mcp.tool(
    name="filter_rows",
    description=(
        "Filtra filas de un archivo tabular según un criterio en una columna. "
        "Operadores soportados: "
        "eq (igual), ne (diferente), gt (mayor), lt (menor), gte (mayor o igual), "
        "lte (menor o igual), contains (contiene substring, case-insensitive), "
        "startswith (empieza con, case-insensitive). "
        "Parámetros: path, column (nombre de columna), operator (ver lista), "
        "value (valor a comparar como string), sheet (opcional). "
        "El valor se convierte automáticamente al tipo de la columna para comparaciones numéricas. "
        "Retorna: mismo formato que read_tabular_file pero solo con las filas que cumplen el filtro."
    ),
)
def tool_filter_rows(
    path: str,
    column: str,
    operator: str,
    value: str,
    sheet: str | None = None,
) -> dict[str, Any]:
    """Filtra filas del archivo según criterio en una columna."""
    try:
        return filter_rows(
            path=path,
            column=column,
            operator=operator,
            value=value,
            sheet=sheet,
            max_rows=settings.max_rows_preview,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("filter_rows", exc)
    except Exception as exc:
        _handle_unexpected_error("filter_rows", exc)
    return {}


@mcp.tool(
    name="search_in_file",
    description=(
        "Busca un texto en todas las columnas del archivo tabular (búsqueda case-insensitive). "
        "Retorna todas las celdas que contienen el texto buscado, con el contexto completo de la fila. "
        "Parámetros: path, query (texto a buscar), sheet (opcional), "
        "max_results (máximo de resultados, por defecto 100). "
        "Retorna: lista de matches con row_index, column, value y row (fila completa)."
    ),
)
def tool_search_in_file(
    path: str,
    query: str,
    sheet: str | None = None,
    max_results: int = 100,
) -> list[dict[str, Any]]:
    """Busca texto en todas las columnas del archivo."""
    try:
        return search_in_file(
            path=path,
            query=query,
            sheet=sheet,
            max_results=max_results,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("search_in_file", exc)
    except Exception as exc:
        _handle_unexpected_error("search_in_file", exc)
    return []


@mcp.tool(
    name="convert_to_csv",
    description=(
        "Convierte un archivo tabular (Excel, ODS, Parquet) a formato CSV. "
        "Retorna el contenido CSV completo como string, incluyendo encabezados. "
        "Útil para exportar datos o usar en otros sistemas que solo aceptan CSV. "
        "Parámetros: path, sheet (nombre de hoja para Excel/ODS, opcional), "
        "output_encoding (encoding del CSV de salida, por defecto 'utf-8'). "
        "Retorna: string con el contenido CSV completo."
    ),
)
def tool_convert_to_csv(
    path: str,
    sheet: str | None = None,
    output_encoding: str = "utf-8",
) -> str:
    """Convierte un archivo tabular a formato CSV."""
    try:
        return convert_to_csv(
            path=path,
            sheet=sheet,
            output_encoding=output_encoding,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("convert_to_csv", exc)
    except Exception as exc:
        _handle_unexpected_error("convert_to_csv", exc)
    return ""


@mcp.tool(
    name="get_column_stats",
    description=(
        "Retorna estadísticas detalladas de una columna específica del archivo. "
        "Para columnas numéricas: mean, std, min, max, percentiles, skewness, kurtosis. "
        "Para columnas de texto: value_counts top-10, most_frequent, avg/min/max length. "
        "Para columnas de fecha: min_date, max_date, date_range_days. "
        "Para todas: null_count, null_percentage, unique_count, dtype, total_count. "
        "Parámetros: path, column (nombre exacto de la columna), sheet (opcional). "
        "Retorna: dict con stats adaptadas al tipo de la columna."
    ),
)
def tool_get_column_stats(
    path: str,
    column: str,
    sheet: str | None = None,
) -> dict[str, Any]:
    """Calcula estadísticas detalladas de una columna."""
    try:
        return get_column_stats(
            path=path,
            column=column,
            sheet=sheet,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("get_column_stats", exc)
    except Exception as exc:
        _handle_unexpected_error("get_column_stats", exc)
    return {}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
