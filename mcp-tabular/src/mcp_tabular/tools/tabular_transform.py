"""Tools adicionales de transformación y análisis para mcp-tabular.

Estas herramientas extienden las capacidades del servidor con operaciones
comunes de manipulación de datos tabulares: pivot, melt, groupby, sort,
drop, rename, fillna, merge, sample, dedup, export y más.
"""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
from mcp_shared.errors import (
    InvalidValueError,
    ParseError,
    ValidationError,
)
from mcp_shared.logging import get_logger

from mcp_tabular.tools.tabular_reader import (
    _build_standard_response,
    _read_dataframe,
    _resolve_path,
    _validate_file_size,
)

logger = get_logger(__name__)

_MAX_ROWS_DEFAULT = 1000
_MAX_FILE_SIZE_BYTES_DEFAULT = 100 * 1024 * 1024


def _read_df(
    path: str,
    sheet: str | None = None,
    max_file_size_mb: int = 100,
) -> tuple[pd.DataFrame, Any]:
    """Lee un archivo y retorna (DataFrame, Path resuelto)."""
    resolved = _resolve_path(path)
    _validate_file_size(resolved, max_bytes=max_file_size_mb * 1024 * 1024)
    df, _ = _read_dataframe(resolved, sheet=sheet)
    return df, resolved


# ---------------------------------------------------------------------------
# Tools de transformación
# ---------------------------------------------------------------------------


def sort_rows(
    path: str,
    by: str | list[str],
    ascending: bool = True,
    sheet: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Ordena filas por una o más columnas."""
    if isinstance(by, str):
        by = [by]

    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)

    missing = [c for c in by if c not in df.columns]
    if missing:
        raise ValidationError(
            field="by",
            message=f"Columnas no encontradas: {missing}. Disponibles: {list(df.columns)}",
        )

    df_sorted = df.sort_values(by=by, ascending=ascending)
    return _build_standard_response(
        df=df_sorted, path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=max_rows,
    )


def drop_columns(
    path: str,
    columns: str | list[str],
    sheet: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Elimina columnas del archivo."""
    if isinstance(columns, str):
        columns = [columns]

    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)

    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValidationError(
            field="columns",
            message=f"Columnas no encontradas: {missing}. Disponibles: {list(df.columns)}",
        )

    df_dropped = df.drop(columns=columns)
    return _build_standard_response(
        df=df_dropped, path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=max_rows,
    )


def select_columns(
    path: str,
    columns: str | list[str],
    sheet: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Selecciona solo las columnas especificadas."""
    if isinstance(columns, str):
        columns = [columns]

    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)

    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValidationError(
            field="columns",
            message=f"Columnas no encontradas: {missing}. Disponibles: {list(df.columns)}",
        )

    df_selected = df[columns]
    return _build_standard_response(
        df=df_selected, path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=max_rows,
    )


def rename_columns(
    path: str,
    mapping: dict[str, str],
    sheet: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Renombra columnas usando un diccionario {old: new}."""
    if not mapping:
        raise ValidationError(field="mapping", message="El mapeo no puede estar vacío.")

    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)
    df_renamed = df.rename(columns=mapping)
    return _build_standard_response(
        df=df_renamed, path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=max_rows,
    )


def fill_nulls(
    path: str,
    value: Any = 0,
    columns: str | list[str] | None = None,
    sheet: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Rellena valores nulos con un valor dado."""
    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)

    if columns is not None:
        if isinstance(columns, str):
            columns = [columns]
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise ValidationError(
                field="columns",
                message=f"Columnas no encontradas: {missing}. Disponibles: {list(df.columns)}",
            )
        df_filled = df.copy()
        df_filled[columns] = df_filled[columns].fillna(value)
    else:
        df_filled = df.fillna(value)

    return _build_standard_response(
        df=df_filled, path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=max_rows,
    )


def drop_nulls(
    path: str,
    how: str = "any",
    subset: str | list[str] | None = None,
    sheet: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Elimina filas con valores nulos."""
    valid_how = {"any", "all"}
    if how not in valid_how:
        raise InvalidValueError(
            field="how", value=how,
            reason=f"'how' debe ser uno de: {valid_how}",
        )

    if isinstance(subset, str):
        subset = [subset]

    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)
    df_clean = df.dropna(how=how, subset=subset)
    return _build_standard_response(
        df=df_clean, path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=max_rows,
    )


def drop_duplicates(
    path: str,
    subset: str | list[str] | None = None,
    keep: str = "first",
    sheet: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Elimina filas duplicadas."""
    valid_keep = {"first", "last", "false"}
    if keep not in valid_keep:
        raise InvalidValueError(
            field="keep", value=keep,
            reason=f"'keep' debe ser uno de: {valid_keep}",
        )

    keep_val: bool | str = False if keep == "false" else keep

    if isinstance(subset, str):
        subset = [subset]

    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)
    df_dedup = df.drop_duplicates(subset=subset, keep=keep_val)
    return _build_standard_response(
        df=df_dedup, path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=max_rows,
    )


def groupby_agg(
    path: str,
    by: str | list[str],
    agg_func: str = "mean",
    sheet: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Agrupa por columnas y aplica una función de agregación."""
    valid_funcs = {
        "mean", "sum", "min", "max", "count", "median",
        "std", "var", "first", "last", "nunique",
    }
    if agg_func not in valid_funcs:
        raise InvalidValueError(
            field="agg_func", value=agg_func,
            reason=f"Función no válida. Soportadas: {sorted(valid_funcs)}",
        )

    if isinstance(by, str):
        by = [by]

    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)

    missing = [c for c in by if c not in df.columns]
    if missing:
        raise ValidationError(
            field="by",
            message=f"Columnas no encontradas: {missing}. Disponibles: {list(df.columns)}",
        )

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    group_cols = [c for c in numeric_cols if c not in by]

    if not group_cols:
        grouped = df.groupby(by).size().reset_index(name="count")
    else:
        grouped = df.groupby(by)[group_cols].agg(agg_func).reset_index()

    return _build_standard_response(
        df=grouped, path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=max_rows,
    )


