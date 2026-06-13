"""
Servidor FastMCP para mcp-calendar.

Expone 15 herramientas para cálculo de días hábiles (9 tools) y tasas de
cambio de divisas vía Frankfurter API (6 tools).

Transporte: configurable mediante MCP_TRANSPORT (stdio | streamable-http).
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

from mcp_calendar.config import CalendarSettings
from mcp_calendar.tools.business_days import (
    add_business_days,
    business_days_in_month,
    calculate_business_days,
    get_country_list,
    get_holidays,
    get_mexico_holidays,
    is_business_day,
    next_business_day,
    previous_business_day,
)
from mcp_calendar.tools.currency import (
    convert_currency,
    get_exchange_rate,
    get_historical_rate,
    get_mx_rates,
    get_rate_history,
    list_supported_currencies,
)

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

settings = CalendarSettings()

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-calendar",
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Context manager de ciclo de vida del servidor MCP."""
    structlog.contextvars.bind_contextvars(server_name="mcp-calendar")
    logger.info(
        "Servidor mcp-calendar iniciando",
        default_country=settings.default_country,
        exchange_rate_provider=settings.exchange_rate_provider,
        exchange_cache_ttl_seconds=settings.exchange_cache_ttl_seconds,
        log_level=settings.log_level,
        log_format=settings.log_format,
        transport=settings.mcp_transport,
    )
    yield
    logger.info("Servidor mcp-calendar detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-calendar",
    instructions=(
        "Servidor MCP especializado en calendario de días hábiles y tasas de cambio de divisas.\n\n"
        "## Días Hábiles\n"
        "- **get_holidays**: Lista feriados de un país y año (soporta +100 países).\n"
        "- **calculate_business_days**: Calcula días hábiles entre dos fechas.\n"
        "- **add_business_days**: Suma N días hábiles a una fecha.\n"
        "- **is_business_day**: Verifica si una fecha es día hábil.\n"
        "- **next_business_day**: Retorna el siguiente día hábil.\n"
        "- **previous_business_day**: Retorna el día hábil anterior.\n"
        "- **business_days_in_month**: Días hábiles de un mes completo.\n"
        "- **get_mexico_holidays**: Feriados mexicanos con descripciones en español.\n"
        "- **get_country_list**: Lista de países soportados con subdivisiones.\n\n"
        "## Divisas (Frankfurter API — gratuita, BCE)\n"
        "- **get_exchange_rate**: Tasa de cambio actual entre dos divisas.\n"
        "- **convert_currency**: Convierte un monto de divisa origen a destino.\n"
        "- **get_historical_rate**: Tasa de cambio histórica para una fecha.\n"
        "- **get_mx_rates**: Tasas MXN vs principales divisas del mundo.\n"
        "- **list_supported_currencies**: Lista de divisas disponibles (ISO 4217).\n"
        "- **get_rate_history**: Serie histórica de tasas entre dos fechas.\n\n"
        "Todas las fechas usan formato ISO 8601 (YYYY-MM-DD). "
        "Los códigos de país usan ISO 3166-1 alpha-2. "
        "Los códigos de divisa usan ISO 4217."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Helpers de manejo de errores
# ---------------------------------------------------------------------------


def _handle_mcp_error(tool_name: str, exc: McpError) -> None:
    """Registra un McpError y lo relanza como SdkMcpError."""
    logger.error(
        "Error en tool MCP",
        tool=tool_name,
        error_code=exc.error_code,
        message=exc.message,
        context=exc.context,
    )
    raise SdkMcpError(ErrorData(code=-32000, message=str(exc)))


def _handle_unexpected_error(tool_name: str, exc: Exception) -> None:
    """Registra un error inesperado y lo relanza como SdkMcpError."""
    logger.exception(
        "Error inesperado en tool MCP",
        tool=tool_name,
        error_type=type(exc).__name__,
        error=str(exc),
    )
    raise SdkMcpError(ErrorData(code=-32603, message=f"Error interno: {exc}"))


# ---------------------------------------------------------------------------
# Tools — Días Hábiles
# ---------------------------------------------------------------------------


@mcp.tool(
    name="get_holidays",
    description=(
        "Lista todos los feriados de un país para un año dado. "
        "Soporta más de 100 países usando ISO 3166-1 alpha-2 (ej: 'MX', 'US', 'DE'). "
        "Parámetros: country (código de país), year (año ej: 2025), "
        "state (subdivisión opcional ej: 'CDMX', 'CA'). "
        "Retorna: lista de feriados con fecha, nombre, país y región."
    ),
)
def tool_get_holidays(
    country: str,
    year: int,
    state: str | None = None,
) -> list[dict[str, Any]]:
    """Lista feriados de un país y año."""
    try:
        return get_holidays(country=country, year=year, state=state)
    except McpError as exc:
        _handle_mcp_error("get_holidays", exc)
    except Exception as exc:
        _handle_unexpected_error("get_holidays", exc)
    return []


@mcp.tool(
    name="calculate_business_days",
    description=(
        "Calcula los días hábiles entre dos fechas (ambas inclusive). "
        "Excluye fines de semana y feriados del país. "
        "Parámetros: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), "
        "country (ISO alpha-2, por defecto 'MX'). "
        "Retorna: business_days, total_days, weekend_days, holidays_excluded, country."
    ),
)
def tool_calculate_business_days(
    start_date: str,
    end_date: str,
    country: str = "MX",
) -> dict[str, Any]:
    """Calcula días hábiles entre dos fechas."""
    try:
        return calculate_business_days(
            start_date=start_date,
            end_date=end_date,
            country=country,
        )
    except McpError as exc:
        _handle_mcp_error("calculate_business_days", exc)
    except Exception as exc:
        _handle_unexpected_error("calculate_business_days", exc)
    return {}


@mcp.tool(
    name="add_business_days",
    description=(
        "Suma N días hábiles a una fecha de inicio. "
        "Si n_days es negativo, resta días hábiles hacia atrás. "
        "La fecha de inicio NO cuenta como día hábil a sumar. "
        "Parámetros: start_date (YYYY-MM-DD), n_days (entero, puede ser negativo), "
        "country (ISO alpha-2, por defecto 'MX'). "
        "Retorna: fecha resultante en formato ISO 8601 (YYYY-MM-DD)."
    ),
)
def tool_add_business_days(
    start_date: str,
    n_days: int,
    country: str = "MX",
) -> str:
    """Suma N días hábiles a una fecha."""
    try:
        return add_business_days(
            start_date=start_date,
            n_days=n_days,
            country=country,
        )
    except McpError as exc:
        _handle_mcp_error("add_business_days", exc)
    except Exception as exc:
        _handle_unexpected_error("add_business_days", exc)
    return ""


@mcp.tool(
    name="is_business_day",
    description=(
        "Verifica si una fecha específica es día hábil en el país dado. "
        "Parámetros: check_date (YYYY-MM-DD), country (ISO alpha-2, por defecto 'MX'). "
        "Retorna: is_business_day, is_weekend, is_holiday, holiday_name, "
        "holiday_description, day_of_week, country."
    ),
)
def tool_is_business_day(
    check_date: str,
    country: str = "MX",
) -> dict[str, Any]:
    """Verifica si una fecha es día hábil."""
    try:
        return is_business_day(check_date=check_date, country=country)
    except McpError as exc:
        _handle_mcp_error("is_business_day", exc)
    except Exception as exc:
        _handle_unexpected_error("is_business_day", exc)
    return {}


@mcp.tool(
    name="next_business_day",
    description=(
        "Retorna el siguiente día hábil después de la fecha dada. "
        "Si la fecha dada ya es hábil, retorna el SIGUIENTE (no el mismo día). "
        "Parámetros: check_date (YYYY-MM-DD), country (ISO alpha-2, por defecto 'MX'). "
        "Retorna: fecha del siguiente día hábil en formato ISO 8601."
    ),
)
def tool_next_business_day(
    check_date: str,
    country: str = "MX",
) -> str:
    """Retorna el siguiente día hábil."""
    try:
        return next_business_day(check_date=check_date, country=country)
    except McpError as exc:
        _handle_mcp_error("next_business_day", exc)
    except Exception as exc:
        _handle_unexpected_error("next_business_day", exc)
    return ""


@mcp.tool(
    name="previous_business_day",
    description=(
        "Retorna el día hábil anterior a la fecha dada. "
        "Si la fecha dada ya es hábil, retorna el ANTERIOR (no el mismo día). "
        "Parámetros: check_date (YYYY-MM-DD), country (ISO alpha-2, por defecto 'MX'). "
        "Retorna: fecha del día hábil anterior en formato ISO 8601."
    ),
)
def tool_previous_business_day(
    check_date: str,
    country: str = "MX",
) -> str:
    """Retorna el día hábil anterior."""
    try:
        return previous_business_day(check_date=check_date, country=country)
    except McpError as exc:
        _handle_mcp_error("previous_business_day", exc)
    except Exception as exc:
        _handle_unexpected_error("previous_business_day", exc)
    return ""


@mcp.tool(
    name="business_days_in_month",
    description=(
        "Calcula el total de días hábiles en un mes completo. "
        "Parámetros: year (ej: 2025), month (1–12), country (ISO alpha-2, por defecto 'MX'). "
        "Retorna: year, month, month_name, business_days, total_days, "
        "weekend_days, holiday_count, holidays, country."
    ),
)
def tool_business_days_in_month(
    year: int,
    month: int,
    country: str = "MX",
) -> dict[str, Any]:
    """Calcula días hábiles de un mes completo."""
    try:
        return business_days_in_month(year=year, month=month, country=country)
    except McpError as exc:
        _handle_mcp_error("business_days_in_month", exc)
    except Exception as exc:
        _handle_unexpected_error("business_days_in_month", exc)
    return {}


@mcp.tool(
    name="get_mexico_holidays",
    description=(
        "Retorna todos los feriados oficiales de México para el año dado, "
        "con descripciones en español de su contexto histórico y cultural. "
        "Incluye la base legal (Ley Federal del Trabajo, Art. 74). "
        "Parámetro: year (ej: 2025). "
        "Retorna: lista de feriados con date, name, description, is_fixed, "
        "day_of_week, legal_basis."
    ),
)
def tool_get_mexico_holidays(year: int) -> list[dict[str, Any]]:
    """Lista feriados de México con descripciones en español."""
    try:
        return get_mexico_holidays(year=year)
    except McpError as exc:
        _handle_mcp_error("get_mexico_holidays", exc)
    except Exception as exc:
        _handle_unexpected_error("get_mexico_holidays", exc)
    return []


@mcp.tool(
    name="get_country_list",
    description=(
        "Retorna la lista de todos los países soportados para cálculo de días hábiles. "
        "Incluye código ISO alpha-2, nombre del país y subdivisiones disponibles. "
        "Útil para validar códigos de país antes de llamar otras herramientas. "
        "No requiere parámetros. "
        "Retorna: lista con code, name, has_subdivisions, subdivisions."
    ),
)
def tool_get_country_list() -> list[dict[str, Any]]:
    """Lista países soportados con sus subdivisiones."""
    try:
        return get_country_list()
    except Exception as exc:
        _handle_unexpected_error("get_country_list", exc)
    return []


# ---------------------------------------------------------------------------
# Tools — Divisas
# ---------------------------------------------------------------------------


@mcp.tool(
    name="get_exchange_rate",
    description=(
        "Obtiene la tasa de cambio actual entre dos divisas vía Frankfurter API (BCE). "
        "Las tasas se actualizan diariamente y se cachean en memoria. "
        "Parámetros: from_currency (ISO 4217 ej: 'USD'), to_currency (ISO 4217 ej: 'MXN'), "
        "ttl_seconds (TTL del caché, por defecto 3600). "
        "Retorna: base_currency, target_currency, rate, timestamp, source."
    ),
)
async def tool_get_exchange_rate(
    from_currency: str,
    to_currency: str,
    ttl_seconds: int = 3600,
) -> dict[str, Any]:
    """Obtiene la tasa de cambio actual."""
    try:
        return await get_exchange_rate(
            from_currency=from_currency,
            to_currency=to_currency,
            ttl_seconds=ttl_seconds,
        )
    except McpError as exc:
        _handle_mcp_error("get_exchange_rate", exc)
    except Exception as exc:
        _handle_unexpected_error("get_exchange_rate", exc)
    return {}


@mcp.tool(
    name="convert_currency",
    description=(
        "Convierte un monto de una divisa a otra usando la tasa de cambio actual. "
        "Parámetros: amount (monto a convertir, >=0), from_currency (ISO 4217), "
        "to_currency (ISO 4217), ttl_seconds (TTL del caché, por defecto 3600). "
        "Retorna: original_amount, converted_amount, rate (tasa utilizada)."
    ),
)
async def tool_convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    ttl_seconds: int = 3600,
) -> dict[str, Any]:
    """Convierte un monto entre divisas."""
    try:
        return await convert_currency(
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
            ttl_seconds=ttl_seconds,
        )
    except McpError as exc:
        _handle_mcp_error("convert_currency", exc)
    except Exception as exc:
        _handle_unexpected_error("convert_currency", exc)
    return {}


@mcp.tool(
    name="get_historical_rate",
    description=(
        "Obtiene la tasa de cambio histórica entre dos divisas para una fecha específica. "
        "Datos disponibles desde 1999-01-04 (inicio del BCE). "
        "Parámetros: from_currency (ISO 4217), to_currency (ISO 4217), "
        "rate_date (YYYY-MM-DD, no puede ser fecha futura). "
        "Retorna: base_currency, target_currency, rate, timestamp, source."
    ),
)
async def tool_get_historical_rate(
    from_currency: str,
    to_currency: str,
    rate_date: str,
) -> dict[str, Any]:
    """Obtiene la tasa de cambio histórica para una fecha."""
    try:
        return await get_historical_rate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate_date=rate_date,
        )
    except McpError as exc:
        _handle_mcp_error("get_historical_rate", exc)
    except Exception as exc:
        _handle_unexpected_error("get_historical_rate", exc)
    return {}


