"""
Herramientas de tasas de cambio de divisas para el servidor mcp-calendar.

Implementa consultas a la API de Frankfurter (frankfurter.app), que es gratuita
y no requiere clave de API. Incluye caché en memoria con TTL configurable.

Frankfurter API docs: https://frankfurter.app/docs
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, date, datetime
from typing import Any

import httpx
from mcp_shared.errors import ApiError, InvalidValueError, NetworkTimeoutError
from mcp_shared.models import ConversionResult, ExchangeRate

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

FRANKFURTER_BASE = "https://api.frankfurter.app"

# Monedas principales para las consultas de MXN
MX_MAJOR_CURRENCIES = ["USD", "EUR", "GBP", "CAD", "JPY", "CHF", "CNY"]

# Caché simple en memoria: {cache_key: (data, timestamp)}
_cache: dict[str, tuple[Any, float]] = {}
_cache_lock = asyncio.Lock()

# TTL por defecto (puede ser sobreescrito por configuración)
_DEFAULT_TTL_SECONDS = 3600


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _cache_key(*parts: str) -> str:
    """Genera una clave de caché a partir de las partes dadas."""
    return ":".join(parts).lower()


async def _get_cached(key: str, ttl: int = _DEFAULT_TTL_SECONDS) -> Any | None:
    """
    Retorna datos del caché si existen y no han expirado.

    Args:
        key: Clave de caché.
        ttl: Tiempo de vida en segundos.

    Returns:
        Datos cacheados o None si no existen / han expirado.
    """
    async with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        data, ts = entry
        if time.monotonic() - ts > ttl:
            del _cache[key]
            return None
        return data


async def _set_cached(key: str, data: Any) -> None:
    """Guarda datos en el caché con la marca de tiempo actual."""
    async with _cache_lock:
        _cache[key] = (data, time.monotonic())


def _parse_exchange_rate(
    data: dict[str, Any],
    from_currency: str,
    to_currency: str,
) -> ExchangeRate:
    """
    Parsea la respuesta de Frankfurter API a un modelo ExchangeRate.

    Args:
        data: Diccionario JSON de la respuesta de la API.
        from_currency: Código de la divisa base.
        to_currency: Código de la divisa destino.

    Returns:
        Modelo ExchangeRate con la tasa de cambio.

    Raises:
        ApiError: Si la respuesta no contiene la tasa esperada.
    """
    rates = data.get("rates", {})
    to_upper = to_currency.upper()

    if to_upper not in rates:
        raise ApiError(
            url=FRANKFURTER_BASE,
            status_code=200,
            response_body=(
                f"La divisa '{to_upper}' no está en la respuesta. "
                f"Tasas disponibles: {list(rates.keys())}"
            ),
        )

    # Parsear la fecha de la respuesta
    date_str = data.get("date", datetime.now(tz=UTC).date().isoformat())
    rate_date = date.fromisoformat(date_str)
    timestamp = datetime(
        rate_date.year,
        rate_date.month,
        rate_date.day,
        tzinfo=UTC,
    )

    return ExchangeRate(
        base_currency=from_currency.upper(),
        target_currency=to_upper,
        rate=float(rates[to_upper]),
        timestamp=timestamp,
        source="frankfurter.app",
    )


async def _frankfurter_get(
    path: str,
    params: dict[str, str] | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """
    Realiza una petición GET a la API de Frankfurter.

    Args:
        path: Ruta del endpoint (ej: '/latest', '/2025-01-01').
        params: Parámetros de query string opcionales.
        timeout: Timeout en segundos.

    Returns:
        Diccionario con la respuesta JSON de la API.

    Raises:
        NetworkTimeoutError: Si la petición supera el timeout.
        ApiError: Si la API retorna un código de error.
    """
    url = f"{FRANKFURTER_BASE}{path}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params or {})
            if response.status_code >= 400:
                raise ApiError(
                    url=url,
                    status_code=response.status_code,
                    response_body=response.text[:500],
                )
            return response.json()
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(url=url, timeout_seconds=timeout) from exc
    except httpx.RequestError as exc:
        from mcp_shared.errors import NetworkError

        raise NetworkError(url=url, reason=str(exc)) from exc


# ---------------------------------------------------------------------------
# Tools exportadas
# ---------------------------------------------------------------------------


async def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    ttl_seconds: int = _DEFAULT_TTL_SECONDS,
) -> dict:
    """
    Obtiene la tasa de cambio actual entre dos divisas vía Frankfurter API.

    Las tasas son actualizadas diariamente por el Banco Central Europeo.
    Los resultados se cachean en memoria según `ttl_seconds`.

    Args:
        from_currency: Código ISO 4217 de la divisa origen (ej: 'USD', 'MXN').
        to_currency: Código ISO 4217 de la divisa destino (ej: 'EUR', 'USD').
        ttl_seconds: TTL del caché en segundos. Por defecto 3600 (1 hora).

    Returns:
        Diccionario con `base_currency`, `target_currency`, `rate`,
        `timestamp` y `source`.

    Raises:
        ApiError: Si la API retorna error.
        InvalidValueError: Si los códigos de divisa son inválidos.

    Example:
        >>> await get_exchange_rate("USD", "MXN")
        {"base_currency": "USD", "target_currency": "MXN", "rate": 17.25, ...}
    """
    from_upper = from_currency.upper().strip()
    to_upper = to_currency.upper().strip()

    if len(from_upper) != 3:
        raise InvalidValueError(
            field="from_currency",
            value=from_currency,
            reason="El código de divisa debe tener exactamente 3 caracteres (ISO 4217).",
        )
    if len(to_upper) != 3:
        raise InvalidValueError(
            field="to_currency",
            value=to_currency,
            reason="El código de divisa debe tener exactamente 3 caracteres (ISO 4217).",
        )

    cache_key = _cache_key("rate", from_upper, to_upper)
    cached = await _get_cached(cache_key, ttl_seconds)
    if cached is not None:
        return cached

    data = await _frankfurter_get(
        "/latest",
        params={"from": from_upper, "to": to_upper},
    )
    exchange_rate = _parse_exchange_rate(data, from_upper, to_upper)
    result = exchange_rate.model_dump(mode="json")
    await _set_cached(cache_key, result)
    return result


async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    ttl_seconds: int = _DEFAULT_TTL_SECONDS,
) -> dict:
    """
    Convierte un monto de una divisa a otra usando la tasa de cambio actual.

    Args:
        amount: Monto a convertir (debe ser mayor a 0).
        from_currency: Código ISO 4217 de la divisa origen.
        to_currency: Código ISO 4217 de la divisa destino.
        ttl_seconds: TTL del caché de tasas en segundos. Por defecto 3600.

    Returns:
        Diccionario con `original_amount`, `converted_amount` y la tasa utilizada.

    Raises:
        InvalidValueError: Si el monto es negativo o las divisas son inválidas.
        ApiError: Si la API retorna error.

    Example:
        >>> await convert_currency(1000.0, "MXN", "USD")
        {"original_amount": 1000.0, "converted_amount": 57.97, "rate": {...}}
    """
    if amount < 0:
        raise InvalidValueError(
            field="amount",
            value=amount,
            reason="El monto a convertir no puede ser negativo.",
        )

    rate_dict = await get_exchange_rate(from_currency, to_currency, ttl_seconds)

    # Reconstruir el modelo ExchangeRate desde el dict para usar los validadores
    rate_obj = ExchangeRate(**rate_dict)

    converted = round(amount * rate_obj.rate, 6)

    result = ConversionResult(
        original_amount=amount,
        converted_amount=converted,
        rate=rate_obj,
    )
    return result.model_dump(mode="json")


async def get_historical_rate(
    from_currency: str,
    to_currency: str,
    rate_date: str,
) -> dict:
    """
    Obtiene la tasa de cambio histórica entre dos divisas para una fecha específica.

    Los datos históricos están disponibles desde 1999-01-04 (inicio del BCE).

    Args:
        from_currency: Código ISO 4217 de la divisa origen.
        to_currency: Código ISO 4217 de la divisa destino.
        rate_date: Fecha en formato ISO 8601 (YYYY-MM-DD).

    Returns:
        Diccionario con la tasa de cambio para la fecha dada.

    Raises:
        InvalidValueError: Si la fecha o divisas son inválidas.
        ApiError: Si no hay datos disponibles para esa fecha.

    Example:
        >>> await get_historical_rate("USD", "MXN", "2020-01-15")
        {"base_currency": "USD", "target_currency": "MXN", "rate": 18.95, ...}
    """
    from_upper = from_currency.upper().strip()
    to_upper = to_currency.upper().strip()

    # Validar fecha
    try:
        parsed_date = date.fromisoformat(rate_date)
    except ValueError as exc:
        raise InvalidValueError(
            field="rate_date",
            value=rate_date,
            reason=f"Formato de fecha inválido '{rate_date}'. Use YYYY-MM-DD.",
        ) from exc

    if parsed_date > date.today():
        raise InvalidValueError(
            field="rate_date",
            value=rate_date,
            reason="No se pueden consultar tasas históricas para fechas futuras.",
        )

    cache_key = _cache_key("hist", from_upper, to_upper, rate_date)
    cached = await _get_cached(cache_key, ttl=86400)  # Hist = 24h cache
    if cached is not None:
        return cached

    data = await _frankfurter_get(
        f"/{rate_date}",
        params={"from": from_upper, "to": to_upper},
    )
    exchange_rate = _parse_exchange_rate(data, from_upper, to_upper)
    result = exchange_rate.model_dump(mode="json")
    await _set_cached(cache_key, result)
    return result


async def get_mx_rates(
    base: str = "MXN",
    ttl_seconds: int = _DEFAULT_TTL_SECONDS,
) -> dict:
    """
    Obtiene las tasas de cambio entre MXN y las principales monedas del mundo.

    Por defecto retorna cuántos pesos mexicanos equivalen a 1 unidad de cada
    moneda principal (base=MXN muestra el valor del peso).

    Args:
        base: Divisa base de referencia. Por defecto 'MXN'.
              Si base='USD', muestra cuántos USD vale cada moneda.
        ttl_seconds: TTL del caché en segundos. Por defecto 3600.

    Returns:
        Diccionario con `base`, `date`, `rates` (mapa código→tasa) y `source`.

    Example:
        >>> await get_mx_rates()
        {"base": "MXN", "date": "2025-06-08", "rates": {"USD": 0.058, "EUR": 0.053, ...}}
    """
    base_upper = base.upper().strip()

    cache_key = _cache_key("mx_rates", base_upper)
    cached = await _get_cached(cache_key, ttl_seconds)
    if cached is not None:
        return cached

    # Obtener todas las tasas en un solo request
    currencies_str = ",".join(MX_MAJOR_CURRENCIES + ([] if base_upper == "MXN" else ["MXN"]))

    data = await _frankfurter_get(
        "/latest",
        params={"from": base_upper, "to": currencies_str},
    )

    rates = data.get("rates", {})
    date_str = data.get("date", date.today().isoformat())

    # Construir respuesta enriquecida
    enriched_rates: dict[str, dict] = {}
    for currency_code, rate_value in rates.items():
        enriched_rates[currency_code] = {
            "rate": float(rate_value),
            "currency": currency_code,
        }

    result = {
        "base": base_upper,
        "date": date_str,
        "rates": enriched_rates,
        "source": "frankfurter.app",
        "note": (
            f"1 {base_upper} = X [divisa_destino]. "
            "Tasas del Banco Central Europeo, actualizadas diariamente."
        ),
    }
    await _set_cached(cache_key, result)
    return result


async def list_supported_currencies() -> list[dict]:
    """
    Retorna la lista de todas las divisas soportadas por Frankfurter API.

    Incluye el código ISO 4217 y el nombre completo de la divisa en inglés.
    Los resultados se cachean durante 24 horas (la lista raramente cambia).

    Returns:
        Lista de diccionarios con `code` y `name` de cada divisa,
        ordenados por código alfabéticamente.

    Example:
        >>> await list_supported_currencies()
        [{"code": "AUD", "name": "Australian Dollar"}, {"code": "EUR", "name": "Euro"}, ...]
    """
    cache_key = _cache_key("currencies")
    cached = await _get_cached(cache_key, ttl=86400)
    if cached is not None:
        return cached

    data = await _frankfurter_get("/currencies")

    result: list[dict] = [{"code": code, "name": name} for code, name in sorted(data.items())]
    await _set_cached(cache_key, result)
    return result


async def get_rate_history(
    from_currency: str,
    to_currency: str,
    start_date: str,
    end_date: str,
) -> list[dict]:
    """
    Obtiene el historial de tasas de cambio entre dos fechas (inclusive).

    Los datos históricos de Frankfurter cubren desde 1999-01-04.
    Solo se incluyen días hábiles europeos (no se incluyen fines de semana
    ni feriados del BCE).

    Args:
        from_currency: Código ISO 4217 de la divisa origen.
        to_currency: Código ISO 4217 de la divisa destino.
        start_date: Fecha de inicio en formato ISO 8601 (YYYY-MM-DD).
        end_date: Fecha de fin en formato ISO 8601 (YYYY-MM-DD).

    Returns:
        Lista de diccionarios ExchangeRate ordenados por fecha ascendente.
        Cada elemento representa una tasa de cambio en un día específico.

    Raises:
        InvalidValueError: Si las fechas tienen formato inválido o el rango es inválido.
        ApiError: Si la API retorna error.

    Example:
        >>> await get_rate_history("USD", "MXN", "2025-01-01", "2025-01-15")
        [
            {"base_currency": "USD", "target_currency": "MXN", "rate": 20.48,
             "timestamp": "2025-01-02T00:00:00Z", ...},
            ...
        ]
    """
    from_upper = from_currency.upper().strip()
    to_upper = to_currency.upper().strip()

    # Validar fechas
    try:
        start = date.fromisoformat(start_date)
    except ValueError as exc:
        raise InvalidValueError(
            field="start_date",
            value=start_date,
            reason=f"Formato de fecha inválido '{start_date}'. Use YYYY-MM-DD.",
        ) from exc

    try:
        end = date.fromisoformat(end_date)
    except ValueError as exc:
        raise InvalidValueError(
            field="end_date",
            value=end_date,
            reason=f"Formato de fecha inválido '{end_date}'. Use YYYY-MM-DD.",
        ) from exc

    if start > end:
        raise InvalidValueError(
            field="start_date",
            value=start_date,
            reason=f"'start_date' ({start_date}) debe ser anterior o igual a 'end_date' ({end_date}).",
        )

    cache_key = _cache_key("history", from_upper, to_upper, start_date, end_date)
    cached = await _get_cached(cache_key, ttl=86400)
    if cached is not None:
        return cached

    data = await _frankfurter_get(
        f"/{start_date}..{end_date}",
        params={"from": from_upper, "to": to_upper},
    )

    rates_by_date = data.get("rates", {})
    result: list[dict] = []

    for date_str, rates in sorted(rates_by_date.items()):
        if to_upper not in rates:
            continue
        rate_date = date.fromisoformat(date_str)
        timestamp = datetime(
            rate_date.year,
            rate_date.month,
            rate_date.day,
            tzinfo=UTC,
        )
        exchange_rate = ExchangeRate(
            base_currency=from_upper,
            target_currency=to_upper,
            rate=float(rates[to_upper]),
            timestamp=timestamp,
            source="frankfurter.app",
        )
        result.append(exchange_rate.model_dump(mode="json"))

    await _set_cached(cache_key, result)
    return result
