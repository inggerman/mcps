"""
Herramientas de cálculo de días hábiles para el servidor mcp-calendar.

Implementa todas las operaciones de calendario utilizando la librería `holidays`
con soporte para múltiples países y un foco especial en México (MX).
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta

import holidays

from mcp_shared.errors import InvalidValueError, ValidationError
from mcp_shared.models import BusinessDaysResult, Holiday


# ---------------------------------------------------------------------------
# Descripciones en español de feriados mexicanos
# ---------------------------------------------------------------------------

_MX_HOLIDAY_DESCRIPTIONS: dict[str, str] = {
    "New Year's Day": "Año Nuevo — Primer día del año calendario.",
    "Constitution Day": (
        "Día de la Constitución — Conmemoración de la promulgación de la "
        "Constitución Política de los Estados Unidos Mexicanos de 1917."
    ),
    "Benito Juárez's birthday": (
        "Natalicio de Benito Juárez — Homenaje al presidente Benito Juárez García, "
        "símbolo de la Reforma y la defensa de la soberanía nacional."
    ),
    "Labor Day": (
        "Día del Trabajo — Reconocimiento a los derechos de los trabajadores, "
        "celebrado internacionalmente el 1° de mayo."
    ),
    "Independence Day": (
        "Día de la Independencia — Conmemoración del inicio de la guerra de "
        "Independencia de México, proclamada en el Grito de Dolores en 1810."
    ),
    "Revolution Day": (
        "Día de la Revolución — Aniversario del inicio de la Revolución Mexicana "
        "de 1910, encabezada por Francisco I. Madero."
    ),
    "Change of Federal Government": (
        "Transmisión del Poder Ejecutivo Federal — Jornada en que toma posesión "
        "el Presidente de la República (cada 6 años, el 1° de octubre)."
    ),
    "Christmas Day": (
        "Navidad — Festividad religiosa y cultural que celebra el nacimiento "
        "de Jesucristo, reconocida como día de descanso obligatorio."
    ),
}

# Días feriados adicionales de México con descripciones personalizadas
_MX_EXTRA_DESCRIPTIONS: dict[str, str] = {
    "Día de Muertos": (
        "Día de Muertos — Festividad de origen prehispánico en la que se honra "
        "a los difuntos; es Patrimonio Cultural Inmaterial de la Humanidad (UNESCO)."
    ),
    "Día de la Virgen de Guadalupe": (
        "Día de la Virgen de Guadalupe — Celebración religiosa en honor a la "
        "advocación mariana patrona de México y de toda América Latina."
    ),
}


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _get_holidays(
    country: str,
    year: int,
    state: str | None = None,
) -> holidays.HolidayBase:
    """
    Retorna el objeto `holidays.HolidayBase` para el país y año dados.

    Args:
        country: Código ISO 3166-1 alpha-2 del país (ej: 'MX', 'US', 'CO').
        year: Año para el que se cargan los feriados.
        state: Subdivisión (estado o provincia) opcional.

    Returns:
        Objeto HolidayBase con todos los feriados del país/año.

    Raises:
        InvalidValueError: Si el código de país no está soportado.
    """
    try:
        kwargs: dict = {"years": year}
        if state:
            kwargs["subdiv"] = state
        return holidays.country_holidays(country.upper(), **kwargs)
    except (NotImplementedError, KeyError) as exc:
        raise InvalidValueError(
            field="country",
            value=country,
            reason=(
                f"El código de país '{country}' no está soportado por la librería holidays. "
                "Use get_country_list() para ver los países disponibles."
            ),
        ) from exc


def _date_from_str(value: str, field_name: str = "date") -> date:
    """
    Parsea una cadena ISO 8601 a `datetime.date`.

    Args:
        value: Cadena de fecha en formato 'YYYY-MM-DD'.
        field_name: Nombre del campo para mensajes de error.

    Returns:
        Objeto `datetime.date`.

    Raises:
        ValidationError: Si el formato de la fecha es inválido.
    """
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(
            field=field_name,
            message=f"Formato de fecha inválido '{value}'. Use el formato ISO 8601: YYYY-MM-DD.",
        ) from exc


def _holiday_to_model(
    holiday_date: date,
    name: str,
    country: str,
    state: str | None = None,
) -> Holiday:
    """Convierte una tupla (date, name) del objeto holidays a un modelo Holiday."""
    description = _MX_HOLIDAY_DESCRIPTIONS.get(name) if country.upper() == "MX" else None
    return Holiday(
        date=holiday_date,
        name=name,
        country=country.upper(),
        region=state,
        description=description,
        is_fixed=holiday_date.month != 0,  # Los feriados de holidays siempre tienen mes
    )


# ---------------------------------------------------------------------------
# Tools exportadas
# ---------------------------------------------------------------------------


def get_holidays(
    country: str,
    year: int,
    state: str | None = None,
) -> list[dict]:
    """
    Retorna todos los feriados del año para el país y estado opcionales.

    Args:
        country: Código ISO 3166-1 alpha-2 (ej: 'MX', 'US', 'DE').
        year: Año a consultar (ej: 2025).
        state: Subdivisión opcional (ej: 'CDMX', 'CA', 'BY').

    Returns:
        Lista de diccionarios con fecha, nombre, país y región de cada feriado,
        ordenados por fecha ascendente.

    Example:
        >>> get_holidays("MX", 2025)
        [{"date": "2025-01-01", "name": "New Year's Day", "country": "MX", ...}, ...]
    """
    country_holidays = _get_holidays(country, year, state)
    result: list[Holiday] = []
    for h_date, h_name in sorted(country_holidays.items()):
        result.append(_holiday_to_model(h_date, h_name, country, state))
    return [h.model_dump(mode="json") for h in result]


def calculate_business_days(
    start_date: str,
    end_date: str,
    country: str = "MX",
) -> dict:
    """
    Calcula los días hábiles entre dos fechas (inclusive en ambos extremos).

    Un día hábil es aquel que no es sábado, domingo ni feriado en el país dado.

    Args:
        start_date: Fecha de inicio en formato ISO 8601 (YYYY-MM-DD).
        end_date: Fecha de fin en formato ISO 8601 (YYYY-MM-DD).
        country: Código ISO 3166-1 alpha-2 del país. Por defecto 'MX'.

    Returns:
        Diccionario con `start_date`, `end_date`, `business_days`, `total_days`,
        `weekend_days`, `holidays_excluded` y `country`.

    Raises:
        ValidationError: Si las fechas tienen formato inválido.
        InvalidValueError: Si `start_date` es posterior a `end_date`.

    Example:
        >>> calculate_business_days("2025-01-01", "2025-01-31", "MX")
        {"business_days": 22, "total_days": 31, "weekend_days": 8, ...}
    """
    start = _date_from_str(start_date, "start_date")
    end = _date_from_str(end_date, "end_date")

    if start > end:
        raise InvalidValueError(
            field="start_date",
            value=start_date,
            reason=f"'start_date' ({start_date}) debe ser anterior o igual a 'end_date' ({end_date}).",
        )

    # Cargar feriados para todos los años involucrados
    all_holidays: dict[date, str] = {}
    for year in range(start.year, end.year + 1):
        all_holidays.update(_get_holidays(country, year))

    total_days = (end - start).days + 1
    business_days_count = 0
    weekend_days_count = 0
    holidays_excluded: list[Holiday] = []

    current = start
    while current <= end:
        is_weekend = current.weekday() >= 5  # 5=sábado, 6=domingo
        is_holiday = current in all_holidays

        if is_weekend:
            weekend_days_count += 1
        elif is_holiday:
            holidays_excluded.append(
                _holiday_to_model(current, all_holidays[current], country)
            )
        else:
            business_days_count += 1

        current += timedelta(days=1)

    result = BusinessDaysResult(
        start_date=start,
        end_date=end,
        business_days=business_days_count,
        total_days=total_days,
        holidays_excluded=holidays_excluded,
        country=country.upper(),
        weekend_days=weekend_days_count,
    )
    return result.model_dump(mode="json")


def add_business_days(
    start_date: str,
    n_days: int,
    country: str = "MX",
) -> str:
    """
    Suma `n_days` días hábiles a `start_date` y retorna la fecha resultante.

    Si `n_days` es negativo, resta días hábiles hacia atrás.
    El `start_date` en sí mismo NO cuenta como un día hábil a sumar.

    Args:
        start_date: Fecha de inicio en formato ISO 8601 (YYYY-MM-DD).
        n_days: Número de días hábiles a sumar (puede ser negativo).
        country: Código ISO 3166-1 alpha-2 del país. Por defecto 'MX'.

    Returns:
        Fecha resultante en formato ISO 8601 (YYYY-MM-DD).

    Raises:
        ValidationError: Si el formato de fecha es inválido.
        InvalidValueError: Si el código de país no está soportado.

    Example:
        >>> add_business_days("2025-01-01", 5, "MX")
        "2025-01-08"  # 1-ene es feriado, suma 5 días hábiles
    """
    current = _date_from_str(start_date, "start_date")
    direction = 1 if n_days >= 0 else -1
    remaining = abs(n_days)

    # Pre-cargar feriados de los años que podrían estar involucrados
    # (estimamos ~260 días hábiles por año)
    years_needed = max(1, (remaining // 200) + 2)
    all_holidays: dict[date, str] = {}
    start_year = current.year
    for offset in range(-1, years_needed + 1):
        all_holidays.update(_get_holidays(country, start_year + offset * direction))

    while remaining > 0:
        current += timedelta(days=direction)
        # Recargar feriados si cambiamos de año
        if current.year not in {d.year for d in all_holidays}:
            all_holidays.update(_get_holidays(country, current.year))

        if current.weekday() < 5 and current not in all_holidays:
            remaining -= 1

    return current.isoformat()


def is_business_day(
    check_date: str,
    country: str = "MX",
) -> dict:
    """
    Verifica si una fecha específica es día hábil en el país dado.

    Args:
        check_date: Fecha a verificar en formato ISO 8601 (YYYY-MM-DD).
        country: Código ISO 3166-1 alpha-2 del país. Por defecto 'MX'.

    Returns:
        Diccionario con:
            - `date`: La fecha consultada.
            - `is_business_day`: True si es día hábil.
            - `is_weekend`: True si es sábado o domingo.
            - `is_holiday`: True si es feriado oficial.
            - `holiday_name`: Nombre del feriado si aplica, None en caso contrario.
            - `day_of_week`: Nombre del día de la semana en inglés.
            - `country`: Código de país usado.

    Example:
        >>> is_business_day("2025-09-16", "MX")
        {"date": "2025-09-16", "is_business_day": false, "is_holiday": true,
         "holiday_name": "Independence Day", ...}
    """
    d = _date_from_str(check_date, "date")
    country_holidays = _get_holidays(country, d.year)
    is_weekend = d.weekday() >= 5
    is_holiday = d in country_holidays
    holiday_name = country_holidays.get(d)

    return {
        "date": check_date,
        "is_business_day": not is_weekend and not is_holiday,
        "is_weekend": is_weekend,
        "is_holiday": is_holiday,
        "holiday_name": holiday_name,
        "holiday_description": _MX_HOLIDAY_DESCRIPTIONS.get(holiday_name, None) if holiday_name and country.upper() == "MX" else None,
        "day_of_week": d.strftime("%A"),
        "day_of_week_number": d.weekday(),  # 0=lunes, 6=domingo
        "country": country.upper(),
    }


def next_business_day(
    check_date: str,
    country: str = "MX",
) -> str:
    """
    Retorna el siguiente día hábil después de `check_date`.

    Si `check_date` ya es día hábil, retorna el siguiente (no el mismo día).

    Args:
        check_date: Fecha de referencia en formato ISO 8601 (YYYY-MM-DD).
        country: Código ISO 3166-1 alpha-2 del país. Por defecto 'MX'.

    Returns:
        Fecha del siguiente día hábil en formato ISO 8601 (YYYY-MM-DD).

    Example:
        >>> next_business_day("2025-09-15", "MX")  # Lunes antes del 16-sep (feriado)
        "2025-09-17"
    """
    d = _date_from_str(check_date, "date")
    all_holidays: dict[date, str] = _get_holidays(country, d.year)  # type: ignore[assignment]

    candidate = d + timedelta(days=1)
    while True:
        if candidate.year not in {h.year for h in all_holidays}:
            all_holidays.update(_get_holidays(country, candidate.year))
        if candidate.weekday() < 5 and candidate not in all_holidays:
            return candidate.isoformat()
        candidate += timedelta(days=1)


def previous_business_day(
    check_date: str,
    country: str = "MX",
) -> str:
    """
    Retorna el día hábil anterior a `check_date`.

    Si `check_date` ya es día hábil, retorna el anterior (no el mismo día).

    Args:
        check_date: Fecha de referencia en formato ISO 8601 (YYYY-MM-DD).
        country: Código ISO 3166-1 alpha-2 del país. Por defecto 'MX'.

    Returns:
        Fecha del día hábil anterior en formato ISO 8601 (YYYY-MM-DD).

    Example:
        >>> previous_business_day("2025-09-16", "MX")  # Día de Independencia
        "2025-09-15"
    """
    d = _date_from_str(check_date, "date")
    all_holidays: dict[date, str] = _get_holidays(country, d.year)  # type: ignore[assignment]

    candidate = d - timedelta(days=1)
    while True:
        if candidate.year not in {h.year for h in all_holidays}:
            all_holidays.update(_get_holidays(country, candidate.year))
        if candidate.weekday() < 5 and candidate not in all_holidays:
            return candidate.isoformat()
        candidate -= timedelta(days=1)


def business_days_in_month(
    year: int,
    month: int,
    country: str = "MX",
) -> dict:
    """
    Calcula la cantidad de días hábiles en un mes completo.

    Args:
        year: Año a calcular (ej: 2025).
        month: Mes a calcular (1–12).
        country: Código ISO 3166-1 alpha-2 del país. Por defecto 'MX'.

    Returns:
        Diccionario con:
            - `year`, `month`, `month_name`: Identificadores del mes.
            - `business_days`: Total de días hábiles.
            - `total_days`: Total de días del mes.
            - `weekend_days`: Días de fin de semana.
            - `holiday_count`: Número de feriados en días de semana.
            - `holidays`: Lista de feriados del mes.
            - `country`: Código de país.

    Raises:
        InvalidValueError: Si el mes está fuera del rango 1–12.

    Example:
        >>> business_days_in_month(2025, 9, "MX")
        {"year": 2025, "month": 9, "business_days": 20, "total_days": 30, ...}
    """
    if not 1 <= month <= 12:
        raise InvalidValueError(
            field="month",
            value=month,
            reason="El mes debe ser un número entre 1 y 12.",
        )

    _, total_days = calendar.monthrange(year, month)
    start = date(year, month, 1)
    end = date(year, month, total_days)

    result_dict = calculate_business_days(start.isoformat(), end.isoformat(), country)

    return {
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "business_days": result_dict["business_days"],
        "total_days": total_days,
        "weekend_days": result_dict["weekend_days"],
        "holiday_count": len(result_dict["holidays_excluded"]),
        "holidays": result_dict["holidays_excluded"],
        "country": country.upper(),
    }


def get_mexico_holidays(year: int) -> list[dict]:
    """
    Retorna la lista completa de feriados oficiales de México para el año dado.

    Incluye descripciones en español de cada feriado con su contexto histórico
    y cultural. Los feriados siguen la Ley Federal del Trabajo (Art. 74).

    Args:
        year: Año a consultar (ej: 2025).

    Returns:
        Lista de diccionarios con fecha, nombre oficial, descripción en español
        e indicador de si el feriado es de fecha fija o móvil (lunes próximo).
        Ordenados por fecha ascendente.

    Example:
        >>> get_mexico_holidays(2025)
        [
            {"date": "2025-01-01", "name": "New Year's Day",
             "description": "Año Nuevo — ...", "is_fixed": true},
            ...
        ]
    """
    mx_holidays = _get_holidays("MX", year)
    result: list[dict] = []

    for h_date, h_name in sorted(mx_holidays.items()):
        description = _MX_HOLIDAY_DESCRIPTIONS.get(h_name, h_name)
        # Los feriados "observados" en lunes son los móviles (ej: Día de la Constitución)
        is_fixed = not any(
            keyword in h_name.lower()
            for keyword in ["observed", "day off"]
        )
        result.append({
            "date": h_date.isoformat(),
            "name": h_name,
            "description": description,
            "is_fixed": is_fixed,
            "day_of_week": h_date.strftime("%A"),
            "country": "MX",
            "region": None,
            "legal_basis": "Ley Federal del Trabajo, Art. 74",
        })

    return result


def get_country_list() -> list[dict]:
    """
    Retorna la lista de todos los países soportados por la librería `holidays`.

    Incluye el código ISO 3166-1 alpha-2 y el nombre del país en inglés.
    Se puede usar para validar códigos de país antes de llamar otras herramientas.

    Returns:
        Lista de diccionarios con `code` (código ISO alpha-2) y `name`
        (nombre del país en inglés), ordenados por código.

    Example:
        >>> get_country_list()
        [{"code": "AR", "name": "Argentina"}, {"code": "MX", "name": "Mexico"}, ...]
    """
    supported = holidays.list_supported_countries()
    result: list[dict] = []
    for code, subdivisions in sorted(supported.items()):
        # Obtener nombre del país (la librería holidays lo tiene en el módulo)
        country_cls = getattr(holidays, code, None)
        name = getattr(country_cls, "country", code) if country_cls else code

        result.append({
            "code": code,
            "name": name,
            "has_subdivisions": bool(subdivisions),
            "subdivisions": sorted(subdivisions) if subdivisions else [],
        })

    return result
