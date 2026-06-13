"""Herramienta para invocar LLMs con salidas estructuradas (JSON Schema).

Soporta cuatro proveedores:
- ``bedrock-converse``          → Bedrock Converse API (outputConfig.textFormat)
- ``bedrock-invoke-claude``     → Bedrock InvokeModel con Anthropic Claude (output_config.format)
- ``bedrock-invoke-openweight`` → Bedrock InvokeModel con modelos open-weight (response_format)
- ``openai-compatible``         → Cualquier endpoint OpenAI-compatible

Las credenciales AWS se leen desde el entorno / perfil boto3 (no se pasan como parámetro).
"""

from __future__ import annotations

import json
from typing import Any

from mcp_shared.errors import ApiError, NetworkError, ParseError, ValidationError

_BOTO3_MISSING = "boto3 no está instalado. Ejecuta: pip install boto3"
_APP_JSON = "application/json"

_VALID_PROVIDERS: frozenset[str] = frozenset(
    {
        "bedrock-converse",
        "bedrock-invoke-claude",
        "bedrock-invoke-openweight",
        "openai-compatible",
    }
)


def invoke_structured(
    prompt: str,
    schema: dict[str, Any],
    schema_name: str = "response",
    provider: str = "bedrock-converse",
    model_id: str = "amazon.nova-pro-v1:0",
    system_prompt: str | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.0,
    region: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Llama a un LLM y garantiza que la respuesta cumpla el JSON Schema dado.

    Args:
        prompt: Mensaje del usuario / instrucción.
        schema: JSON Schema al que debe ceñirse la respuesta.
        schema_name: Nombre descriptivo del schema (requerido por algunas APIs).
        provider: Proveedor a usar. Uno de: ``bedrock-converse``,
            ``bedrock-invoke-claude``, ``bedrock-invoke-openweight``,
            ``openai-compatible``.
        model_id: Identificador del modelo en el proveedor (p.ej.
            ``"amazon.nova-pro-v1:0"`` o ``"anthropic.claude-3-5-sonnet-20241022-v2:0"``).
        system_prompt: System prompt opcional.
        max_tokens: Máximo de tokens a generar (default 2048).
        temperature: Temperatura de muestreo (default 0.0 — ideal para structured output).
        region: Región AWS. Si None usa la región configurada en settings o el entorno.
        base_url: URL base del endpoint (solo para ``openai-compatible``).

    Returns:
        Dict con:
        - ``result`` (dict): Objeto JSON estructurado que cumple el schema.
        - ``provider`` (str): Proveedor usado.
        - ``model_id`` (str): Modelo usado.
        - ``usage`` (dict): ``{"input_tokens": int, "output_tokens": int}``.

    Raises:
        ValidationError: Si el provider no es válido o los parámetros son incorrectos.
        ApiError: Si la API devuelve un error HTTP / de servicio.
        ParseError: Si la respuesta no es JSON válido.
    """
    if provider not in _VALID_PROVIDERS:
        raise ValidationError(
            field="provider",
            message=(
                f"Provider '{provider}' no válido. Opciones: {', '.join(sorted(_VALID_PROVIDERS))}."
            ),
        )

    if not prompt.strip():
        raise ValidationError(field="prompt", message="El prompt no puede estar vacío.")

    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")

    dispatch = {
        "bedrock-converse": _invoke_bedrock_converse,
        "bedrock-invoke-claude": _invoke_bedrock_claude,
        "bedrock-invoke-openweight": _invoke_bedrock_openweight,
        "openai-compatible": _invoke_openai_compatible,
    }

    return dispatch[provider](
        prompt=prompt,
        schema=schema,
        schema_name=schema_name,
        model_id=model_id,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        region=region,
        base_url=base_url,
    )


# ---------------------------------------------------------------------------
# Bedrock Converse API
# ---------------------------------------------------------------------------


def _invoke_bedrock_converse(
    prompt: str,
    schema: dict[str, Any],
    schema_name: str,
    model_id: str,
    system_prompt: str | None,
    max_tokens: int,
    temperature: float,
    region: str | None,
    base_url: str | None,
) -> dict[str, Any]:
    """Llama a Bedrock Converse API con outputConfig.textFormat (json_schema)."""
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:
        raise NetworkError(
            url="bedrock-converse",
            reason=_BOTO3_MISSING,
        ) from exc

    kwargs: dict[str, Any] = {}
    if region:
        kwargs["region_name"] = region

    try:
        client = boto3.client("bedrock-runtime", **kwargs)

        messages: list[dict[str, Any]] = [{"role": "user", "content": [{"text": prompt}]}]

        request: dict[str, Any] = {
            "modelId": model_id,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
            "outputConfig": {
                "textFormat": {
                    "type": "json_schema",
                    "structure": {
                        "jsonSchema": {
                            "schema": json.dumps(schema),
                            "name": schema_name,
                            "description": f"Structured output schema: {schema_name}",
                        }
                    },
                }
            },
        }

        if system_prompt:
            request["system"] = [{"text": system_prompt}]

        response = client.converse(**request)

        raw_text: str = response["output"]["message"]["content"][0]["text"]
        usage = response.get("usage", {})

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        error_msg = exc.response["Error"]["Message"]
        raise ApiError(
            url="bedrock-converse",
            status_code=int(exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)),
            response_body=f"{error_code}: {error_msg}",
        ) from exc
    except BotoCoreError as exc:
        raise NetworkError(
            url="bedrock-converse",
            reason=str(exc),
        ) from exc

    return _build_result(
        raw_text=raw_text,
        provider="bedrock-converse",
        model_id=model_id,
        input_tokens=usage.get("inputTokens", 0),
        output_tokens=usage.get("outputTokens", 0),
    )


# ---------------------------------------------------------------------------
# Bedrock InvokeModel — Anthropic Claude
# ---------------------------------------------------------------------------


def _invoke_bedrock_claude(
    prompt: str,
    schema: dict[str, Any],
    schema_name: str,
    model_id: str,
    system_prompt: str | None,
    max_tokens: int,
    temperature: float,
    region: str | None,
    base_url: str | None,
) -> dict[str, Any]:
    """Llama a Bedrock InvokeModel con Anthropic Claude (output_config.format)."""
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:
        raise NetworkError(
            url="bedrock-invoke-claude",
            reason=_BOTO3_MISSING,
        ) from exc

    kwargs: dict[str, Any] = {}
    if region:
        kwargs["region_name"] = region

    try:
        client = boto3.client("bedrock-runtime", **kwargs)

        body: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "schema": schema,
                }
            },
        }

        if system_prompt:
            body["system"] = system_prompt

        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType=_APP_JSON,
            accept=_APP_JSON,
        )

        response_body: dict[str, Any] = json.loads(response["body"].read())
        raw_text = response_body["content"][0]["text"]
        usage = response_body.get("usage", {})

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        error_msg = exc.response["Error"]["Message"]
        raise ApiError(
            url="bedrock-invoke-claude",
            status_code=int(exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)),
            response_body=f"{error_code}: {error_msg}",
        ) from exc
    except BotoCoreError as exc:
        raise NetworkError(
            url="bedrock-invoke-claude",
            reason=str(exc),
        ) from exc

    return _build_result(
        raw_text=raw_text,
        provider="bedrock-invoke-claude",
        model_id=model_id,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
    )


# ---------------------------------------------------------------------------
# Bedrock InvokeModel — Open-weight models
# ---------------------------------------------------------------------------


def _invoke_bedrock_openweight(
    prompt: str,
    schema: dict[str, Any],
    schema_name: str,
    model_id: str,
    system_prompt: str | None,
    max_tokens: int,
    temperature: float,
    region: str | None,
    base_url: str | None,
) -> dict[str, Any]:
    """Llama a Bedrock InvokeModel con modelos open-weight (response_format)."""
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:
        raise NetworkError(
            url="bedrock-invoke-openweight",
            reason=_BOTO3_MISSING,
        ) from exc

    kwargs: dict[str, Any] = {}
    if region:
        kwargs["region_name"] = region

    try:
        client = boto3.client("bedrock-runtime", **kwargs)

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body: dict[str, Any] = {
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                },
            },
        }

        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType=_APP_JSON,
            accept=_APP_JSON,
        )

        response_body = json.loads(response["body"].read())
        # Open-weight models return content differently — try common patterns
        if "choices" in response_body:
            raw_text = response_body["choices"][0]["message"]["content"]
        elif "content" in response_body and isinstance(response_body["content"], list):
            raw_text = response_body["content"][0]["text"]
        elif "generation" in response_body:
            raw_text = response_body["generation"]
        else:
            raw_text = json.dumps(response_body)

        usage = response_body.get("usage", {})

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        error_msg = exc.response["Error"]["Message"]
        raise ApiError(
            url="bedrock-invoke-openweight",
            status_code=int(exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)),
            response_body=f"{error_code}: {error_msg}",
        ) from exc
    except BotoCoreError as exc:
        raise NetworkError(
            url="bedrock-invoke-openweight",
            reason=str(exc),
        ) from exc

    return _build_result(
        raw_text=raw_text,
        provider="bedrock-invoke-openweight",
        model_id=model_id,
        input_tokens=usage.get("prompt_tokens", usage.get("input_tokens", 0)),
        output_tokens=usage.get("completion_tokens", usage.get("output_tokens", 0)),
    )


# ---------------------------------------------------------------------------
# OpenAI-compatible endpoint
# ---------------------------------------------------------------------------


def _invoke_openai_compatible(
    prompt: str,
    schema: dict[str, Any],
    schema_name: str,
    model_id: str,
    system_prompt: str | None,
    max_tokens: int,
    temperature: float,
    region: str | None,
    base_url: str | None,
) -> dict[str, Any]:
    """Llama a cualquier endpoint OpenAI-compatible con response_format json_schema."""
    try:
        from openai import OpenAI, OpenAIError
    except ImportError as exc:
        raise NetworkError(
            url="openai-compatible",
            reason="openai no está instalado. Ejecuta: pip install openai",
        ) from exc

    from mcp_structured_output.config import settings

    api_key = settings.openai_api_key or "no-key"
    resolved_base_url = base_url or settings.openai_base_url

    if not resolved_base_url and not settings.openai_api_key:
        raise ValidationError(
            field="base_url",
            message=(
                "Para 'openai-compatible' se requiere base_url o MCP_SO_OPENAI_BASE_URL. "
                "Para OpenAI.com también configura MCP_SO_OPENAI_API_KEY."
            ),
        )

    try:
        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if resolved_base_url:
            client_kwargs["base_url"] = resolved_base_url

        client = OpenAI(**client_kwargs)

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(  # type: ignore[call-overload]
            model=model_id,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                },
            },
            max_tokens=max_tokens,
            temperature=temperature,
        )

        raw_text = response.choices[0].message.content or ""
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0

    except OpenAIError as exc:
        raise ApiError(
            url="openai-compatible",
            status_code=getattr(exc, "status_code", 0) or 0,
            response_body=str(exc),
        ) from exc

    return _build_result(
        raw_text=raw_text,
        provider="openai-compatible",
        model_id=model_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


# ---------------------------------------------------------------------------
# Helper compartido
# ---------------------------------------------------------------------------


def _build_result(
    raw_text: str,
    provider: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int,
) -> dict[str, Any]:
    """Parsea el texto de respuesta como JSON y construye el dict de retorno."""
    try:
        result: Any = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ParseError(
            source=provider,
            reason=f"La respuesta no es JSON válido. Primeros 200 chars: {raw_text[:200]!r}",
        ) from exc

    if not isinstance(result, dict):
        raise ParseError(
            source=provider,
            reason=f"Se esperaba dict, se recibió {type(result).__name__}. Respuesta: {raw_text[:200]!r}",
        )

    return {
        "result": result,
        "provider": provider,
        "model_id": model_id,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
    }