@mcp.tool(
    name="get_mx_rates",
    description=(
        "Obtiene las tasas de cambio entre MXN y las principales monedas mundiales "
        "(USD, EUR, GBP, CAD, JPY, CHF, CNY). "
        "Parámetros: base (divisa base, por defecto 'MXN'), "
        "ttl_seconds (TTL del caché, por defecto 3600). "
        "Retorna: base, date, rates (mapa código→rate), source."
    ),
)
async def tool_get_mx_rates(
    base: str = "MXN",
    ttl_seconds: int = 3600,
) -> dict[str, Any]:
    """Obtiene tasas MXN vs principales divisas mundiales."""
    try:
        return await get_mx_rates(base=base, ttl_seconds=ttl_seconds)
    except McpError as exc:
        _handle_mcp_error("get_mx_rates", exc)
    except Exception as exc:
        _handle_unexpected_error("get_mx_rates", exc)
    return {}


@mcp.tool(
    name="list_supported_currencies",
    description=(
        "Lista todas las divisas soportadas por Frankfurter API (ISO 4217). "
        "Incluye el código y el nombre completo en inglés de cada divisa. "
        "No requiere parámetros. Los resultados se cachean 24 horas. "
        "Retorna: lista de dicts con 'code' y 'name', ordenados alfabéticamente."
    ),
)
async def tool_list_supported_currencies() -> list[dict[str, Any]]:
    """Lista todas las divisas disponibles en Frankfurter."""
    try:
        return await list_supported_currencies()
    except McpError as exc:
        _handle_mcp_error("list_supported_currencies", exc)
    except Exception as exc:
        _handle_unexpected_error("list_supported_currencies", exc)
    return []


