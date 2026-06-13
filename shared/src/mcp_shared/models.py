"""
Modelos Pydantic v2 compartidos por todos los servidores MCP del framework.

Incluye modelos para respuestas estándar, documentos, calendarios y divisas.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

_Date = date

# Variable de tipo genérica para StandardResponse
T = TypeVar("T")


# ---------------------------------------------------------------------------
# Respuestas estándar
# ---------------------------------------------------------------------------


class StandardResponse(BaseModel, Generic[T]):
    """
    Respuesta estándar genérica para todas las herramientas MCP.

    Encapsula el resultado de una operación con estado, datos, error y metadatos
    de manera uniforme, independientemente del tipo de dato retornado.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: Literal["success", "error"] = Field(
        ...,
        description="Estado de la operación: 'success' o 'error'.",
    )
    data: T | None = Field(
        default=None,
        description="Resultado de la operación cuando el estado es 'success'.",
    )
    error: str | None = Field(
        default=None,
        description="Mensaje descriptivo del error cuando el estado es 'error'.",
    )
    error_code: str | None = Field(
        default=None,
        description="Código de error estructurado para identificación programática.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadatos adicionales de la respuesta (duración, versión, etc.).",
    )

    @classmethod
    def success(cls, data: T, metadata: dict[str, Any] | None = None) -> StandardResponse[T]:
        """Crea una respuesta exitosa con los datos y metadatos opcionales."""
        return cls(status="success", data=data, metadata=metadata or {})

    @classmethod
    def failure(
        cls,
        error: str,
        error_code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StandardResponse[T]:
        """Crea una respuesta de error con el mensaje y código de error opcionales."""
        return cls(
            status="error",
            error=error,
            error_code=error_code,
            metadata=metadata or {},
        )

    @property
    def is_success(self) -> bool:
        """Retorna True si la operación fue exitosa."""
        return self.status == "success"

    @property
    def is_error(self) -> bool:
        """Retorna True si la operación terminó en error."""
        return self.status == "error"


class TableRecord(BaseModel):
    """
    Representa una fila de tabla como un diccionario de columnas a valores.

    Utilizado para retornar resultados tabulares de consultas o extracción de datos.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: dict[str, Any] = Field(
        ...,
        description="Mapa de nombre de columna a valor para esta fila.",
    )


class StandardTableResponse(BaseModel):
    """
    Respuesta estándar para datos tabulares.

    Contiene las columnas, registros, total de filas y metadatos de la tabla.
    """

    columns: list[str] = Field(
        default_factory=list,
        description="Lista ordenada de nombres de columnas de la tabla.",
    )
    records: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Lista de filas, cada una como un diccionario columna→valor.",
    )
    total_rows: int = Field(
        default=0,
        ge=0,
        description="Número total de filas en el resultado.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadatos adicionales (fuente, consulta, tiempo, etc.).",
    )

    @field_validator("total_rows", mode="before")
    @classmethod
    def infer_total_rows(cls, v: int, info: Any) -> int:
        """Infiere total_rows desde records si el valor es 0 y hay registros."""
        return v


# ---------------------------------------------------------------------------
# Modelos de documentos
# ---------------------------------------------------------------------------


class ImageData(BaseModel):
    """
    Datos de una imagen extraída de un documento.

    Contiene la ruta, descripción y texto OCR si está disponible.
    """

    path: str = Field(..., description="Ruta absoluta o relativa al archivo de imagen.")
    description: str | None = Field(
        default=None,
        description="Descripción generada o provista de la imagen.",
    )
    ocr_text: str | None = Field(
        default=None,
        description="Texto extraído por OCR de la imagen, si está disponible.",
    )
    page_number: int | None = Field(
        default=None,
        ge=1,
        description="Número de página del documento donde aparece la imagen.",
    )
    width: int | None = Field(default=None, ge=1, description="Ancho de la imagen en píxeles.")
    height: int | None = Field(default=None, ge=1, description="Alto de la imagen en píxeles.")


class TableData(BaseModel):
    """
    Tabla extraída de un documento.

    Preserva la estructura tabular con encabezados y filas de datos.
    """

    headers: list[str] = Field(
        default_factory=list,
        description="Nombres de las columnas de la tabla.",
    )
    rows: list[list[str]] = Field(
        default_factory=list,
        description="Filas de datos; cada fila es una lista de strings por columna.",
    )
    caption: str | None = Field(
        default=None,
        description="Título o descripción de la tabla si está disponible.",
    )
    page_number: int | None = Field(
        default=None,
        ge=1,
        description="Número de página del documento donde aparece la tabla.",
    )

    @property
    def row_count(self) -> int:
        """Retorna el número de filas de datos (sin contar encabezados)."""
        return len(self.rows)

    @property
    def column_count(self) -> int:
        """Retorna el número de columnas."""
        return len(self.headers)


class DocumentMetadata(BaseModel):
    """
    Metadatos de un documento procesado.

    Incluye información del archivo y datos extraídos durante el procesamiento.
    """

    file_path: str = Field(..., description="Ruta absoluta al archivo del documento.")
    file_name: str = Field(..., description="Nombre del archivo con extensión.")
    file_size_bytes: int | None = Field(
        default=None,
        ge=0,
        description="Tamaño del archivo en bytes.",
    )
    format: str = Field(
        ...,
        description="Formato del documento (pdf, docx, xlsx, txt, etc.).",
    )
    page_count: int | None = Field(
        default=None,
        ge=1,
        description="Número de páginas del documento, si aplica.",
    )
    author: str | None = Field(default=None, description="Autor del documento.")
    title: str | None = Field(default=None, description="Título del documento.")
    subject: str | None = Field(default=None, description="Asunto o tema del documento.")
    created_at: datetime | None = Field(
        default=None,
        description="Fecha y hora de creación del documento.",
    )
    modified_at: datetime | None = Field(
        default=None,
        description="Fecha y hora de última modificación del documento.",
    )
    language: str | None = Field(
        default=None,
        description="Idioma principal detectado o declarado (código ISO 639-1).",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadatos adicionales específicos del formato.",
    )


class DocumentContent(BaseModel):
    """
    Contenido completo extraído de un documento.

    Agrega texto, tablas, imágenes y metadatos en una estructura unificada.
    """

    text: str = Field(
        default="",
        description="Texto plano extraído del documento, preservando el orden de lectura.",
    )
    tables: list[TableData] = Field(
        default_factory=list,
        description="Tablas extraídas del documento en orden de aparición.",
    )
    images: list[ImageData] = Field(
        default_factory=list,
        description="Imágenes extraídas del documento en orden de aparición.",
    )
    metadata: DocumentMetadata | None = Field(
        default=None,
        description="Metadatos del documento.",
    )

    @property
    def has_tables(self) -> bool:
        """Retorna True si el documento contiene al menos una tabla."""
        return len(self.tables) > 0

    @property
    def has_images(self) -> bool:
        """Retorna True si el documento contiene al menos una imagen."""
        return len(self.images) > 0

    @property
    def word_count(self) -> int:
        """Retorna una estimación del número de palabras en el texto extraído."""
        return len(self.text.split()) if self.text else 0


# ---------------------------------------------------------------------------
# Modelos de calendario y días hábiles
# ---------------------------------------------------------------------------


class Holiday(BaseModel):
    """
    Feriado nacional o regional.

    Representa un día no laborable con su fecha, nombre y contexto geográfico.
    """

    date: _Date = Field(..., description="Fecha del feriado en formato ISO 8601.")
    name: str = Field(..., description="Nombre oficial del feriado.")
    country: str = Field(
        ...,
        description="Código de país ISO 3166-1 alpha-2 (ej: 'MX', 'US', 'CO').",
    )
    region: str | None = Field(
        default=None,
        description="Región, estado o provincia específica donde aplica el feriado.",
    )
    description: str | None = Field(
        default=None,
        description="Descripción o contexto histórico/cultural del feriado.",
    )
    is_fixed: bool = Field(
        default=True,
        description="True si el feriado cae siempre en la misma fecha; False si es móvil.",
    )

    @field_validator("country")
    @classmethod
    def country_uppercase(cls, v: str) -> str:
        """Normaliza el código de país a mayúsculas."""
        return v.upper()


class BusinessDaysResult(BaseModel):
    """
    Resultado de un cálculo de días hábiles entre dos fechas.

    Incluye el total de días hábiles, los feriados excluidos y las fechas procesadas.
    """

    start_date: date = Field(..., description="Fecha de inicio del período calculado.")
    end_date: date = Field(..., description="Fecha de fin del período calculado.")
    business_days: int = Field(
        ...,
        ge=0,
        description="Número total de días hábiles en el período (excluye feriados y fines de semana).",
    )
    total_days: int = Field(
        ...,
        ge=0,
        description="Número total de días del período (feriados, fines de semana y hábiles).",
    )
    holidays_excluded: list[Holiday] = Field(
        default_factory=list,
        description="Lista de feriados que cayeron dentro del período y fueron excluidos.",
    )
    country: str = Field(
        ...,
        description="Código de país ISO 3166-1 alpha-2 para el que se calcularon los días hábiles.",
    )
    weekend_days: int = Field(
        default=0,
        ge=0,
        description="Número de días de fin de semana excluidos del cálculo.",
    )


# ---------------------------------------------------------------------------
# Modelos de divisas y cambio
# ---------------------------------------------------------------------------


class ExchangeRate(BaseModel):
    """
    Tasa de cambio entre dos divisas en un momento específico.

    Almacena la relación de conversión y la fuente de la cotización.
    """

    base_currency: str = Field(
        ...,
        description="Código ISO 4217 de la divisa base (ej: 'USD', 'EUR', 'MXN').",
    )
    target_currency: str = Field(
        ...,
        description="Código ISO 4217 de la divisa destino.",
    )
    rate: float = Field(
        ...,
        gt=0,
        description="Unidades de la divisa destino por una unidad de la divisa base.",
    )
    timestamp: datetime = Field(
        ...,
        description="Fecha y hora de la cotización en UTC.",
    )
    source: str = Field(
        ...,
        description="Nombre o URL de la fuente de la cotización.",
    )
    bid: float | None = Field(
        default=None,
        gt=0,
        description="Precio de compra (bid) si está disponible.",
    )
    ask: float | None = Field(
        default=None,
        gt=0,
        description="Precio de venta (ask) si está disponible.",
    )

    @field_validator("base_currency", "target_currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        """Normaliza los códigos de divisa a mayúsculas."""
        return v.upper()


class ConversionResult(BaseModel):
    """
    Resultado de una conversión de divisas.

    Contiene el monto original, el monto convertido y la tasa utilizada.
    """

    original_amount: float = Field(
        ...,
        description="Monto original en la divisa de origen.",
    )
    converted_amount: float = Field(
        ...,
        description="Monto resultante en la divisa destino.",
    )
    rate: ExchangeRate = Field(
        ...,
        description="Tasa de cambio utilizada para la conversión.",
    )
    fee_amount: float = Field(
        default=0.0,
        ge=0,
        description="Comisión aplicada a la conversión, en la divisa origen.",
    )
    net_amount: float | None = Field(
        default=None,
        description="Monto neto convertido después de comisiones, en la divisa destino.",
    )


# ---------------------------------------------------------------------------
# Modelos de Markdown
# ---------------------------------------------------------------------------


class MarkdownHeading(BaseModel):
    """Encabezado de un documento Markdown con su nivel y texto."""

    level: int = Field(..., ge=1, le=6, description="Nivel del encabezado (1–6).")
    text: str = Field(..., description="Texto del encabezado sin los caracteres '#'.")
    anchor: str | None = Field(
        default=None,
        description="Ancla HTML generada para el encabezado (ej: 'my-heading').",
    )


class MarkdownLink(BaseModel):
    """Enlace encontrado en un documento Markdown."""

    text: str = Field(..., description="Texto visible del enlace.")
    url: str = Field(..., description="URL de destino del enlace.")
    title: str | None = Field(
        default=None,
        description="Título opcional del enlace (aparece como tooltip).",
    )
    is_image: bool = Field(
        default=False,
        description="True si el enlace es en realidad una imagen embebida.",
    )


class MarkdownCodeBlock(BaseModel):
    """Bloque de código en un documento Markdown."""

    language: str | None = Field(
        default=None,
        description="Lenguaje de programación declarado en la cerca de código.",
    )
    code: str = Field(..., description="Contenido del bloque de código.")
    line_start: int | None = Field(
        default=None,
        ge=1,
        description="Línea de inicio del bloque en el documento original.",
    )
    line_end: int | None = Field(
        default=None,
        ge=1,
        description="Línea de fin del bloque en el documento original.",
    )


class MarkdownDocument(BaseModel):
    """
    Documento Markdown completamente parseado.

    Contiene el texto crudo, frontmatter YAML, encabezados, enlaces y bloques de código.
    """

    raw: str = Field(..., description="Contenido crudo del documento Markdown.")
    frontmatter: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadatos YAML del frontmatter del documento.",
    )
    headings: list[MarkdownHeading] = Field(
        default_factory=list,
        description="Lista de encabezados del documento en orden de aparición.",
    )
    links: list[MarkdownLink] = Field(
        default_factory=list,
        description="Lista de enlaces encontrados en el documento.",
    )
    code_blocks: list[MarkdownCodeBlock] = Field(
        default_factory=list,
        description="Lista de bloques de código en el documento.",
    )
    word_count: int = Field(
        default=0,
        ge=0,
        description="Número estimado de palabras del cuerpo del documento.",
    )


# ---------------------------------------------------------------------------
# Modelos de análisis de texto y prompts
# ---------------------------------------------------------------------------


class TokenEstimate(BaseModel):
    """
    Estimado de tokens para un texto dado.

    Proporciona estimados usando distintas metodologías de tokenización.
    """

    text_length: int = Field(..., ge=0, description="Longitud del texto en caracteres.")
    word_count: int = Field(..., ge=0, description="Número de palabras en el texto.")
    estimated_tokens_gpt: int = Field(
        ...,
        ge=0,
        description="Tokens estimados según la metodología GPT (aprox. 4 chars/token).",
    )
    estimated_tokens_claude: int = Field(
        ...,
        ge=0,
        description="Tokens estimados según la metodología Claude (aprox. 3.5 chars/token).",
    )
    method: str = Field(
        default="heuristic",
        description="Método de estimación utilizado: 'heuristic', 'tiktoken', etc.",
    )


class TextStats(BaseModel):
    """
    Estadísticas detalladas de un texto.

    Útil para análisis de contenido y planificación de prompts.
    """

    character_count: int = Field(..., ge=0, description="Total de caracteres incluyendo espacios.")
    character_count_no_spaces: int = Field(
        ...,
        ge=0,
        description="Total de caracteres excluyendo espacios.",
    )
    word_count: int = Field(..., ge=0, description="Número de palabras.")
    sentence_count: int = Field(..., ge=0, description="Número de oraciones.")
    paragraph_count: int = Field(..., ge=0, description="Número de párrafos.")
    line_count: int = Field(..., ge=0, description="Número de líneas.")
    unique_word_count: int = Field(..., ge=0, description="Número de palabras únicas.")
    avg_word_length: float = Field(
        ...,
        ge=0,
        description="Longitud promedio de las palabras en caracteres.",
    )
    avg_sentence_length: float = Field(
        ...,
        ge=0,
        description="Longitud promedio de las oraciones en palabras.",
    )
    token_estimate: TokenEstimate | None = Field(
        default=None,
        description="Estimado de tokens para modelos de lenguaje.",
    )


class PromptAnalysis(BaseModel):
    """
    Análisis completo de un prompt de texto para modelos de lenguaje.

    Combina estadísticas, estimados de tokens y recomendaciones de uso.
    """

    prompt: str = Field(..., description="Texto original del prompt analizado.")
    stats: TextStats = Field(..., description="Estadísticas detalladas del texto.")
    token_estimate: TokenEstimate = Field(
        ...,
        description="Estimado de tokens del prompt.",
    )
    has_code: bool = Field(
        default=False,
        description="True si el prompt contiene bloques o fragmentos de código.",
    )
    has_markdown: bool = Field(
        default=False,
        description="True si el prompt contiene formato Markdown.",
    )
    detected_language: str | None = Field(
        default=None,
        description="Idioma principal detectado del prompt (código ISO 639-1).",
    )
    complexity_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Puntuación de complejidad del prompt entre 0.0 (simple) y 1.0 (complejo).",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Lista de recomendaciones para mejorar o usar el prompt.",
    )
