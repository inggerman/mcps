"""Sentry/GlitchTip integration for MCP servers.

Shared module usable by all 59 MCP servers. Reads the DSN from the
`SENTRY_DSN` environment variable (injected by Vault/ESO, never hardcoded).
When the DSN is absent, initialization is a no-op so local development and
tests are unaffected.

Environment variables:
    SENTRY_DSN: GlitchTip/Sentry ingest DSN. When unset, tracking is disabled.
    SENTRY_ENVIRONMENT: deployment environment (default: production).
    SENTRY_RELEASE: release version (default: mcp-<server-name>).
    SENTRY_TRACES_SAMPLE_RATE: traces sample rate 0-1 (default: 0.0).
    SENTRY_SEND_DEFAULT_PII: send PII (default: false).
"""

from __future__ import annotations

import os

import structlog

logger = structlog.get_logger(__name__)

_INITIALIZED = False

_REDACTED = "[Filtered]"
_SECRET_KEYS = {
    "authorization",
    "password",
    "passwd",
    "token",
    "api_key",
    "apikey",
    "secret",
    "secret_key",
    "dsn",
    "database_url",
    "mcp_token",
}


def init_error_tracking(server_name: str = "mcp") -> None:
    """Initialize Sentry SDK if SENTRY_DSN is set; no-op otherwise.

    Args:
        server_name: MCP server name for release tagging (e.g. "mcp-comfyui").
    """
    global _INITIALIZED
    if _INITIALIZED:
        return

    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        logger.info("error_tracking_disabled", reason="SENTRY_DSN not set")
        return

    try:
        import sentry_sdk
    except ImportError:
        logger.warning(
            "error_tracking_unavailable",
            reason="sentry-sdk not installed; add sentry-sdk to dependencies",
        )
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        release=os.environ.get("SENTRY_RELEASE", f"{server_name}@latest"),
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        send_default_pii=os.environ.get("SENTRY_SEND_DEFAULT_PII", "false").lower()
        in ("1", "true", "yes"),
        before_send=_scrub_secrets,
    )
    _INITIALIZED = True
    logger.info(
        "error_tracking_initialized",
        server_name=server_name,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
    )


def _scrub_secrets(event: dict, hint: dict | None = None) -> dict | None:
    """Before-send hook: redact known secret-bearing fields before ingest."""

    def _scrub(obj: object) -> object:
        if isinstance(obj, dict):
            return {
                k: (_REDACTED if k.lower() in _SECRET_KEYS else _scrub(v))
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_scrub(item) for item in obj]
        return obj

    try:
        if "request" in event and isinstance(event["request"], dict):
            headers = event["request"].get("headers")
            if isinstance(headers, dict):
                event["request"]["headers"] = {
                    k: (_REDACTED if k.lower() in _SECRET_KEYS else v)
                    for k, v in headers.items()
                }
        if "extra" in event:
            event["extra"] = _scrub(event["extra"])
    except Exception:
        return None
    return event


def capture_exception(exc: BaseException, **context: str) -> None:
    """Capture an exception with optional context tags. No-op if not initialized."""
    if not _INITIALIZED:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_tag(key, value)
            sentry_sdk.capture_exception(exc)
    except Exception:
        pass


def shutdown_error_tracking() -> None:
    """Flush pending events on shutdown. Safe to call when not initialized."""
    global _INITIALIZED
    if not _INITIALIZED:
        return
    try:
        import sentry_sdk

        sentry_sdk.flush(timeout=2.0)
    except Exception:
        pass
    _INITIALIZED = False
