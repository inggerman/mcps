from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from mcp_shared.errors import ValidationError


def validate_url(url: str, allowed_hosts: list[str]) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError(field="url", message="Solo se permiten URLs HTTP(S).")
    if parsed.username or parsed.password:
        raise ValidationError(field="url", message="No se permiten credenciales embebidas.")
    if allowed_hosts and parsed.hostname not in allowed_hosts:
        raise ValidationError(
            field="url", message=f"El host '{parsed.hostname}' no esta permitido."
        )
    return url


def extract_page(
    url: str,
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
    selector: str = "body",
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            locator = page.locator(selector)
            return {
                "url": page.url,
                "title": page.title(),
                "text": locator.inner_text(timeout=timeout_ms),
                "html": locator.inner_html(timeout=timeout_ms),
            }
        finally:
            browser.close()


def capture_page(
    url: str,
    allowed_hosts: list[str],
    output_dir: Path,
    headless: bool,
    timeout_ms: int,
    filename: str = "screenshot.png",
    full_page: bool = True,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    safe_name = Path(filename).name
    if Path(safe_name).suffix.lower() != ".png":
        raise ValidationError(field="filename", message="La captura debe usar extension .png.")
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = (output_dir / safe_name).resolve()
    if not destination.is_relative_to(output_dir.resolve()):
        raise ValidationError(field="filename", message="Nombre de archivo invalido.")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="networkidle", timeout=timeout_ms)
            page.screenshot(path=str(destination), full_page=full_page)
            return {"url": page.url, "path": str(destination)}
        finally:
            browser.close()


def get_page_title(
    url: str,
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            return {"url": page.url, "title": page.title()}
        finally:
            browser.close()


def get_page_links(
    url: str,
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            links = page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => ({href: e.href, text: e.innerText.trim().slice(0, 100)}))",
            )
            return {"url": page.url, "links": links[:200], "link_count": len(links)}
        finally:
            browser.close()


def get_page_metadata(
    url: str,
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            title = page.title()
            description = page.eval_on_selector(
                "meta[name='description']",
                "el => el ? el.content : null",
            )
            og_tags = page.eval_on_selector_all(
                "meta[property^='og:']",
                "els => Object.fromEntries(els.map(e => [e.getAttribute('property'), e.content]))",
            )
            return {
                "url": page.url,
                "title": title,
                "description": description,
                "og_tags": og_tags,
            }
        finally:
            browser.close()


def get_page_text(
    url: str,
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            text = page.inner_text("body", timeout=timeout_ms)
            return {
                "url": page.url,
                "title": page.title(),
                "text": text,
                "word_count": len(text.split()),
            }
        finally:
            browser.close()


def click_element(
    url: str,
    selector: str,
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            page.click(selector, timeout=timeout_ms)
            return {
                "url": page.url,
                "title": page.title(),
                "clicked": selector,
            }
        finally:
            browser.close()


def fill_form(
    url: str,
    fields: dict[str, str],
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
    submit_selector: str | None = None,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            for selector, value in fields.items():
                page.fill(selector, value, timeout=timeout_ms)
            if submit_selector:
                page.click(submit_selector, timeout=timeout_ms)
            return {
                "url": page.url,
                "title": page.title(),
                "fields_filled": list(fields.keys()),
                "submitted": submit_selector is not None,
            }
        finally:
            browser.close()


def wait_for_selector(
    url: str,
    selector: str,
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
    state: str = "visible",
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_selector(selector, state=state, timeout=timeout_ms)
            return {
                "url": page.url,
                "selector": selector,
                "state": state,
                "found": True,
            }
        finally:
            browser.close()


def scroll_page(
    url: str,
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
    pixels: int = 500,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            page.evaluate(f"window.scrollBy(0, {int(pixels)})")
            scroll_y = page.evaluate("window.scrollY")
            return {
                "url": page.url,
                "scrolled_pixels": int(pixels),
                "current_scroll_y": scroll_y,
            }
        finally:
            browser.close()


def evaluate_js(
    url: str,
    expression: str,
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            result = page.evaluate(expression)
            return {
                "url": page.url,
                "expression": expression,
                "result": result,
            }
        finally:
            browser.close()


def get_cookies(
    url: str,
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            cookies = page.context.cookies()
            return {
                "url": page.url,
                "cookies": cookies,
                "cookie_count": len(cookies),
            }
        finally:
            browser.close()


def set_viewport(
    url: str,
    width: int,
    height: int,
    allowed_hosts: list[str],
    headless: bool,
    timeout_ms: int,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    target = validate_url(url, allowed_hosts)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page(viewport={"width": int(width), "height": int(height)})
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            return {
                "url": page.url,
                "title": page.title(),
                "viewport": {"width": int(width), "height": int(height)},
            }
        finally:
            browser.close()
