"""Tools de notificación: email (SMTP) y Telegram Bot API."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx

from mcp_notify.config import settings
from mcp_shared.errors import McpError, ValidationError


def send_email(
    to: str,
    subject: str,
    body: str,
    html: bool = False,
) -> dict[str, Any]:
    """Envía un email vía SMTP."""
    if not settings.smtp_host:
        raise ValidationError(field="smtp_host", message="SMTP no configurado. Establece NOTIFY_SMTP_HOST.")
    if not settings.smtp_from:
        raise ValidationError(field="smtp_from", message="Remitente no configurado. Establece NOTIFY_SMTP_FROM.")
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        if html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.default_timeout) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, [to], msg.as_string())

        return {"to": to, "subject": subject, "status": "sent"}
    except smtplib.SMTPException as exc:
        raise McpError(f"SMTP error: {exc}") from exc
    except Exception as exc:
        raise McpError(f"Error enviando email: {exc}") from exc


def send_telegram_message(chat_id: str, text: str) -> dict[str, Any]:
    """Envía un mensaje vía Telegram Bot API."""
    if not settings.telegram_bot_token:
        raise ValidationError(
            field="telegram_bot_token",
            message="Telegram no configurado. Establece NOTIFY_TELEGRAM_BOT_TOKEN.",
        )
    try:
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        with httpx.Client(timeout=settings.default_timeout) as client:
            resp = client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
            resp.raise_for_status()
            data = resp.json()
            return {
                "chat_id": chat_id,
                "message_id": data.get("result", {}).get("message_id"),
                "status": "sent" if data.get("ok") else "failed",
            }
    except httpx.HTTPStatusError as exc:
        raise McpError(f"Telegram API error: {exc.response.status_code} - {exc.response.text[:200]}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def send_slack_message(
    text: str,
    channel: str = "",
    blocks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Envía un mensaje vía Slack Incoming Webhook.

    Args:
        text: Texto del mensaje (plain text o Markdown de Slack).
        channel: Canal override (opcional, si no se usa el del webhook).
        blocks: Bloques estructurados de Slack (opcional, formato Block Kit).
    """
    if not settings.slack_webhook_url:
        raise ValidationError(
            field="slack_webhook_url",
            message="Slack no configurado. Establece NOTIFY_SLACK_WEBHOOK_URL.",
        )
    try:
        payload: dict[str, Any] = {"text": text}
        if channel or settings.slack_channel:
            payload["channel"] = channel or settings.slack_channel
        if blocks:
            payload["blocks"] = blocks

        with httpx.Client(timeout=settings.default_timeout) as client:
            resp = client.post(settings.slack_webhook_url, json=payload)
            resp.raise_for_status()
            # Slack webhook responde con "ok" o un JSON de error
            if resp.text.strip() == "ok":
                return {"status": "sent", "response": "ok"}
            data = resp.json()
            return {"status": "sent" if data.get("ok", True) else "failed", "response": data}
    except httpx.HTTPStatusError as exc:
        raise McpError(f"Slack API error: {exc.response.status_code} - {exc.response.text[:200]}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc
