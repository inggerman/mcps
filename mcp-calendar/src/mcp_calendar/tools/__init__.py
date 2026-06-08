"""Paquete de herramientas del servidor mcp-calendar."""

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

__all__ = [
    # Business days
    "get_holidays",
    "calculate_business_days",
    "add_business_days",
    "is_business_day",
    "next_business_day",
    "previous_business_day",
    "business_days_in_month",
    "get_mexico_holidays",
    "get_country_list",
    # Currency
    "get_exchange_rate",
    "convert_currency",
    "get_historical_rate",
    "get_mx_rates",
    "list_supported_currencies",
    "get_rate_history",
]
