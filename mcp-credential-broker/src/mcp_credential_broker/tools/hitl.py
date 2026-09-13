"""Human-in-the-loop: prompt nativo para confirmacion de reveal de credenciales.

El MCP corre como subprocess stdio del agente. Su stdin/stdout son el transporte
MCP, por lo que NO podemos usar input() para pedir confirmacion al usuario.
En su lugar usamos:

  - Windows: MessageBox nativo via ctypes (dialogo SI/NO).
  - Unix:    abrir /dev/tty para leer del terminal real.

El valor de la credencial se imprime al TTY/consola del usuario, NUNCA a stdout
(que es el transporte MCP que va al LLM).
"""

from __future__ import annotations

import sys
from typing import Any

from mcp_credential_broker.config import settings


def confirm_reveal(credential_ref: str, reason: str = "") -> bool:
    """Pide confirmacion humana para revelar una credencial.

    Returns:
        True si el usuario aprueba, False si deniega o expira.
    """
    if settings.hitl_auto_deny:
        return False

    prompt_text = f"Revelar credencial '{credential_ref}'?"
    if reason:
        prompt_text += f"\n\nMotivo solicitado: {reason}"

    if sys.platform == "win32":
        return _confirm_windows(prompt_text)
    return _confirm_unix(prompt_text)


def _confirm_windows(prompt_text: str) -> bool:
    """Dialogo nativo Windows via ctypes."""
    try:
        import ctypes

        MB_YESNO = 0x04  # noqa: N806
        MB_ICONQUESTION = 0x20  # noqa: N806
        MB_DEFBUTTON2 = 0x100  # noqa: N806
        result = ctypes.windll.user32.MessageBoxW(
            0,
            prompt_text + "\n\nClick Si para revelar en consola, No para denegar.",
            "mcp-credential-broker — Confirmar reveal",
            MB_YESNO | MB_ICONQUESTION | MB_DEFBUTTON2,
        )
        return result == 6  # IDYES = 6
    except Exception:
        return False


def _confirm_unix(prompt_text: str) -> bool:
    """Lee del TTY real (/dev/tty), no del stdin del proceso."""
    try:
        with open("/dev/tty", encoding="utf-8") as tty:  # noqa: PTH123 — device file
            sys.stderr.write(prompt_text + " [y/N]: ")
            sys.stderr.flush()
            response = tty.readline().strip().lower()
            return response in ("y", "yes", "s", "si")
    except OSError:
        return False


def print_value_to_user(credential_ref: str, value: str) -> dict[str, Any]:
    """Imprime el valor al terminal del usuario (NO a stdout/transporte MCP).

    En Windows escribe a la consola adjunta (sys.stderr).
    En Unix escribe a /dev/tty.
    """
    header = f"\n{'=' * 60}\n  CREDENCIAL REVELADA: {credential_ref}\n{'=' * 60}\n"
    footer = f"\n{'=' * 60}\n  (Este valor NO se envio al agente/LLM)\n{'=' * 60}\n\n"

    if sys.platform == "win32":
        sys.stderr.write(header + value + footer)
        sys.stderr.flush()
    else:
        try:
            with open("/dev/tty", "w", encoding="utf-8") as tty:  # noqa: PTH123 — device file
                tty.write(header + value + footer)
        except OSError:
            sys.stderr.write(header + value + footer)
            sys.stderr.flush()

    return {"revealed": True, "to": "terminal", "ref": credential_ref}
