"""Resources de solo lectura para mcp-calendar.

Expone metadatos, guias y consejos sobre calendario, dias habiles y divisas
como URIs accesibles para el modelo a traves de `@mcp.resource`.
"""

from __future__ import annotations

import json

from mcp_calendar.config import CalendarSettings

settings = CalendarSettings()


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


def calendar_configuration() -> str:
    """Configuracion actual del servidor calendar."""
    return json.dumps(
        {
            "default_country": settings.default_country,
            "exchange_cache_ttl_seconds": settings.exchange_cache_ttl_seconds,
            "mcp_server_name": settings.mcp_server_name,
        },
        indent=2,
        ensure_ascii=False,
    )


def supported_countries() -> str:
    """Paises soportados para calculo de dias habiles."""
    return (
        "# Paises soportados\n\n"
        "El servidor usa la libreria `holidays` que soporta 100+ paises.\n"
        "Usa get_country_list() para obtener la lista completa.\n\n"
        "Algunos paises populares:\n"
        "- MX — Mexico\n"
        "- US — Estados Unidos\n"
        "- CA — Canada\n"
        "- GB — Reino Unido\n"
        "- DE — Alemania\n"
        "- FR — Francia\n"
        "- ES — Espana\n"
        "- CO — Colombia\n"
        "- AR — Argentina\n"
        "- BR — Brasil\n"
        "- JP — Japon\n"
        "- CN — China\n"
        "- IN — India\n"
        "- AU — Australia\n"
        "\n"
        "Codigos ISO 3166-1 alpha-2 (2 letras)."
    )


def mexico_holidays_guide() -> str:
    """Guia de feriados mexicanos."""
    return (
        "# Feriados de Mexico\n\n"
        "Dias de descanso obligatorio (Ley Federal del Trabajo, Art. 74):\n"
        "- 1 de enero — Ano Nuevo\n"
        "- Primer lunes de febrero — Dia de la Constitucion\n"
        "- Tercer lunes de marzo — Natalicio de Benito Juarez\n"
        "- 1 de mayo — Dia del Trabajo\n"
        "- 16 de septiembre — Dia de la Independencia\n"
        "- Tercer lunes de noviembre — Dia de la Revolucion\n"
        "- 1 de diciembre (cada 6 anos) — Transmision del Poder Ejecutivo\n"
        "- 25 de diciembre — Navidad\n"
        "\n"
        "Usa get_mexico_holidays(year) para obtener feriados con descripciones."
    )


def currency_api_info() -> str:
    """Informacion sobre la API de divisas."""
    return (
        "# API de divisas — Frankfurter\n\n"
        "- URL: https://api.frankfurter.app\n"
        "- Gratuita, sin API key requerida.\n"
        "- Datos del Banco Central Europeo (BCE).\n"
        "- Actualizacion diaria (dias habiles del BCE).\n"
        "- Datos historicos desde 1999-01-04.\n"
        "- Caché en memoria con TTL configurable.\n"
        "- EXCHANGE_CACHE_TTL_SECONDS controla el TTL (default 3600s)."
    )


def iso_date_format_guide() -> str:
    """Guia de formato de fechas ISO 8601."""
    return (
        "# Formato ISO 8601\n\n"
        "Todas las fechas usan formato ISO 8601: YYYY-MM-DD\n\n"
        "Ejemplos:\n"
        "- 2025-01-15 — 15 de enero de 2025\n"
        "- 2025-12-31 — 31 de diciembre de 2025\n"
        "- 1999-01-04 — 4 de enero de 1999\n"
        "\n"
        "El servidor valida el formato y rechaza fechas invalidas.\n"
        "Para fechas historicas de divisas, el rango es 1999-01-04 a hoy."
    )


def business_days_tips() -> str:
    """Consejos de calculo de dias habiles."""
    return (
        "# Calculo de dias habiles\n\n"
        "- Los dias habiles excluyen fines de semana (sabado y domingo).\n"
        "- Tambien excluyen los feriados del pais especificado.\n"
        "- calculate_business_days incluye ambas fechas (inicio y fin).\n"
        "- add_business_days no cuenta la fecha de inicio como dia habil.\n"
        "- next_business_day retorna el SIGUIENTE dia habil (no el actual).\n"
        "- previous_business_day retorna el ANTERIOR dia habil (no el actual)."
    )


def currency_conversion_tips() -> str:
    """Consejos de conversion de divisas."""
    return (
        "# Conversion de divisas\n\n"
        "- get_exchange_rate obtiene la tasa actual entre dos divisas.\n"
        "- convert_currency convierte un monto usando la tasa actual.\n"
        "- get_historical_rate obtiene la tasa para una fecha especifica.\n"
        "- get_rate_history obtiene una serie historica entre dos fechas.\n"
        "- get_mx_rates obtiene tasas MXN vs principales divisas.\n"
        "- Los codigos de divisa son ISO 4217 (3 letras): USD, EUR, MXN, etc.\n"
        "- Los resultados se cachean para reducir llamadas a la API."
    )


