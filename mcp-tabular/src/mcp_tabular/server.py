"""
Servidor FastMCP para mcp-tabular.

Expone tools para leer, filtrar, buscar, transformar y analizar archivos
tabulares (Excel, CSV, ODS, TSV, Parquet) y resources con documentación,
metadatos y vistas de archivos.

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
from mcp_tabular.config import settings
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
from mcp_tabular.tools.tabular_transform import (
    convert_to_json,
    convert_to_markdown,
    drop_columns,
    drop_duplicates,
    drop_nulls,
    fill_nulls,
    get_correlation,
    get_duplicates_info,
    groupby_agg,
    head_rows,
    melt_table,
    pivot_table,
    rename_columns,
    sample_rows,
    select_columns,
    sort_rows,
    tail_rows,
)
from mcp_tabular import resources as res

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

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
    raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor."))


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
# Tools de transformación (tabular_transform)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="sort_rows",
    description=(
        "Ordena las filas del archivo por una o más columnas. "
        "Parámetros: path, by (nombre de columna o lista), ascending (bool, default true), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file con las filas ordenadas."
    ),
)
def tool_sort_rows(
    path: str,
    by: str | list[str],
    ascending: bool = True,
    sheet: str | None = None,
) -> dict[str, Any]:
    """Ordena filas por columnas."""
    try:
        return sort_rows(
            path=path, by=by, ascending=ascending, sheet=sheet,
            max_rows=settings.max_rows_preview, max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("sort_rows", exc)
    except Exception as exc:
        _handle_unexpected_error("sort_rows", exc)
    return {}


@mcp.tool(
    name="drop_columns",
    description=(
        "Elimina columnas específicas del archivo. "
        "Parámetros: path, columns (nombre o lista de columnas a eliminar), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file sin las columnas eliminadas."
    ),
)
def tool_drop_columns(
    path: str,
    columns: str | list[str],
    sheet: str | None = None,
) -> dict[str, Any]:
    """Elimina columnas del archivo."""
    try:
        return drop_columns(
            path=path, columns=columns, sheet=sheet,
            max_rows=settings.max_rows_preview, max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("drop_columns", exc)
    except Exception as exc:
        _handle_unexpected_error("drop_columns", exc)
    return {}


@mcp.tool(
    name="select_columns",
    description=(
        "Selecciona solo las columnas especificadas, descartando las demás. "
        "Parámetros: path, columns (nombre o lista de columnas a conservar), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file con solo las columnas seleccionadas."
    ),
)
def tool_select_columns(
    path: str,
    columns: str | list[str],
    sheet: str | None = None,
) -> dict[str, Any]:
    """Selecciona columnas específicas."""
    try:
        return select_columns(
            path=path, columns=columns, sheet=sheet,
            max_rows=settings.max_rows_preview, max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("select_columns", exc)
    except Exception as exc:
        _handle_unexpected_error("select_columns", exc)
    return {}


@mcp.tool(
    name="rename_columns",
    description=(
        "Renombra columnas del archivo usando un diccionario {nombre_antiguo: nombre_nuevo}. "
        "Parámetros: path, mapping (dict de renombrado), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file con las columnas renombradas."
    ),
)
def tool_rename_columns(
    path: str,
    mapping: dict[str, str],
    sheet: str | None = None,
) -> dict[str, Any]:
    """Renombra columnas."""
    try:
        return rename_columns(
            path=path, mapping=mapping, sheet=sheet,
            max_rows=settings.max_rows_preview, max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("rename_columns", exc)
    except Exception as exc:
        _handle_unexpected_error("rename_columns", exc)
    return {}


@mcp.tool(
    name="fill_nulls",
    description=(
        "Rellena valores nulos (NaN) con un valor dado. "
        "Parámetros: path, value (valor de relleno, default 0), "
        "columns (lista opcional de columnas a rellenar; si es None, rellena todas), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file con los nulos rellenados."
    ),
)
def tool_fill_nulls(
    path: str,
    value: Any = 0,
    columns: str | list[str] | None = None,
    sheet: str | None = None,
) -> dict[str, Any]:
    """Rellena valores nulos."""
    try:
        return fill_nulls(
            path=path, value=value, columns=columns, sheet=sheet,
            max_rows=settings.max_rows_preview, max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("fill_nulls", exc)
    except Exception as exc:
        _handle_unexpected_error("fill_nulls", exc)
    return {}


@mcp.tool(
    name="drop_nulls",
    description=(
        "Elimina filas que contienen valores nulos. "
        "Parámetros: path, how ('any' = cualquier nulo, 'all' = todos nulos, default 'any'), "
        "subset (columnas específicas a considerar, opcional), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file sin las filas con nulos."
    ),
)
def tool_drop_nulls(
    path: str,
    how: str = "any",
    subset: str | list[str] | None = None,
    sheet: str | None = None,
) -> dict[str, Any]:
    """Elimina filas con nulos."""
    try:
        return drop_nulls(
            path=path, how=how, subset=subset, sheet=sheet,
            max_rows=settings.max_rows_preview, max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("drop_nulls", exc)
    except Exception as exc:
        _handle_unexpected_error("drop_nulls", exc)
    return {}


@mcp.tool(
    name="drop_duplicates",
    description=(
        "Elimina filas duplicadas del archivo. "
        "Parámetros: path, subset (columnas a considerar para duplicados, opcional), "
        "keep ('first' = mantener primero, 'last' = mantener último, 'false' = eliminar todos), "
        "sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file sin duplicados."
    ),
)
def tool_drop_duplicates(
    path: str,
    subset: str | list[str] | None = None,
    keep: str = "first",
    sheet: str | None = None,
) -> dict[str, Any]:
    """Elimina filas duplicadas."""
    try:
        return drop_duplicates(
            path=path, subset=subset, keep=keep, sheet=sheet,
            max_rows=settings.max_rows_preview, max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("drop_duplicates", exc)
    except Exception as exc:
        _handle_unexpected_error("drop_duplicates", exc)
    return {}


@mcp.tool(
    name="groupby_agg",
    description=(
        "Agrupa filas por una o más columnas y aplica una función de agregación. "
        "Funciones soportadas: mean, sum, min, max, count, median, std, var, first, last, nunique. "
        "Parámetros: path, by (columna o lista de agrupación), agg_func (función de agregación), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file con el resultado agrupado."
    ),
)
def tool_groupby_agg(
    path: str,
    by: str | list[str],
    agg_func: str = "mean",
    sheet: str | None = None,
) -> dict[str, Any]:
    """Agrupa y agrega."""
    try:
        return groupby_agg(
            path=path, by=by, agg_func=agg_func, sheet=sheet,
            max_rows=settings.max_rows_preview, max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("groupby_agg", exc)
    except Exception as exc:
        _handle_unexpected_error("groupby_agg", exc)
    return {}


@mcp.tool(
    name="pivot_table",
    description=(
        "Crea una tabla pivot desde el archivo tabular. "
        "Parámetros: path, index (columna de filas), columns (columna de columnas), "
        "values (columna de valores), aggfunc (función de agregación, default 'mean'), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file con la tabla pivot."
    ),
)
def tool_pivot_table(
    path: str,
    index: str,
    columns: str,
    values: str,
    aggfunc: str = "mean",
    sheet: str | None = None,
) -> dict[str, Any]:
    """Crea tabla pivot."""
    try:
        return pivot_table(
            path=path, index=index, columns=columns, values=values,
            aggfunc=aggfunc, sheet=sheet,
            max_rows=settings.max_rows_preview, max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("pivot_table", exc)
    except Exception as exc:
        _handle_unexpected_error("pivot_table", exc)
    return {}


@mcp.tool(
    name="melt_table",
    description=(
        "Convierte el archivo de formato ancho a largo (unpivot/melt). "
        "Parámetros: path, id_vars (columnas que se mantienen), "
        "value_vars (columnas a despivotar, opcional), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file en formato largo."
    ),
)
def tool_melt_table(
    path: str,
    id_vars: str | list[str],
    value_vars: str | list[str] | None = None,
    sheet: str | None = None,
) -> dict[str, Any]:
    """Convierte ancho a largo."""
    try:
        return melt_table(
            path=path, id_vars=id_vars, value_vars=value_vars, sheet=sheet,
            max_rows=settings.max_rows_preview, max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("melt_table", exc)
    except Exception as exc:
        _handle_unexpected_error("melt_table", exc)
    return {}


@mcp.tool(
    name="sample_rows",
    description=(
        "Retorna una muestra aleatoria de n filas del archivo. "
        "Parámetros: path, n (número de filas, default 10), random_state (semilla, opcional), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file con la muestra."
    ),
)
def tool_sample_rows(
    path: str,
    n: int = 10,
    random_state: int | None = None,
    sheet: str | None = None,
) -> dict[str, Any]:
    """Muestra aleatoria de filas."""
    try:
        return sample_rows(
            path=path, n=n, random_state=random_state, sheet=sheet,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("sample_rows", exc)
    except Exception as exc:
        _handle_unexpected_error("sample_rows", exc)
    return {}


@mcp.tool(
    name="head_rows",
    description=(
        "Retorna las primeras n filas del archivo. "
        "Parámetros: path, n (número de filas, default 10), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file."
    ),
)
def tool_head_rows(
    path: str,
    n: int = 10,
    sheet: str | None = None,
) -> dict[str, Any]:
    """Primeras n filas."""
    try:
        return head_rows(
            path=path, n=n, sheet=sheet,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("head_rows", exc)
    except Exception as exc:
        _handle_unexpected_error("head_rows", exc)
    return {}


@mcp.tool(
    name="tail_rows",
    description=(
        "Retorna las últimas n filas del archivo. "
        "Parámetros: path, n (número de filas, default 10), sheet (opcional). "
        "Retorna: mismo formato que read_tabular_file."
    ),
)
def tool_tail_rows(
    path: str,
    n: int = 10,
    sheet: str | None = None,
) -> dict[str, Any]:
    """Últimas n filas."""
    try:
        return tail_rows(
            path=path, n=n, sheet=sheet,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("tail_rows", exc)
    except Exception as exc:
        _handle_unexpected_error("tail_rows", exc)
    return {}


@mcp.tool(
    name="convert_to_json",
    description=(
        "Convierte un archivo tabular a formato JSON. "
        "Parámetros: path, sheet (opcional), orient ('records', 'index', 'columns', 'values', 'split'). "
        "Retorna: string JSON completo."
    ),
)
def tool_convert_to_json(
    path: str,
    sheet: str | None = None,
    orient: str = "records",
) -> str:
    """Convierte a JSON."""
    try:
        return convert_to_json(
            path=path, sheet=sheet, orient=orient,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("convert_to_json", exc)
    except Exception as exc:
        _handle_unexpected_error("convert_to_json", exc)
    return ""


@mcp.tool(
    name="convert_to_markdown",
    description=(
        "Convierte un archivo tabular a tabla Markdown. "
        "Parámetros: path, sheet (opcional), max_rows (límite de filas, default 50). "
        "Retorna: string con tabla Markdown."
    ),
)
def tool_convert_to_markdown(
    path: str,
    sheet: str | None = None,
    max_rows: int = 50,
) -> str:
    """Convierte a Markdown."""
    try:
        return convert_to_markdown(
            path=path, sheet=sheet, max_rows=max_rows,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("convert_to_markdown", exc)
    except Exception as exc:
        _handle_unexpected_error("convert_to_markdown", exc)
    return ""


@mcp.tool(
    name="get_duplicates_info",
    description=(
        "Reporta filas duplicadas en el archivo con conteo y muestra. "
        "Parámetros: path, subset (columnas a considerar, opcional), sheet (opcional). "
        "Retorna: dict con total_rows, duplicate_rows, duplicate_percentage, sample_duplicates."
    ),
)
def tool_get_duplicates_info(
    path: str,
    subset: str | list[str] | None = None,
    sheet: str | None = None,
) -> dict[str, Any]:
    """Reporta duplicados."""
    try:
        return get_duplicates_info(
            path=path, subset=subset, sheet=sheet,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("get_duplicates_info", exc)
    except Exception as exc:
        _handle_unexpected_error("get_duplicates_info", exc)
    return {}


@mcp.tool(
    name="get_correlation",
    description=(
        "Calcula la matriz de correlación entre columnas numéricas. "
        "Métodos soportados: pearson, spearman, kendall. "
        "Parámetros: path, method (default 'pearson'), sheet (opcional). "
        "Retorna: dict con la matriz de correlación."
    ),
)
def tool_get_correlation(
    path: str,
    method: str = "pearson",
    sheet: str | None = None,
) -> dict[str, Any]:
    """Matriz de correlación."""
    try:
        return get_correlation(
            path=path, method=method, sheet=sheet,
            max_file_size_mb=settings.max_file_size_mb,
        )
    except McpError as exc:
        _handle_mcp_error("get_correlation", exc)
    except Exception as exc:
        _handle_unexpected_error("get_correlation", exc)
    return {}


# ---------------------------------------------------------------------------
# Resources (solo lectura)
# ---------------------------------------------------------------------------


@mcp.resource("tabular://supported-formats")
def res_supported_formats() -> str:
    """Formatos de archivo soportados por el servidor."""
    return res.supported_formats()


@mcp.resource("tabular://supported-encodings")
def res_supported_encodings() -> str:
    """Encodings comunes soportados para CSV/TSV."""
    return res.supported_encodings()


@mcp.resource("tabular://filter-operators")
def res_filter_operators() -> str:
    """Operadores de filtrado disponibles."""
    return res.filter_operators()


@mcp.resource("tabular://tips/encoding")
def res_tips_encoding() -> str:
    """Consejos para manejar encoding."""
    return res.tips_encoding()


@mcp.resource("tabular://tips/large-files")
def res_tips_large_files() -> str:
    """Consejos para archivos grandes."""
    return res.tips_large_files()


@mcp.resource("tabular://tips/data-types")
def res_tips_data_types() -> str:
    """Consejos sobre tipos de datos en pandas."""
    return res.tips_data_types()


@mcp.resource("tabular://best-practices/csv")
def res_best_practices_csv() -> str:
    """Buenas prácticas para CSV."""
    return res.best_practices_csv()


@mcp.resource("tabular://best-practices/excel")
def res_best_practices_excel() -> str:
    """Buenas prácticas para Excel."""
    return res.best_practices_excel()


@mcp.resource("tabular://best-practices/parquet")
def res_best_practices_parquet() -> str:
    """Buenas prácticas para Parquet."""
    return res.best_practices_parquet()


@mcp.resource("tabular://examples/sample-csv")
def res_example_sample_csv() -> str:
    """Ejemplo de contenido CSV."""
    return res.example_sample_csv()


@mcp.resource("tabular://examples/sample-json")
def res_example_sample_json() -> str:
    """Ejemplo de registro JSON."""
    return res.example_sample_json()


@mcp.resource("tabular://cheatsheet/pandas")
def res_pandas_cheatsheet() -> str:
    """Cheatsheet de pandas."""
    return res.pandas_cheatsheet()


@mcp.resource("tabular://file/{path}/schema")
def res_file_schema(path: str) -> str:
    """Esquema de columnas del archivo."""
    return res.file_schema(path=path)


@mcp.resource("tabular://file/{path}/columns")
def res_file_columns(path: str) -> str:
    """Nombres de columnas del archivo."""
    return res.file_columns(path=path)


@mcp.resource("tabular://file/{path}/shape")
def res_file_shape(path: str) -> str:
    """Dimensiones del archivo."""
    return res.file_shape(path=path)


@mcp.resource("tabular://file/{path}/dtypes")
def res_file_dtypes(path: str) -> str:
    """Tipos de datos por columna."""
    return res.file_dtypes(path=path)


@mcp.resource("tabular://file/{path}/nulls")
def res_file_nulls(path: str) -> str:
    """Reporte de valores nulos."""
    return res.file_nulls(path=path)


@mcp.resource("tabular://file/{path}/summary")
def res_file_summary(path: str) -> str:
    """Resumen estadístico del archivo."""
    return res.file_summary(path=path)


@mcp.resource("tabular://file/{path}/preview")
def res_file_preview(path: str) -> str:
    """Vista previa en Markdown."""
    return res.file_preview(path=path)


@mcp.resource("tabular://file/{path}/head")
def res_file_head(path: str) -> str:
    """Primeras filas en Markdown."""
    return res.file_head(path=path)


@mcp.resource("tabular://file/{path}/tail")
def res_file_tail(path: str) -> str:
    """Últimas filas en Markdown."""
    return res.file_tail(path=path)


@mcp.resource("tabular://file/{path}/csv")
def res_file_csv(path: str) -> str:
    """Archivo convertido a CSV."""
    return res.file_csv(path=path)


@mcp.resource("tabular://file/{path}/sheets")
def res_file_sheets(path: str) -> str:
    """Hojas de un archivo Excel/ODS."""
    return res.file_sheets(path=path)


@mcp.resource("tabular://file/{path}/column/{column}/stats")
def res_file_stats(path: str, column: str) -> str:
    """Estadísticas de una columna."""
    return res.file_stats(path=path, column=column)


@mcp.resource("tabular://file/{path}/column/{column}/unique")
def res_file_unique(path: str, column: str) -> str:
    """Valores únicos de una columna."""
    return res.file_unique(path=path, column=column)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
