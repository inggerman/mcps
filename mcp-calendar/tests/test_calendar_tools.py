from __future__ import annotations

import pytest
from mcp_calendar.tools.business_days import (
    add_business_days,
    calculate_business_days,
    is_business_day,
)
from mcp_shared.errors import InvalidValueError, ValidationError


def test_calculate_business_days_for_regular_week() -> None:
    result = calculate_business_days("2025-01-06", "2025-01-10", "MX")
    assert result["business_days"] == 5
    assert result["total_days"] == 5


def test_add_business_days_skips_weekend() -> None:
    assert add_business_days("2025-01-10", 1, "MX") == "2025-01-13"


def test_is_business_day_detects_weekend() -> None:
    result = is_business_day("2025-01-11", "MX")
    assert result["is_business_day"] is False
    assert result["is_weekend"] is True


def test_invalid_date_is_rejected() -> None:
    with pytest.raises(ValidationError):
        calculate_business_days("not-a-date", "2025-01-10", "MX")


def test_inverted_range_is_rejected() -> None:
    with pytest.raises(InvalidValueError):
        calculate_business_days("2025-01-10", "2025-01-01", "MX")
