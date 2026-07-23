"""Resources de solo lectura para mcp-tabular.

Expone documentación, metadatos y vistas de archivos tabulares como URIs
accesibles para el modelo a través de `@mcp.resource`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from mcp_shared.logging import get_logger

from mcp_tabular.config import settings
from mcp_tabular.tools.tabular_reader import (
    SUPPORTED_EXTENSIONS,
    _build_column_info,
    _read_dataframe,
    _resolve_path,
    _validate_file_size,
    convert_to_csv,
    get_column_stats,
    get_file_summary,
    get_sheet_names,
)

logger = get_logger(__name__)

_MAX_FILE_SIZE_BYTES_DEFAULT = 100 * 1024 * 1024

SUPPORTED_ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "latin-1",
    "cp1252",
    "iso-8859-1",
    "ascii",
    "utf-16",
    "utf-32",
]

FILTER_OPERATORS = [
    {"operator": "eq", "description": "Igual a (==)."},
    {"operator": "ne", "description": "Diferente a (!=)."},
    {"operator": "gt", "description": "Mayor que (>)."},
    {"operator": "lt", "description": "Menor que (<)."},
    {"operator": "gte", "description": "Mayor o igual que (>=)."},
    {"operator": "lte", "description": "Menor o igual que (<=)."},
    {"operator": "contains", "description": "Contiene el substring (case-insensitive)."},
    {"operator": "startswith", "description": "Empieza con el substring (case-insensitive)."},
]


def _serialize_for_json(value: Any) -> Any:
    """Convierte valores pandas/numpy a tipos nativos de Python serializables."""
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _df_to_markdown(df: pd.DataFrame, max_rows: int = 20) -> str:
    """Genera una tabla Markdown simple a partir de un DataFrame."""
    if df.empty:
        return "*Sin datos para mostrar.*"

    preview = df.head(max_rows)
    headers = "| " + " | ".join(str(c) for c in preview.columns) + " |"
    separator = "|" + "|".join(" --- " for _ in preview.columns) + "|"
    rows: list[str] = []
    for _, row in preview.iterrows():
        cells = "| " + " | ".join(str(_serialize_for_json(v)) for v in row.values) + " |"
        rows.append(cells)
    return "\n".join([headers, separator, *rows])


def _resolve_and_read(
    path: str,
    sheet: str | None = None,
    max_file_size_bytes: int = _MAX_FILE_SIZE_BYTES_DEFAULT,
) -> tuple[pd.DataFrame, Path]:
    """Resuelve la ruta, valida tamaño y lee el archivo en un DataFrame."""
    resolved = _resolve_path(path)
    _validate_file_size(resolved, max_bytes=max_file_size_bytes)
    df, _ = _read_dataframe(resolved, sheet=sheet)
    return df, resolved


# ---------------------------------------------------------------------------
# Resources estáticos
# ---------------------------------------------------------------------------


def supported_formats() -> str:
    """Lista de formatos de archivo soportados."""
    return json.dumps(
        {
            "formats": [
                {"extension": ext, "type": fmt}
                for ext, fmt in SUPPORTED_EXTENSIONS.items()
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def supported_encodings() -> str:
    """Lista de encodings comunes soportados para archivos de texto."""
    return json.dumps({"encodings": SUPPORTED_ENCODINGS}, indent=2, ensure_ascii=False)


def filter_operators() -> str:
    """Operadores de filtrado soportados."""
    return json.dumps({"operators": FILTER_OPERATORS}, indent=2, ensure_ascii=False)


def tips_encoding() -> str:
    """Consejos para manejar encoding en archivos CSV/TSV."""
    return (
        "# Encoding en archivos tabulares\n\n"
        "- Usa UTF-8 siempre que sea posible.\n"
        "- Para archivos de origen Windows, prueba `latin-1` o `cp1252`.\n"
        "- Deja `encoding='auto'` para detectar con chardet.\n"
        "- Si los acentos se ven mal, el encoding probablemente sea ISO-8859-1.\n"
        "- Guarda archivos procesados como UTF-8 para evitar problemas futuros."
    )


def tips_large_files() -> str:
    """Consejos para trabajar con archivos grandes."""
    return (
        "# Archivos tabulares grandes\n\n"
        "- Usa Parquet en lugar de CSV/Excel: ocupa menos y carga más rápido.\n"
        "- Filtra o samplea antes de leer todo el archivo.\n"
        "- Aumenta `TABULAR_MAX_FILE_SIZE_MB` solo si la memoria lo permite.\n"
        "- Para Excel muy grandes, considera convertir a Parquet primero.\n"
        "- Evita abrir archivos de más de 2 GB en memoria sin particionar."
    )


def tips_data_types() -> str:
    """Consejos sobre tipos de datos en pandas."""
    return (
        "# Tipos de datos\n\n"
        "- `int64` / `float64`: números. Revisa valores nulos en enteros.\n"
        "- `object`: usualmente texto; puede ser ineficiente en memoria.\n"
        "- `datetime64[ns]`: fechas. Usa `pd.to_datetime()` si no se detecta.\n"
        "- `bool`: booleanos. Asegúrate de que no haya strings como 'True'.\n"
        "- Categorías: convierte columnas repetitivas a `category` para ahorrar RAM."
    )


def best_practices_csv() -> str:
    """Buenas prácticas para archivos CSV."""
    return (
        "# Buenas prácticas CSV\n\n"
        "- Incluye encabezados en la primera fila.\n"
        "- Usa comas como separador por defecto; TSV para datos con comas.\n"
        "- No mezclar miles de columnas con comas dentro de campos sin comillas.\n"
        "- Guarda con UTF-8 y usa `.csv` como extensión.\n"
        "- Evita filas vacías al inicio o entre los datos."
    )


def best_practices_excel() -> str:
    """Buenas prácticas para archivos Excel."""
    return (
        "# Buenas prácticas Excel\n\n"
        "- Usa `.xlsx` (openpyxl) en vez de `.xls` (formato antiguo).\n"
        "- Nombra las hojas sin caracteres especiales ni espacios.\n"
        "- Evita celdas combinadas; dificultan la lectura programática.\n"
        "- Usa tablas formateadas de Excel para que pandas infiera tipos mejor.\n"
        "- No incluya imágenes o macros si el objetivo es procesar datos."
    )


def best_practices_parquet() -> str:
    """Buenas prácticas para archivos Parquet."""
    return (
        "# Buenas prácticas Parquet\n\n"
        "- Define `dtypes` explícitos al escribir para evitar sorpresas.\n"
        "- Usa particionado por columnas de baja cardinalidad (ej: fecha).\n"
        "- Prefiere `pyarrow` sobre `fastparquet` para compatibilidad.\n"
        "- No modiques un Parquet mientras otros procesos lo lean.\n"
        "- Comprime con snappy para equilibrio velocidad/tamaño."
    )


def example_sample_csv() -> str:
    """Ejemplo de contenido CSV."""
    return "id,nombre,edad,ciudad\n1,Ana,30,CDMX\n2,Luis,25,Guadalajara\n3,María,35,Monterrey\n"


def example_sample_json() -> str:
    """Ejemplo de registro JSON."""
    return json.dumps(
        {
            "columns": ["id", "nombre", "edad", "ciudad"],
            "records": [
                {"id": 1, "nombre": "Ana", "edad": 30, "ciudad": "CDMX"},
                {"id": 2, "nombre": "Luis", "edad": 25, "ciudad": "Guadalajara"},
                {"id": 3, "nombre": "María", "edad": 35, "ciudad": "Monterrey"},
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


def pandas_cheatsheet() -> str:
    """Cheatsheet de pandas para operaciones comunes."""
    return (
        "# Pandas cheatsheet\n\n"
        "- Leer: `pd.read_csv('file.csv')`\n"
        "- Primeras filas: `df.head(n)`\n"
        "- Info: `df.info()` y `df.describe()`\n"
        "- Filtrar: `df[df['col'] > 0]`\n"
        "- Agrupar: `df.groupby('col').agg('mean')`\n"
        "- Pivot: `df.pivot_table(index='a', columns='b', values='c', aggfunc='sum')`\n"
        "- Merge: `pd.merge(df1, df2, on='key', how='inner')`\n"
        "- Rellenar nulos: `df.fillna(0)`"
    )


# ---------------------------------------------------------------------------
# Resources dinámicos sobre archivos
# ---------------------------------------------------------------------------


def file_schema(path: str, sheet: str | None = None) -> str:
    """Esquema de columnas del archivo (nombre, tipo, nulos)."""
    df, resolved = _resolve_and_read(path, sheet=sheet)
    schema = {
        "path": str(resolved),
        "sheet": sheet,
        "columns": _build_column_info(df),
    }
    return json.dumps(schema, indent=2, ensure_ascii=False, default=str)


def file_columns(path: str, sheet: str | None = None) -> str:
    """Nombres de las columnas del archivo."""
    df, resolved = _resolve_and_read(path, sheet=sheet)
    return json.dumps(
        {"path": str(resolved), "columns": [str(c) for c in df.columns]},
        indent=2,
        ensure_ascii=False,
    )


def file_shape(path: str, sheet: str | None = None) -> str:
    """Dimensiones del archivo (filas, columnas)."""
    df, resolved = _resolve_and_read(path, sheet=sheet)
    return json.dumps(
        {"path": str(resolved), "rows": int(df.shape[0]), "columns": int(df.shape[1])},
        indent=2,
        ensure_ascii=False,
    )


def file_dtypes(path: str, sheet: str | None = None) -> str:
    """Tipos de datos por columna."""
    df, resolved = _resolve_and_read(path, sheet=sheet)
    return json.dumps(
        {"path": str(resolved), "dtypes": {str(c): str(t) for c, t in df.dtypes.items()}},
        indent=2,
        ensure_ascii=False,
    )


def file_nulls(path: str, sheet: str | None = None) -> str:
    """Reporte de valores nulos por columna."""
    df, resolved = _resolve_and_read(path, sheet=sheet)
    null_counts = {str(c): int(df[c].isna().sum()) for c in df.columns}
    total = len(df)
    null_percentages = {
        str(c): round((count / total * 100), 2) if total else 0.0
        for c, count in null_counts.items()
    }
    return json.dumps(
        {
            "path": str(resolved),
            "total_rows": total,
            "null_counts": null_counts,
            "null_percentages": null_percentages,
        },
        indent=2,
        ensure_ascii=False,
    )


def file_summary(path: str, sheet: str | None = None) -> str:
    """Resumen estadístico completo del archivo."""
    return json.dumps(
        get_file_summary(
            path=path,
            sheet=sheet,
            max_file_size_mb=settings.max_file_size_mb,
        ),
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def file_preview(path: str, sheet: str | None = None, n: int = 10) -> str:
    """Vista previa en Markdown de las primeras n filas."""
    df, _ = _resolve_and_read(path, sheet=sheet)
    return _df_to_markdown(df.head(n))


def file_head(path: str, sheet: str | None = None, n: int = 10) -> str:
    """Primeras n filas del archivo en Markdown."""
    return file_preview(path=path, sheet=sheet, n=n)


def file_tail(path: str, sheet: str | None = None, n: int = 10) -> str:
    """Últimas n filas del archivo en Markdown."""
    df, _ = _resolve_and_read(path, sheet=sheet)
    return _df_to_markdown(df.tail(n))


def file_csv(path: str, sheet: str | None = None) -> str:
    """Contenido del archivo convertido a CSV."""
    return convert_to_csv(
        path=path,
        sheet=sheet,
        output_encoding="utf-8",
        max_file_size_mb=settings.max_file_size_mb,
    )


def file_sheets(path: str) -> str:
    """Nombres de hojas de un archivo Excel u ODS."""
    return json.dumps(
        {"path": path, "sheets": get_sheet_names(path=path)},
        indent=2,
        ensure_ascii=False,
    )


def file_stats(path: str, column: str, sheet: str | None = None) -> str:
    """Estadísticas detalladas de una columna."""
    return json.dumps(
        get_column_stats(
            path=path,
            column=column,
            sheet=sheet,
            max_file_size_mb=settings.max_file_size_mb,
        ),
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def file_unique(path: str, column: str, sheet: str | None = None) -> str:
    """Valores únicos de una columna."""
    df, resolved = _resolve_and_read(path, sheet=sheet)
    if column not in df.columns:
        raise ValueError(f"La columna '{column}' no existe. Columnas: {list(df.columns)}")
    unique = df[column].dropna().unique()[:100]
    return json.dumps(
        {
            "path": str(resolved),
            "column": column,
            "unique_count": int(df[column].nunique()),
            "unique_values_sample": [_serialize_for_json(v) for v in unique],
        },
        indent=2,
        ensure_ascii=False,
    )
