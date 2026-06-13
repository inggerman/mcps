"""
Implementación de todas las tools de lectura y análisis de archivos tabulares.

Soporta los siguientes formatos:
- Excel: .xlsx (openpyxl), .xls (xlrd)
- Texto delimitado: .csv, .tsv (pandas + chardet para detección de encoding)
- OpenDocument: .ods (odfpy)
- Columnar: .parquet (pyarrow)

Todas las funciones retornan tipos serializables a JSON o raise McpError.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Literal

import chardet
import pandas as pd
from mcp_shared.errors import (
    FileReadError,
    InvalidValueError,
    ParseError,
    UnsupportedFormatError,
    ValidationError,
)
from mcp_shared.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".xlsx": "excel",
    ".xls": "excel",
    ".csv": "csv",
    ".tsv": "tsv",
    ".ods": "ods",
    ".parquet": "parquet",
}

FILTER_OPERATORS = Literal["eq", "ne", "gt", "lt", "gte", "lte", "contains", "startswith"]

_MAX_ROWS_DEFAULT = 1000
_MAX_FILE_SIZE_BYTES_DEFAULT = 100 * 1024 * 1024  # 100 MB
_SAMPLE_VALUES_COUNT = 5


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _resolve_path(path: str) -> Path:
    """
    Resuelve y valida la ruta de un archivo.

    Args:
        path: Ruta absoluta o relativa al archivo.

    Returns:
        Path absoluto al archivo existente.

    Raises:
        mcp_shared.errors.FileNotFoundError: Si el archivo no existe.
        ValidationError: Si la ruta está vacía.
    """
    if not path or not path.strip():
        raise ValidationError(field="path", message="La ruta del archivo no puede estar vacía.")

    resolved = Path(path).expanduser().resolve()

    if not resolved.exists():
        from mcp_shared.errors import FileNotFoundError as McpFileNotFoundError

        raise McpFileNotFoundError(file_path=str(resolved))

    if not resolved.is_file():
        raise ValidationError(
            field="path",
            message=f"La ruta no apunta a un archivo: '{resolved}'",
        )

    return resolved


def _validate_file_size(path: Path, max_bytes: int = _MAX_FILE_SIZE_BYTES_DEFAULT) -> None:
    """
    Valida que el archivo no supere el tamaño máximo permitido.

    Args:
        path: Ruta al archivo.
        max_bytes: Tamaño máximo en bytes.

    Raises:
        ValidationError: Si el archivo supera el tamaño máximo.
    """
    size = path.stat().st_size
    if size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = size / (1024 * 1024)
        raise ValidationError(
            field="path",
            message=(
                f"El archivo supera el tamaño máximo permitido de {max_mb:.0f} MB "
                f"(tamaño actual: {actual_mb:.1f} MB)."
            ),
        )


def _detect_encoding(path: Path, confidence_threshold: float = 0.7) -> str:
    """
    Detecta el encoding de un archivo de texto con chardet.

    Lee los primeros 64 KB del archivo para la detección (más rápido y suficiente).

    Args:
        path: Ruta al archivo de texto.
        confidence_threshold: Confianza mínima requerida para aceptar la detección.

    Returns:
        Nombre del encoding detectado (ej: 'utf-8', 'latin-1').
    """
    sample_size = 65536  # 64 KB
    with path.open("rb") as f:
        raw = f.read(sample_size)

    result = chardet.detect(raw)
    encoding = result.get("encoding") or "utf-8"
    confidence = result.get("confidence") or 0.0

    logger.debug(
        "Encoding detectado",
        file=str(path),
        encoding=encoding,
        confidence=confidence,
    )

    if confidence < confidence_threshold:
        logger.warning(
            "Confianza de detección de encoding baja, usando utf-8",
            file=str(path),
            detected_encoding=encoding,
            confidence=confidence,
            fallback="utf-8",
        )
        return "utf-8"

    return encoding


def _get_file_format(path: Path) -> str:
    """
    Determina el formato del archivo por su extensión.

    Args:
        path: Ruta al archivo.

    Returns:
        Identificador de formato ('excel', 'csv', 'tsv', 'ods', 'parquet').

    Raises:
        UnsupportedFormatError: Si la extensión no está soportada.
    """
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFormatError(
            format_name=ext or "(sin extensión)",
            supported_formats=list(SUPPORTED_EXTENSIONS.keys()),
        )
    return SUPPORTED_EXTENSIONS[ext]


def _read_dataframe(
    path: Path,
    sheet: str | None = None,
    encoding: str = "auto",
) -> tuple[pd.DataFrame, str | None]:
    """
    Lee un archivo tabular en un DataFrame de pandas.

    Args:
        path: Ruta al archivo.
        sheet: Nombre o índice de hoja (solo para Excel/ODS).
        encoding: 'auto' para detección automática con chardet, o nombre de encoding.

    Returns:
        Tupla de (DataFrame, encoding_utilizado | None).

    Raises:
        UnsupportedFormatError: Si el formato no está soportado.
        ParseError: Si el archivo no puede ser parseado.
        FileReadError: Si hay un error de I/O al leer el archivo.
    """
    fmt = _get_file_format(path)
    used_encoding: str | None = None

    try:
        if fmt == "excel":
            engine = "openpyxl" if path.suffix.lower() == ".xlsx" else "xlrd"
            kwargs: dict[str, Any] = {"engine": engine}
            if sheet is not None:
                kwargs["sheet_name"] = sheet
            df = pd.read_excel(path, **kwargs)

        elif fmt == "ods":
            kwargs = {"engine": "odf"}
            if sheet is not None:
                kwargs["sheet_name"] = sheet
            df = pd.read_excel(path, **kwargs)

        elif fmt == "csv":
            if encoding == "auto":
                used_encoding = _detect_encoding(path)
            else:
                used_encoding = encoding
            df = pd.read_csv(path, encoding=used_encoding, low_memory=False)

        elif fmt == "tsv":
            if encoding == "auto":
                used_encoding = _detect_encoding(path)
            else:
                used_encoding = encoding
            df = pd.read_csv(path, sep="\t", encoding=used_encoding, low_memory=False)

        elif fmt == "parquet":
            df = pd.read_parquet(path, engine="pyarrow")

        else:
            raise UnsupportedFormatError(
                format_name=fmt,
                supported_formats=list(SUPPORTED_EXTENSIONS.keys()),
            )

    except UnsupportedFormatError:
        raise
    except OSError as exc:
        raise FileReadError(
            file_path=str(path),
            reason=str(exc),
        ) from exc
    except Exception as exc:
        raise ParseError(
            source=str(path),
            reason=str(exc),
        ) from exc

    return df, used_encoding


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Convierte un DataFrame en una lista de dicts serializable a JSON.

    Maneja tipos especiales de pandas (NaT, NA, Timestamp, numpy types).

    Args:
        df: DataFrame a convertir.

    Returns:
        Lista de diccionarios con valores JSON-serializables.
    """
    records = []
    for _, row in df.iterrows():
        record: dict[str, Any] = {}
        for col, value in row.items():
            if pd.isna(value) if not isinstance(value, (list, dict, str)) else False:
                record[str(col)] = None
            elif isinstance(value, pd.Timestamp):
                record[str(col)] = value.isoformat()
            elif hasattr(value, "item"):
                # numpy scalar → Python native
                record[str(col)] = value.item()
            else:
                record[str(col)] = value
        records.append(record)
    return records


def _build_column_info(
    df: pd.DataFrame, sample_count: int = _SAMPLE_VALUES_COUNT
) -> list[dict[str, Any]]:
    """
    Construye metadatos de columnas del DataFrame.

    Args:
        df: DataFrame fuente.
        sample_count: Cantidad de valores de muestra a incluir por columna.

    Returns:
        Lista de dicts con info de cada columna (name, dtype, nullable, null_count, sample_values).
    """
    column_info = []
    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        non_null = series.dropna()

        # Obtener sample de valores únicos no-nulos
        unique_vals = non_null.unique()[:sample_count]
        samples: list[Any] = []
        for v in unique_vals:
            if isinstance(v, pd.Timestamp):
                samples.append(v.isoformat())
            elif hasattr(v, "item"):
                samples.append(v.item())
            else:
                samples.append(v)

        column_info.append(
            {
                "name": str(col),
                "dtype": str(series.dtype),
                "nullable": null_count > 0,
                "null_count": null_count,
                "sample_values": samples,
            }
        )
    return column_info


def _build_standard_response(
    df: pd.DataFrame,
    path: Path,
    fmt: str,
    sheet: str | None = None,
    encoding: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
) -> dict[str, Any]:
    """
    Construye la respuesta estándar serializable a JSON a partir de un DataFrame.

    Args:
        df: DataFrame fuente.
        path: Ruta al archivo fuente.
        fmt: Formato del archivo (xlsx, csv, etc.).
        sheet: Nombre de hoja si aplica.
        encoding: Encoding detectado/usado si aplica.
        max_rows: Límite de filas en la respuesta.

    Returns:
        Diccionario JSON-serializable con columns, records, total_rows, etc.
    """
    total_rows = len(df)
    truncated = total_rows > max_rows

    if truncated:
        df_out = df.head(max_rows)
        logger.warning(
            "Dataset truncado al límite de filas",
            total_rows=total_rows,
            max_rows=max_rows,
            file=str(path),
        )
    else:
        df_out = df

    warnings: list[str] = []
    if truncated:
        warnings.append(
            f"Dataset truncado a {max_rows} filas. El archivo tiene {total_rows} filas en total."
        )

    return {
        "columns": _build_column_info(df),
        "records": _df_to_records(df_out),
        "total_rows": total_rows,
        "returned_rows": len(df_out),
        "truncated": truncated,
        "metadata": {
            "path": str(path),
            "format": fmt,
            "size_bytes": path.stat().st_size,
            "sheet_name": sheet,
            "encoding": encoding,
        },
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Tools públicas
# ---------------------------------------------------------------------------


def read_tabular_file(
    path: str,
    sheet: str | None = None,
    encoding: str = "auto",
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """
    Lee un archivo tabular (xlsx, xls, csv, ods, tsv, parquet) y retorna datos estructurados.

    Detecta automáticamente el formato por extensión. Para CSV/TSV detecta el encoding
    automáticamente con chardet si encoding='auto'.

    Args:
        path: Ruta absoluta o relativa al archivo tabular.
        sheet: Nombre o índice de hoja para archivos Excel/ODS (None = primera hoja).
        encoding: 'auto' para detección automática, o nombre de encoding (ej: 'utf-8', 'latin-1').
        max_rows: Número máximo de filas a retornar (el resto se trunca).
        max_file_size_mb: Tamaño máximo de archivo en MB.

    Returns:
        Diccionario con:
          - columns: Lista de metadatos de columnas.
          - records: Lista de filas como dicts.
          - total_rows: Total de filas en el archivo.
          - returned_rows: Filas efectivamente retornadas.
          - truncated: True si se truncaron filas.
          - metadata: Metadatos del archivo (path, format, size_bytes, sheet_name, encoding).
          - warnings: Lista de advertencias no fatales.

    Raises:
        McpError: Si el archivo no existe, el formato no está soportado, o hay errores de parseo.
    """
    logger.info("Leyendo archivo tabular", path=path, sheet=sheet, encoding=encoding)

    resolved = _resolve_path(path)
    _validate_file_size(resolved, max_bytes=max_file_size_mb * 1024 * 1024)

    fmt = _get_file_format(resolved)
    df, used_encoding = _read_dataframe(resolved, sheet=sheet, encoding=encoding)

    logger.info(
        "Archivo leído exitosamente",
        path=str(resolved),
        format=fmt,
        rows=len(df),
        columns=len(df.columns),
    )

    return _build_standard_response(
        df=df,
        path=resolved,
        fmt=resolved.suffix.lstrip("."),
        sheet=sheet,
        encoding=used_encoding,
        max_rows=max_rows,
    )


def get_sheet_names(path: str) -> list[str]:
    """
    Retorna los nombres de todas las hojas de un archivo Excel o ODS.

    No aplica a CSV, TSV ni Parquet (estos formatos no tienen hojas).

    Args:
        path: Ruta al archivo Excel (.xlsx, .xls) u ODS (.ods).

    Returns:
        Lista de nombres de hojas en el orden en que aparecen en el archivo.

    Raises:
        UnsupportedFormatError: Si el formato no soporta hojas (ej: CSV).
        McpError: Si el archivo no existe o no puede ser leído.
    """
    logger.info("Obteniendo nombres de hojas", path=path)

    resolved = _resolve_path(path)
    fmt = _get_file_format(resolved)

    if fmt not in ("excel", "ods"):
        raise UnsupportedFormatError(
            format_name=resolved.suffix,
            supported_formats=[".xlsx", ".xls", ".ods"],
        )

    try:
        engine = (
            "odf"
            if fmt == "ods"
            else ("openpyxl" if resolved.suffix.lower() == ".xlsx" else "xlrd")
        )
        xl = pd.ExcelFile(resolved, engine=engine)
        sheet_names = xl.sheet_names
    except Exception as exc:
        raise FileReadError(file_path=str(resolved), reason=str(exc)) from exc

    logger.info("Hojas encontradas", path=str(resolved), count=len(sheet_names))
    return sheet_names


def get_file_summary(
    path: str,
    sheet: str | None = None,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """
    Retorna un resumen estadístico del archivo tabular.

    Incluye shape, tipos de datos, conteo de nulos, estadísticas descriptivas
    (mean, std, min, max, percentiles) para columnas numéricas.

    Args:
        path: Ruta al archivo tabular.
        sheet: Nombre de hoja para Excel/ODS (None = primera hoja).
        max_file_size_mb: Tamaño máximo de archivo en MB.

    Returns:
        Diccionario con:
          - path: Ruta del archivo.
          - format: Formato del archivo.
          - shape: [filas, columnas].
          - columns: Lista de nombres de columnas.
          - dtypes: Dict columna → dtype como string.
          - null_counts: Dict columna → cantidad de nulos.
          - null_percentages: Dict columna → porcentaje de nulos.
          - numeric_describe: Estadísticas descriptivas de columnas numéricas.
          - sheet_name: Nombre de hoja si aplica.
          - size_bytes: Tamaño del archivo en bytes.
          - size_mb: Tamaño del archivo en MB.

    Raises:
        McpError: Si el archivo no existe, formato no soportado, o error de parseo.
    """
    logger.info("Generando resumen de archivo", path=path, sheet=sheet)

    resolved = _resolve_path(path)
    _validate_file_size(resolved, max_bytes=max_file_size_mb * 1024 * 1024)

    df, _ = _read_dataframe(resolved, sheet=sheet)

    # Estadísticas descriptivas de columnas numéricas
    numeric_df = df.select_dtypes(include=["number"])
    numeric_describe: dict[str, Any] = {}
    if not numeric_df.empty:
        desc = numeric_df.describe().to_dict()
        # Convertir numpy types a Python natives
        for col, stats in desc.items():
            numeric_describe[str(col)] = {
                k: (v.item() if hasattr(v, "item") else v) for k, v in stats.items()
            }

    size_bytes = resolved.stat().st_size

    summary = {
        "path": str(resolved),
        "format": resolved.suffix.lstrip("."),
        "shape": list(df.shape),
        "columns": [str(c) for c in df.columns],
        "dtypes": {str(c): str(t) for c, t in df.dtypes.items()},
        "null_counts": {str(c): int(df[c].isna().sum()) for c in df.columns},
        "null_percentages": {
            str(c): round(float(df[c].isna().mean() * 100), 2) for c in df.columns
        },
        "numeric_describe": numeric_describe,
        "sheet_name": sheet,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 3),
    }

    logger.info(
        "Resumen generado",
        path=str(resolved),
        rows=df.shape[0],
        cols=df.shape[1],
    )

    return summary


def read_specific_sheet(path: str, sheet_name: str, max_file_size_mb: int = 100) -> dict[str, Any]:
    """
    Lee una hoja específica de un archivo Excel o ODS por nombre.

    Equivalente a read_tabular_file(path, sheet=sheet_name) pero con validación
    más explícita del nombre de hoja y mejor mensaje de error si no existe.

    Args:
        path: Ruta al archivo Excel (.xlsx, .xls) u ODS (.ods).
        sheet_name: Nombre exacto de la hoja a leer.
        max_file_size_mb: Tamaño máximo de archivo en MB.

    Returns:
        Respuesta estándar igual que read_tabular_file.

    Raises:
        ValidationError: Si sheet_name está vacío.
        ParseError: Si la hoja no existe en el archivo.
        McpError: Si el archivo no existe o formato no soportado.
    """
    if not sheet_name or not sheet_name.strip():
        raise ValidationError(
            field="sheet_name",
            message="El nombre de hoja no puede estar vacío.",
        )

    logger.info("Leyendo hoja específica", path=path, sheet_name=sheet_name)

    resolved = _resolve_path(path)
    _validate_file_size(resolved, max_bytes=max_file_size_mb * 1024 * 1024)

    fmt = _get_file_format(resolved)
    if fmt not in ("excel", "ods"):
        raise UnsupportedFormatError(
            format_name=resolved.suffix,
            supported_formats=[".xlsx", ".xls", ".ods"],
        )

    # Verificar que la hoja existe
    try:
        available_sheets = get_sheet_names(path)
    except Exception as exc:
        raise FileReadError(file_path=str(resolved), reason=str(exc)) from exc

    if sheet_name not in available_sheets:
        raise ParseError(
            source=str(resolved),
            reason=(
                f"La hoja '{sheet_name}' no existe. "
                f"Hojas disponibles: {', '.join(available_sheets)}"
            ),
        )

    df, used_encoding = _read_dataframe(resolved, sheet=sheet_name)

    return _build_standard_response(
        df=df,
        path=resolved,
        fmt=resolved.suffix.lstrip("."),
        sheet=sheet_name,
        encoding=used_encoding,
    )


def filter_rows(
    path: str,
    column: str,
    operator: str,
    value: str,
    sheet: str | None = None,
    max_rows: int = _MAX_ROWS_DEFAULT,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """
    Filtra filas de un archivo tabular según un criterio en una columna.

    Operadores soportados:
      - eq: Igual a (==)
      - ne: Diferente a (!=)
      - gt: Mayor que (>)
      - lt: Menor que (<)
      - gte: Mayor o igual que (>=)
      - lte: Menor o igual que (<=)
      - contains: Contiene el substring (case-insensitive, solo texto)
      - startswith: Empieza con el substring (case-insensitive, solo texto)

    Args:
        path: Ruta al archivo tabular.
        column: Nombre de la columna a filtrar.
        operator: Operador de comparación (ver lista de soportados).
        value: Valor a comparar (se intenta convertir al tipo de la columna).
        sheet: Nombre de hoja para Excel/ODS.
        max_rows: Máximo de filas en la respuesta.
        max_file_size_mb: Tamaño máximo de archivo en MB.

    Returns:
        Respuesta estándar con solo las filas que cumplen el criterio.

    Raises:
        ValidationError: Si el operador no está soportado o la columna no existe.
        McpError: Si el archivo no existe o no puede ser parseado.
    """
    valid_operators = {"eq", "ne", "gt", "lt", "gte", "lte", "contains", "startswith"}

    if operator not in valid_operators:
        raise InvalidValueError(
            field="operator",
            value=operator,
            reason=f"Operador no válido. Operadores soportados: {', '.join(sorted(valid_operators))}",
        )

    logger.info(
        "Filtrando filas",
        path=path,
        column=column,
        operator=operator,
        value=value,
    )

    resolved = _resolve_path(path)
    _validate_file_size(resolved, max_bytes=max_file_size_mb * 1024 * 1024)

    df, used_encoding = _read_dataframe(resolved, sheet=sheet)

    if column not in df.columns:
        raise ValidationError(
            field="column",
            message=(
                f"La columna '{column}' no existe en el archivo. "
                f"Columnas disponibles: {', '.join(str(c) for c in df.columns)}"
            ),
        )

    series = df[column]

    try:
        if operator in ("contains", "startswith"):
            # Operaciones de string — trabajar en modo texto
            str_series = series.astype(str).str.lower()
            str_value = str(value).lower()
            if operator == "contains":
                mask = str_series.str.contains(str_value, na=False, regex=False)
            else:  # startswith
                mask = str_series.str.startswith(str_value, na=False)
        else:
            # Operaciones numéricas/comparación — intentar convertir el valor
            col_dtype = series.dtype
            try:
                if pd.api.types.is_numeric_dtype(col_dtype):
                    typed_value: Any = float(value) if "." in str(value) else int(value)
                elif pd.api.types.is_datetime64_any_dtype(col_dtype):
                    typed_value = pd.Timestamp(value)
                else:
                    typed_value = str(value)
            except (ValueError, TypeError):
                typed_value = str(value)

            op_map = {
                "eq": series == typed_value,
                "ne": series != typed_value,
                "gt": series > typed_value,
                "lt": series < typed_value,
                "gte": series >= typed_value,
                "lte": series <= typed_value,
            }
            mask = op_map[operator]

        filtered_df = df[mask]

    except Exception as exc:
        raise ParseError(
            source=str(resolved),
            reason=f"Error al aplicar filtro '{operator}' en columna '{column}': {exc}",
        ) from exc

    logger.info(
        "Filtro aplicado",
        path=str(resolved),
        total_rows=len(df),
        filtered_rows=len(filtered_df),
        operator=operator,
        column=column,
    )

    return _build_standard_response(
        df=filtered_df,
        path=resolved,
        fmt=resolved.suffix.lstrip("."),
        sheet=sheet,
        encoding=used_encoding,
        max_rows=max_rows,
    )


def search_in_file(
    path: str,
    query: str,
    sheet: str | None = None,
    max_results: int = 100,
    max_file_size_mb: int = 100,
) -> list[dict[str, Any]]:
    """
    Busca el texto de la consulta en todas las columnas del archivo.

    Realiza una búsqueda case-insensitive en todas las celdas del archivo,
    convirtiendo los valores a texto para la comparación.

    Args:
        path: Ruta al archivo tabular.
        query: Texto a buscar (case-insensitive, búsqueda de substring).
        sheet: Nombre de hoja para Excel/ODS.
        max_results: Número máximo de resultados a retornar.
        max_file_size_mb: Tamaño máximo de archivo en MB.

    Returns:
        Lista de dicts, cada uno con:
          - row_index: Índice de la fila (0-based).
          - column: Nombre de la columna donde se encontró el match.
          - value: Valor de la celda (como string).
          - row: Toda la fila como dict.

    Raises:
        ValidationError: Si query está vacía.
        McpError: Si el archivo no existe o no puede ser parseado.
    """
    if not query or not query.strip():
        raise ValidationError(
            field="query",
            message="La consulta de búsqueda no puede estar vacía.",
        )

    logger.info("Buscando en archivo", path=path, query=query)

    resolved = _resolve_path(path)
    _validate_file_size(resolved, max_bytes=max_file_size_mb * 1024 * 1024)

    df, _ = _read_dataframe(resolved, sheet=sheet)

    query_lower = query.lower()
    matches: list[dict[str, Any]] = []

    for row_idx, (_, row) in enumerate(df.iterrows()):
        if len(matches) >= max_results:
            break
        for col in df.columns:
            cell_value = row[col]
            cell_str = "" if pd.isna(cell_value) else str(cell_value)
            if query_lower in cell_str.lower():
                # Convertir toda la fila a dict serializable
                row_dict: dict[str, Any] = {}
                for c, v in row.items():
                    if pd.isna(v) if not isinstance(v, (list, dict, str)) else False:
                        row_dict[str(c)] = None
                    elif isinstance(v, pd.Timestamp):
                        row_dict[str(c)] = v.isoformat()
                    elif hasattr(v, "item"):
                        row_dict[str(c)] = v.item()
                    else:
                        row_dict[str(c)] = v

                matches.append(
                    {
                        "row_index": row_idx,
                        "column": str(col),
                        "value": cell_str,
                        "row": row_dict,
                    }
                )
                if len(matches) >= max_results:
                    break

    logger.info(
        "Búsqueda completada",
        path=str(resolved),
        query=query,
        matches_found=len(matches),
    )

    return matches


def convert_to_csv(
    path: str,
    sheet: str | None = None,
    output_encoding: str = "utf-8",
    max_file_size_mb: int = 100,
) -> str:
    """
    Convierte un archivo tabular a texto CSV.

    Útil para exportar datos de Excel/ODS/Parquet a formato CSV estándar.

    Args:
        path: Ruta al archivo tabular a convertir.
        sheet: Nombre de hoja para Excel/ODS.
        output_encoding: Encoding del CSV de salida (por defecto utf-8).
        max_file_size_mb: Tamaño máximo de archivo en MB.

    Returns:
        String con el contenido CSV completo (incluyendo encabezados).

    Raises:
        McpError: Si el archivo no existe o no puede ser parseado.
    """
    logger.info("Convirtiendo archivo a CSV", path=path, sheet=sheet)

    resolved = _resolve_path(path)
    _validate_file_size(resolved, max_bytes=max_file_size_mb * 1024 * 1024)

    df, _ = _read_dataframe(resolved, sheet=sheet)

    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding=output_encoding)
    csv_content = buffer.getvalue()

    logger.info(
        "Conversión a CSV completada",
        path=str(resolved),
        rows=len(df),
        columns=len(df.columns),
        output_size_bytes=len(csv_content.encode(output_encoding)),
    )

    return csv_content


def get_column_stats(
    path: str,
    column: str,
    sheet: str | None = None,
    max_file_size_mb: int = 100,
) -> dict[str, Any]:
    """
    Retorna estadísticas detalladas de una columna específica.

    Para columnas numéricas: mean, std, min, max, percentiles, skewness, kurtosis.
    Para columnas de texto: value_counts, most_frequent, unique_count, avg_length.
    Para columnas de fecha: min_date, max_date, date_range_days.
    Para todas: null_count, null_percentage, total_count, dtype.

    Args:
        path: Ruta al archivo tabular.
        column: Nombre de la columna a analizar.
        sheet: Nombre de hoja para Excel/ODS.
        max_file_size_mb: Tamaño máximo de archivo en MB.

    Returns:
        Diccionario con estadísticas específicas según el tipo de la columna.

    Raises:
        ValidationError: Si la columna no existe.
        McpError: Si el archivo no existe o no puede ser parseado.
    """
    logger.info("Calculando estadísticas de columna", path=path, column=column)

    resolved = _resolve_path(path)
    _validate_file_size(resolved, max_bytes=max_file_size_mb * 1024 * 1024)

    df, _ = _read_dataframe(resolved, sheet=sheet)

    if column not in df.columns:
        raise ValidationError(
            field="column",
            message=(
                f"La columna '{column}' no existe en el archivo. "
                f"Columnas disponibles: {', '.join(str(c) for c in df.columns)}"
            ),
        )

    series = df[column]
    total_count = len(series)
    null_count = int(series.isna().sum())
    non_null_series = series.dropna()

    stats: dict[str, Any] = {
        "column": column,
        "dtype": str(series.dtype),
        "total_count": total_count,
        "null_count": null_count,
        "non_null_count": total_count - null_count,
        "null_percentage": round(float(null_count / total_count * 100), 2) if total_count else 0.0,
        "unique_count": int(non_null_series.nunique()),
    }

    if pd.api.types.is_numeric_dtype(series.dtype):
        # Estadísticas numéricas
        try:
            desc = non_null_series.describe()
            stats["numeric"] = {
                "mean": round(float(desc["mean"]), 6),
                "std": round(float(desc["std"]), 6) if not pd.isna(desc.get("std")) else None,
                "min": float(desc["min"]),
                "max": float(desc["max"]),
                "p25": float(desc["25%"]),
                "p50": float(desc["50%"]),
                "p75": float(desc["75%"]),
                "sum": float(non_null_series.sum()),
                "skewness": round(float(non_null_series.skew()), 6)
                if len(non_null_series) >= 3
                else None,
                "kurtosis": round(float(non_null_series.kurtosis()), 6)
                if len(non_null_series) >= 4
                else None,
            }
        except Exception as exc:
            logger.warning("No se pudieron calcular stats numéricas", column=column, error=str(exc))

    elif pd.api.types.is_datetime64_any_dtype(series.dtype):
        # Estadísticas de fecha
        if not non_null_series.empty:
            min_dt = non_null_series.min()
            max_dt = non_null_series.max()
            stats["datetime"] = {
                "min_date": min_dt.isoformat() if pd.notna(min_dt) else None,
                "max_date": max_dt.isoformat() if pd.notna(max_dt) else None,
                "date_range_days": int((max_dt - min_dt).days)
                if pd.notna(min_dt) and pd.notna(max_dt)
                else None,
            }
    else:
        # Estadísticas de texto / categórico
        str_series = non_null_series.astype(str)
        value_counts = str_series.value_counts().head(10)
        stats["text"] = {
            "most_frequent": value_counts.index[0] if not value_counts.empty else None,
            "most_frequent_count": int(value_counts.iloc[0]) if not value_counts.empty else 0,
            "top_10_values": {k: int(v) for k, v in value_counts.items()},
            "avg_length": round(float(str_series.str.len().mean()), 2)
            if not str_series.empty
            else 0.0,
            "min_length": int(str_series.str.len().min()) if not str_series.empty else 0,
            "max_length": int(str_series.str.len().max()) if not str_series.empty else 0,
        }

    logger.info(
        "Estadísticas calculadas",
        path=str(resolved),
        column=column,
        dtype=stats["dtype"],
    )

    return stats