def common_calendar_workflows() -> str:
    """Flujos de trabajo comunes del calendario."""
    return (
        "# Flujos comunes\n\n"
        "- **Feriados**: get_holidays(country='MX', year=2025)\n"
        "- **Dias habiles**: calculate_business_days('2025-01-01', '2025-01-31')\n"
        "- **Sumar dias**: add_business_days('2025-01-15', 10)\n"
        "- **Es habil?**: is_business_day('2025-01-15')\n"
        "- **Siguiente habil**: next_business_day('2025-01-17')\n"
        "- **Anterior habil**: previous_business_day('2025-01-20')\n"
        "- **Dias del mes**: business_days_in_month(2025, 1)\n"
        "- **Feriados MX**: get_mexico_holidays(2025)\n"
        "- **Tasa USD/MXN**: get_exchange_rate('USD', 'MXN')\n"
        "- **Convertir**: convert_currency(100, 'USD', 'MXN')\n"
        "- **Tasa historica**: get_historical_rate('USD', 'MXN', '2025-01-15')\n"
        "- **Historial**: get_rate_history('USD', 'MXN', '2025-01-01', '2025-01-31')"
    )


def calendar_error_codes() -> str:
    """Codigos de error comunes del calendario."""
    return json.dumps(
        {
            "errors": [
                {"code": "VALIDATION_ERROR", "description": "Formato de fecha invalido o parametro incorrecto"},
                {"code": "INVALID_VALUE", "description": "Codigo de pais o divisa no soportado"},
                {"code": "API_ERROR", "description": "Error en la API de Frankfurter"},
                {"code": "NETWORK_ERROR", "description": "Error de red al contactar la API"},
                {"code": "NETWORK_TIMEOUT", "description": "Timeout al contactar la API"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def iso_week_info() -> str:
    """Informacion sobre semanas ISO."""
    return (
        "# Semanas ISO 8601\n\n"
        "- La semana 1 es la que contiene el primer jueves del ano.\n"
        "- Equivale a la semana que contiene el 4 de enero.\n"
        "- Los anos pueden tener 52 o 53 semanas.\n"
        "- El dia de la semana va de 1 (lunes) a 7 (domingo).\n"
        "- Usa get_week_number(date) para obtener el numero de semana ISO."
    )


def quarter_info() -> str:
    """Informacion sobre trimestres."""
    return (
        "# Trimestres (Quarters)\n\n"
        "- Q1: Enero - Marzo (meses 1-3)\n"
        "- Q2: Abril - Junio (meses 4-6)\n"
        "- Q3: Julio - Septiembre (meses 7-9)\n"
        "- Q4: Octubre - Diciembre (meses 10-12)\n"
        "- Usa get_quarter_info(date) para obtener el trimestre de una fecha."
    )


def easter_calculation() -> str:
    """Informacion sobre el calculo de Pascua."""
    return (
        "# Calculo de Pascua\n\n"
        "- Pascua se calcula con el algoritmo de Gauss (Computus).\n"
        "- Es el primer domingo despues de la primera luna llena de primavera.\n"
        "- Varia entre el 22 de marzo y el 25 de abril.\n"
        "- Muchos feriados religiosos dependen de la fecha de Pascua.\n"
        "- Usa get_easter(year) para obtener la fecha de Pascua."
    )


def date_arithmetic_tips() -> str:
    """Consejos de aritmetica de fechas."""
    return (
        "# Aritmetica de fechas\n\n"
        "- date_diff calcula la diferencia entre dos fechas en dias.\n"
        "- add_business_days suma/resta dias habiles.\n"
        "- next_business_day y previous_business_day navegan dias habiles.\n"
        "- business_days_in_month cuenta dias habiles de un mes.\n"
        "- Todas las fechas usan formato ISO 8601 (YYYY-MM-DD)."
    )


def example_business_days() -> str:
    """Ejemplo de calculo de dias habiles."""
    return (
        "# Ejemplo: calculate_business_days\n\n"
        "```\n"
        "calculate_business_days(\n"
        "    start_date='2025-01-01',\n"
        "    end_date='2025-01-31',\n"
        "    country='MX'\n"
        ")\n"
        "```\n"
        "Retorna: business_days, total_days, weekend_days, holidays_excluded, country"
    )


def example_currency_conversion() -> str:
    """Ejemplo de conversion de divisas."""
    return (
        "# Ejemplo: convert_currency\n\n"
        "```\n"
        "convert_currency(\n"
        "    amount=1000,\n"
        "    from_currency='USD',\n"
        "    to_currency='MXN'\n"
        ")\n"
        "```\n"
        "Retorna: original_amount, converted_amount, rate"
    )