def pivot_table(
    path: str,
    index: str,
    columns: str,
    values: str,
    aggfunc: str = "mean",
    sheet: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Crea una tabla pivot desde el archivo."""
    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)

    for col_name, col_val in [("index", index), ("columns", columns), ("values", values)]:
        if col_val not in df.columns:
            raise ValidationError(
                field=col_name,
                message=f"Columna '{col_val}' no existe. Disponibles: {list(df.columns)}",
            )

    try:
        pivoted = df.pivot_table(
            index=index, columns=columns, values=values, aggfunc=aggfunc,
        ).reset_index()
    except Exception as exc:
        raise ParseError(source=str(resolved), reason=f"Error en pivot: {exc}") from exc

    return _build_standard_response(
        df=pivoted, path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=max_rows,
    )


def melt_table(
    path: str,
    id_vars: str | list[str],
    value_vars: str | list[str] | None = None,
    sheet: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Convierte de formato ancho a largo (melt)."""
    if isinstance(id_vars, str):
        id_vars = [id_vars]
    if isinstance(value_vars, str):
        value_vars = [value_vars]

    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)

    melted = df.melt(id_vars=id_vars, value_vars=value_vars)
    return _build_standard_response(
        df=melted, path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=max_rows,
    )


def sample_rows(
    path: str,
    n: int = 10,
    random_state: int | None = None,
    sheet: str | None = None,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Retorna una muestra aleatoria de n filas."""
    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)

    sample_n = min(n, len(df))
    df_sample = df.sample(n=sample_n, random_state=random_state)
    return _build_standard_response(
        df=df_sample, path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=_MAX_ROWS_DEFAULT,
    )


def head_rows(
    path: str,
    n: int = 10,
    sheet: str | None = None,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Retorna las primeras n filas."""
    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)
    return _build_standard_response(
        df=df.head(n), path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=n,
    )


def tail_rows(
    path: str,
    n: int = 10,
    sheet: str | None = None,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Retorna las últimas n filas."""
    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)
    return _build_standard_response(
        df=df.tail(n), path=resolved, fmt=resolved.suffix.lstrip("."),
        sheet=sheet, max_rows=n,
    )


def convert_to_json(
    path: str,
    sheet: str | None = None,
    orient: str = "records",
    max_file_size_mb: int = 100,
) -> str:
    """Convierte un archivo tabular a JSON."""
    df, _ = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)
    return df.to_json(orient=orient, force_ascii=False, date_format="iso")


def convert_to_markdown(
    path: str,
    sheet: str | None = None,
    max_rows: int = 50,
    max_file_size_mb: int = 100,
) -> str:
    """Convierte un archivo tabular a tabla Markdown."""
    from mcp_tabular.resources import _df_to_markdown

    df, _ = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)
    return _df_to_markdown(df, max_rows=max_rows)


def get_duplicates_info(
    path: str,
    subset: str | list[str] | None = None,
    sheet: str | None = None,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Reporta filas duplicadas en el archivo."""
    if isinstance(subset, str):
        subset = [subset]

    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)
    dup_mask = df.duplicated(subset=subset, keep=False)
    dup_count = int(dup_mask.sum())
    dup_rows = df[dup_mask].head(20)

    from mcp_tabular.tools.tabular_reader import _df_to_records

    return {
        "path": str(resolved),
        "total_rows": len(df),
        "duplicate_rows": dup_count,
        "duplicate_percentage": round(dup_count / len(df) * 100, 2) if len(df) else 0.0,
        "sample_duplicates": _df_to_records(dup_rows),
    }


def get_correlation(
    path: str,
    method: str = "pearson",
    sheet: str | None = None,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """Matriz de correlación de columnas numéricas."""
    valid_methods = {"pearson", "spearman", "kendall"}
    if method not in valid_methods:
        raise InvalidValueError(
            field="method", value=method,
            reason=f"Método no válido. Soportados: {sorted(valid_methods)}",
        )

    df, resolved = _read_df(path, sheet=sheet, max_file_size_mb=max_file_size_mb)
    numeric_df = df.select_dtypes(include=["number"])

    if numeric_df.empty:
        return {
            "path": str(resolved),
            "method": method,
            "correlation": {},
            "message": "No hay columnas numéricas para correlación.",
        }

    corr = numeric_df.corr(method=method)
    corr_dict = {}
    for col in corr.columns:
        corr_dict[str(col)] = {
            str(idx): round(float(val), 4) if not pd.isna(val) else None
            for idx, val in corr[col].items()
        }

    return {
        "path": str(resolved),
        "method": method,
        "correlation": corr_dict,
    }
