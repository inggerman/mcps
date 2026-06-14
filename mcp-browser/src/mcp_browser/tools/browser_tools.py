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
            field="url", message=f"El host '{parsed.hostname}' no está permitido."
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
        raise ValidationError(field="filename", message="La captura debe usar extensión .png.")
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = (output_dir / safe_name).resolve()
    if not destination.is_relative_to(output_dir.resolve()):
        raise ValidationError(field="filename", message="Nombre de archivo inválido.")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(target, wait_until="networkidle", timeout=timeout_ms)
            page.screenshot(path=str(destination), full_page=full_page)
            return {"url": page.url, "path": str(destination)}
        finally:
            browser.close()
