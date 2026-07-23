from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_browser.config import settings
from mcp_browser.tools import (
    capture_page,
    click_element,
    evaluate_js,
    extract_page,
    fill_form,
    get_cookies,
    get_page_links,
    get_page_metadata,
    get_page_text,
    get_page_title,
    scroll_page,
    set_viewport,
    wait_for_selector,
)
from mcp_browser import resources as res

setup_logging(
    log_level=settings.log_level, log_format=settings.log_format, server_name="mcp-browser"
)
logger = get_logger(__name__)
mcp = FastMCP(
    name="mcp-browser", instructions="Automatizacion web con Playwright y allowlist opcional."
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Tools originales
# ---------------------------------------------------------------------------


@mcp.tool(name="browser_extract")
def tool_extract(url: str, selector: str = "body") -> dict[str, Any]:
    return _handle(
        extract_page,
        url,
        settings.allowed_hosts,
        settings.headless,
        settings.timeout_ms,
        selector,
    )


@mcp.tool(name="browser_screenshot")
def tool_screenshot(
    url: str,
    filename: str = "screenshot.png",
    full_page: bool = True,
) -> dict[str, Any]:
    return _handle(
        capture_page,
        url,
        settings.allowed_hosts,
        settings.output_dir,
        settings.headless,
        settings.timeout_ms,
        filename,
        full_page,
    )


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(name="browser_get_title")
def tool_get_title(url: str) -> dict[str, Any]:
    return _handle(get_page_title, url, settings.allowed_hosts, settings.headless, settings.timeout_ms)


@mcp.tool(name="browser_get_links")
def tool_get_links(url: str) -> dict[str, Any]:
    return _handle(get_page_links, url, settings.allowed_hosts, settings.headless, settings.timeout_ms)


@mcp.tool(name="browser_get_metadata")
def tool_get_metadata(url: str) -> dict[str, Any]:
    return _handle(get_page_metadata, url, settings.allowed_hosts, settings.headless, settings.timeout_ms)


@mcp.tool(name="browser_get_text")
def tool_get_text(url: str) -> dict[str, Any]:
    return _handle(get_page_text, url, settings.allowed_hosts, settings.headless, settings.timeout_ms)


@mcp.tool(name="browser_click")
def tool_click(url: str, selector: str) -> dict[str, Any]:
    return _handle(click_element, url, selector, settings.allowed_hosts, settings.headless, settings.timeout_ms)


@mcp.tool(name="browser_fill_form")
def tool_fill_form(
    url: str,
    fields: dict[str, str],
    submit_selector: str | None = None,
) -> dict[str, Any]:
    return _handle(
        fill_form,
        url,
        fields,
        settings.allowed_hosts,
        settings.headless,
        settings.timeout_ms,
        submit_selector,
    )


@mcp.tool(name="browser_wait_for")
def tool_wait_for(url: str, selector: str, state: str = "visible") -> dict[str, Any]:
    return _handle(
        wait_for_selector,
        url,
        selector,
        settings.allowed_hosts,
        settings.headless,
        settings.timeout_ms,
        state,
    )


@mcp.tool(name="browser_scroll")
def tool_scroll(url: str, pixels: int = 500) -> dict[str, Any]:
    return _handle(scroll_page, url, settings.allowed_hosts, settings.headless, settings.timeout_ms, pixels)


@mcp.tool(name="browser_evaluate")
def tool_evaluate(url: str, expression: str) -> dict[str, Any]:
    return _handle(evaluate_js, url, expression, settings.allowed_hosts, settings.headless, settings.timeout_ms)


@mcp.tool(name="browser_get_cookies")
def tool_get_cookies(url: str) -> dict[str, Any]:
    return _handle(get_cookies, url, settings.allowed_hosts, settings.headless, settings.timeout_ms)


@mcp.tool(name="browser_set_viewport")
def tool_set_viewport(url: str, width: int, height: int) -> dict[str, Any]:
    return _handle(set_viewport, url, width, height, settings.allowed_hosts, settings.headless, settings.timeout_ms)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("browser://supported-selectors")
def res_selectors() -> str:
    return res.supported_selectors()


@mcp.resource("browser://playwright-tips")
def res_playwright() -> str:
    return res.playwright_tips()


@mcp.resource("browser://scraping-best-practices")
def res_scraping() -> str:
    return res.web_scraping_best_practices()


@mcp.resource("browser://security-guide")
def res_security() -> str:
    return res.browser_security_guide()


@mcp.resource("browser://css-cheatsheet")
def res_css() -> str:
    return res.css_selector_cheatsheet()


@mcp.resource("browser://screenshot-tips")
def res_screenshot() -> str:
    return res.screenshot_tips()


@mcp.resource("browser://use-cases")
def res_use_cases() -> str:
    return res.common_use_cases()


@mcp.resource("browser://configuration")
def res_config() -> str:
    return res.browser_configuration()


@mcp.resource("browser://error-handling")
def res_errors() -> str:
    return res.error_handling_tips()


@mcp.resource("browser://playwright-installation")
def res_install() -> str:
    return res.playwright_installation_guide()


@mcp.resource("browser://interaction-patterns")
def res_patterns() -> str:
    return res.page_interaction_patterns()


@mcp.resource("browser://url-validation-rules")
def res_url_rules() -> str:
    return res.url_validation_rules()


@mcp.resource("browser://examples/extract")
def res_example_extract() -> str:
    return res.example_extract_page()


@mcp.resource("browser://examples/screenshot")
def res_example_screenshot() -> str:
    return res.example_screenshot()


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
