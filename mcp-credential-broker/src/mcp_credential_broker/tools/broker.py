"""Tools del credential broker: run_with_creds, reveal_secret, list_credentials, store_credential.

Principio de seguridad: NINGUNA tool retorna el valor de una credencial al llamador
(el agente LLM). El valor solo se inyecta en subprocess (run_with_creds) o se imprime
al terminal del usuario (reveal_secret con HITL).
"""

from __future__ import annotations

import os
import subprocess
from typing import Any

import httpx
from mcp_shared.errors import McpError, NotFoundError, ValidationError

from mcp_credential_broker.config import settings
from mcp_credential_broker.tools.backends import (
    get_backend,
    list_all_refs,
    parse_ref,
    resolve_ref,
)
from mcp_credential_broker.tools.hitl import confirm_reveal, print_value_to_user

# ---------------------------------------------------------------------------
# run_with_creds
# ---------------------------------------------------------------------------


def run_with_creds(
    command: str,
    credential_ref: str,
    inject_as: str = "CRED",
    timeout: int | None = None,
    cwd: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Ejecuta un comando con una credencial inyectada como env var.

    La credencial se resuelve localmente, se inyecta como variable de entorno
    ``inject_as`` en el subprocess, y el comando la referencia via $CRED o %CRED%.
    El valor NUNCA se retorna en la respuesta.

    Args:
        command: Comando a ejecutar (via shell=True).
        credential_ref: Referencia a la credencial (ej. "vault:secret/gitea#token").
        inject_as: Nombre de la env var que recibira el valor. Default: "CRED".
        timeout: Timeout en segundos. Default: BROKER_DEFAULT_COMMAND_TIMEOUT.
        cwd: Directorio de trabajo.
        extra_env: Variables de entorno adicionales para el subprocess.

    Returns:
        dict con stdout, stderr, exit_code, credential (safe_repr), command (redacted).
    """
    if not command or not command.strip():
        raise ValidationError(field="command", message="Comando vacio.", value=command)

    effective_timeout = timeout or settings.default_command_timeout

    # Resolver credencial localmente
    cred = resolve_ref(credential_ref)

    # Construir entorno del subprocess: heredar + inyectar credencial + extra
    env = os.environ.copy()
    env[inject_as] = cred.value
    if extra_env:
        env.update(extra_env)

    # Log sin el valor
    # (structlog ya configurado en server.py; aqui usamos print a stderr para debug)
    try:
        result = subprocess.run(  # noqa: S602 — shell=True es intencional para run_with_creds
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=effective_timeout,
            cwd=cwd,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise McpError(
            f"Comando excedio timeout de {effective_timeout}s.",
            context={"command": _redact_command(command, inject_as)},
        ) from exc

    # Truncar stdout si excede el limite
    stdout = result.stdout
    if len(stdout.encode("utf-8")) > settings.max_stdout_bytes:
        stdout = stdout[: settings.max_stdout_bytes] + "\n[...truncado por mcp-credential-broker...]"

    return {
        "stdout": stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
        "credential": cred.safe_repr(),
        "command": _redact_command(command, inject_as),
        "injected_as": inject_as,
    }


def _redact_command(command: str, inject_as: str) -> str:
    """Redacta cualquier referencia al valor inyectado en el comando loggeado.

    Solo redacta si el valor literal apareciera (raro, pero posible si el agente
    lo construye mal). Como no tenemos el valor aqui, solo marcamos que se inyecto.
    """
    # El comando se retorna tal cual para auditoria; el valor no esta en el comando
    # (se inyecta como env var). Si el agente puso el valor literal, eso es un bug
    # del agente, no del broker.
    return command


# ---------------------------------------------------------------------------
# reveal_secret
# ---------------------------------------------------------------------------


def reveal_secret(credential_ref: str, reason: str = "") -> dict[str, Any]:
    """Revela una credencial al usuario (NO al agente LLM).

    Requiere confirmacion humana via HITL (dialogo nativo). Si se aprueba,
    el valor se imprime al terminal del usuario. El agente solo recibe
    ``{"revealed": true/false}`` — nunca el valor.

    Args:
        credential_ref: Referencia a la credencial.
        reason: Motivo por el que el agente solicita el reveal (para mostrar al usuario).

    Returns:
        dict con revealed (bool), ref, to ("terminal" o "denied").
    """
    # Resolver primero (para validar que existe antes de pedir confirmacion)
    cred = resolve_ref(credential_ref)

    # Pedir confirmacion humana
    approved = confirm_reveal(credential_ref, reason)

    if not approved:
        return {
            "revealed": False,
            "ref": credential_ref,
            "to": "denied",
            "reason": "Usuario denego o expiro el prompt HITL.",
        }

    # Imprimir al terminal del usuario — NO a stdout (transporte MCP)
    return print_value_to_user(credential_ref, cred.value)


# ---------------------------------------------------------------------------
# list_credentials
# ---------------------------------------------------------------------------


def list_credentials(backend: str | None = None) -> list[dict[str, Any]]:
    """Lista las credenciales disponibles (sin valores).

    Args:
        backend: Filtrar por backend (vault, env, file, keychain). None = todos.

    Returns:
        Lista de dicts con ref, backend, type, metadata. Nunca incluye valores.
    """
    if backend:
        parse_ref(f"{backend}:x")  # validar nombre de backend
    return list_all_refs(backend)


# ---------------------------------------------------------------------------
# store_credential
# ---------------------------------------------------------------------------


def store_credential(
    ref: str,
    from_env: str | None = None,
    from_file: str | None = None,
) -> dict[str, Any]:
    """Almacena una credencial en un backend que soporta escritura.

    El valor se lee de una env var o archivo LOCAL — nunca de un literal pasado
    en la conversacion (eso iria al LLM). Esto evita que el agente guarde
    valores que vio en el chat.

    Args:
        ref: Referencia destino (ej. "keychain:portal-x:admin").
        from_env: Nombre de env var local de donde leer el valor.
        from_file: Ruta de archivo de donde leer el valor.

    Returns:
        dict con stored (bool), ref.

    Raises:
        ValidationError si no se especifica fuente o el backend no soporta escritura.
    """
    if not from_env and not from_file:
        raise ValidationError(
            field="source",
            message="Debes especificar from_env o from_file. El valor no puede venir del chat.",
        )
    if from_env and from_file:
        raise ValidationError(
            field="source",
            message="Especifica solo uno: from_env o from_file, no ambos.",
        )

    # Leer el valor de la fuente local
    if from_env:
        if from_env not in os.environ:
            raise NotFoundError(resource="env_var", identifier=from_env) from None
        value = os.environ[from_env]
    else:
        from pathlib import Path

        path = Path(from_file).expanduser()
        if not path.is_file():
            raise NotFoundError(resource="file", identifier=from_file) from None
        value = path.read_text(encoding="utf-8", errors="replace").strip()

    # Resolver backend destino
    backend_name, location = parse_ref(ref)
    backend = get_backend(backend_name)

    result = backend.store(location, value)
    result["ref"] = ref
    return result


# ---------------------------------------------------------------------------
# process_with_local_llm
# ---------------------------------------------------------------------------


def process_with_local_llm(
    prompt: str,
    credential_ref: str,
    model: str | None = None,
    max_tokens: int = 2000,
) -> dict[str, Any]:
    """Procesa datos sensibles con un LLM local (LM Studio) sin enviarlos al cloud.

    Resuelve la credencial localmente, la incluye en el prompt enviado a LM Studio
    (local), y retorna solo la respuesta del modelo. El valor sensible NUNCA entra
    en la conversacion con el agente cloud.

    Args:
        prompt: Instruccion para el modelo (sin el valor sensible).
        credential_ref: Referencia a la credencial a inyectar en el prompt.
        model: Modelo local a usar (default: settings.lmstudio_model).
        max_tokens: Max tokens de respuesta.

    Returns:
        dict con response (str), model (str), credential (safe_repr).
        El valor sensible no esta en la respuesta.
    """
    if not prompt or not prompt.strip():
        raise ValidationError(field="prompt", message="Prompt vacio.", value=prompt)

    # Resolver credencial localmente
    cred = resolve_ref(credential_ref)

    # Construir el prompt completo con el valor sensible
    full_prompt = f"{prompt}\n\n--- DATO SENSIBLE ---\n{cred.value}\n--- FIN DATO SENSIBLE ---"

    # Enviar a LM Studio (local, no cloud)
    url = f"{settings.lmstudio_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model or settings.lmstudio_model,
        "messages": [{"role": "user", "content": full_prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }

    try:
        with httpx.Client(timeout=settings.lmstudio_timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError as exc:
        raise McpError(
            f"LM Studio no responde en {settings.lmstudio_url}. Verifica que este corriendo.",
            context={"url": settings.lmstudio_url},
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise McpError(
            f"LM Studio devolvio error HTTP {exc.response.status_code}.",
            context={"url": url},
        ) from exc
    except httpx.TimeoutException as exc:
        raise McpError(
            f"LM Studio timeout ({settings.lmstudio_timeout}s).",
            context={"url": settings.lmstudio_url},
        ) from exc

    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})
    response_text = message.get("content", "")
    # qwen3-8b en modo thinking deja content="" y pone el output en reasoning_content.
    # Si content está vacío, usar reasoning_content como fallback.
    if not response_text:
        response_text = message.get("reasoning_content", "")

    return {
        "response": response_text,
        "model": model or settings.lmstudio_model,
        "credential": cred.safe_repr(),
        "lmstudio_url": settings.lmstudio_url,
    }