@mcp.tool(
    name="get_rate_history",
    description=(
        "Obtiene el historial de tasas de cambio entre dos divisas para un rango de fechas. "
        "Solo incluye días hábiles del BCE (no fines de semana ni feriados europeos). "
        "Parámetros: from_currency (ISO 4217), to_currency (ISO 4217), "
        "start_date (YYYY-MM-DD), end_date (YYYY-MM-DD). "
        "Retorna: lista de tasas de cambio diarias ordenadas por fecha ascendente."
    ),
)
async def tool_get_rate_history(
    from_currency: str,
    to_currency: str,
    start_date: str,
    end_date: str,
) -> list[dict[str, Any]]:
    """Obtiene historial de tasas entre dos fechas."""
    try:
        return await get_rate_history(
            from_currency=from_currency,
            to_currency=to_currency,
            start_date=start_date,
            end_date=end_date,
        )
    except McpError as exc:
        _handle_mcp_error("get_rate_history", exc)
    except Exception as exc:
        _handle_unexpected_error("get_rate_history", exc)
    return []


# ---------------------------------------------------------------------------
# Factory + Entrypoint
# ---------------------------------------------------------------------------


def create_server() -> FastMCP:
    """Retorna la instancia del servidor MCP para uso externo."""
    return mcp


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
