import pytest
from mcp_browser.tools.browser_tools import validate_url
from mcp_shared.errors import ValidationError


def test_validate_url() -> None:
    assert validate_url("https://example.com", ["example.com"]) == "https://example.com"


@pytest.mark.parametrize(
    "url",
    ["file:///etc/passwd", "ftp://example.com", "https://user:pass@example.com"],
)
def test_validate_url_rejects_unsafe_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        validate_url(url, [])


def test_validate_url_enforces_allowlist() -> None:
    with pytest.raises(ValidationError, match="no esta permitido"):
        validate_url("https://example.com", ["internal.test"])
