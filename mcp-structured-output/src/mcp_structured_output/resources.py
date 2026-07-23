"""Resources de solo lectura para mcp-structured-output.

Expone metadatos, guias y consejos sobre JSON Schema y structured output
como URIs accesibles para el modelo a traves de `@mcp.resource`.
"""

from __future__ import annotations

import json

from mcp_structured_output.config import settings


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


def structured_output_configuration() -> str:
    """Configuracion actual del servidor structured-output."""
    return json.dumps(
        {
            "default_provider": settings.default_provider,
            "default_model_id": settings.default_model_id,
            "default_max_tokens": settings.default_max_tokens,
            "default_temperature": settings.default_temperature,
            "aws_region": settings.aws_region,
            "openai_base_url": settings.openai_base_url,
        },
        indent=2,
        ensure_ascii=False,
    )


def supported_providers() -> str:
    """Proveedores soportados para structured output."""
    return (
        "# Proveedores soportados\n\n"
        "- **bedrock-converse**: Bedrock Converse API (outputConfig.textFormat)\n"
        "- **bedrock-invoke-claude**: Bedrock InvokeModel con Anthropic Claude\n"
        "- **bedrock-invoke-openweight**: Bedrock InvokeModel con modelos open-weight\n"
        "- **openai-compatible**: Cualquier endpoint OpenAI-compatible\n"
        "\n"
        "Credenciales AWS via entorno/perfil boto3.\n"
        "Para openai-compatible configura MCP_SO_OPENAI_BASE_URL y MCP_SO_OPENAI_API_KEY."
    )


def json_schema_basics() -> str:
    """Conceptos basicos de JSON Schema."""
    return (
        "# JSON Schema — Conceptos basicos\n\n"
        "- **type**: Tipo de dato (object, array, string, integer, number, boolean, null)\n"
        "- **properties**: Campos de un objeto\n"
        "- **required**: Lista de campos obligatorios\n"
        "- **additionalProperties**: false para prohibir campos extra\n"
        "- **items**: Schema para elementos de un array\n"
        "- **enum**: Lista de valores permitidos\n"
        "- **$ref**: Referencia interna (#/...) o externa\n"
        "- **$defs / definitions**: Definiciones reutilizables\n"
        "- **anyOf / allOf / oneOf**: Combinacion de schemas\n"
        "- **description**: Descripcion del schema o campo"
    )


def bedrock_compatibility_guide() -> str:
    """Guia de compatibilidad con Bedrock structured output."""
    return (
        "# Compatibilidad con Bedrock Structured Output\n\n"
        "Bedrock soporta JSON Schema Draft 2020-12 con limitaciones:\n\n"
        "## No soportado\n"
        "- minimum, maximum, exclusiveMinimum, exclusiveMaximum, multipleOf\n"
        "- minLength, maxLength\n"
        "- additionalProperties != false\n"
        "- $ref externos (solo internos #/...)\n"
        "- minItems > 1\n"
        "- enum con valores complejos (dict, list)\n"
        "- Schemas recursivos\n\n"
        "## Requerido\n"
        "- additionalProperties: false en todos los objetos\n"
        "\n"
        "Usa validate_schema() para verificar compatibilidad.\n"
        "Usa sanitize_schema() para transformar automaticamente."
    )


def schema_validation_tips() -> str:
    """Consejos de validacion de schemas."""
    return (
        "# Validacion de schemas\n\n"
        "- validate_schema() detecta problemas de compatibilidad con Bedrock.\n"
        "- Retorna valid=True si no hay errores (warnings son aceptables).\n"
        "- Cada issue tiene: path, message, severity (error|warning).\n"
        "- Errores bloquean el uso del schema con Bedrock.\n"
        "- Warnings son recomendaciones (ej: falta additionalProperties).\n"
        "- Usa sanitize_schema() para corregir automaticamente."
    )


def schema_generation_tips() -> str:
    """Consejos de generacion de schemas."""
    return (
        "# Generacion de schemas\n\n"
        "- generate_schema() crea un schema desde un objeto JSON de ejemplo.\n"
        "- Infiere tipos automaticamente (string, integer, boolean, etc.).\n"
        "- strict=True marca todos los campos como required.\n"
        "- strict=True agrega additionalProperties: false en objetos.\n"
        "- Campos null se infieren como string|null (tipo real desconocido).\n"
        "- Arrays vacios se asumen como items de tipo string.\n"
        "- Retorna warnings sobre campos ambiguos."
    )


def schema_sanitization_tips() -> str:
    """Consejos de saneamiento de schemas."""
    return (
        "# Saneamiento de schemas\n\n"
        "- sanitize_schema() transforma un schema para que sea compatible con Bedrock.\n"
        "- Remueve constraints numericas y de string.\n"
        "- Fuerza additionalProperties: false en objetos.\n"
        "- Reemplaza $ref externos por {type: string}.\n"
        "- Ajusta minItems > 1 a 1.\n"
        "- Remueve valores complejos de enum.\n"
        "- El schema original NO se modifica (usa deep copy).\n"
        "- Retorna lista de changes con path, action, reason."
    )


def common_structured_output_workflows() -> str:
    """Flujos de trabajo comunes con structured output."""
    return (
        "# Flujos comunes\n\n"
        "- **Validar**: validate_schema(schema)\n"
        "- **Generar**: generate_schema({'name': 'test', 'age': 25})\n"
        "- **Sanear**: sanitize_schema(schema)\n"
        "- **Invocar**: invoke_structured(prompt, schema, provider='bedrock-converse')\n"
        "\n"
        "Flujo tipico:\n"
        "1. Genera o escribe un schema\n"
        "2. Validalo con validate_schema()\n"
        "3. Si hay errores, sanearlo con sanitize_schema()\n"
        "4. Invoca el LLM con invoke_structured()"
    )


def structured_output_error_codes() -> str:
    """Codigos de error comunes del servidor structured-output."""
    return json.dumps(
        {
            "errors": [
                {"code": "VALIDATION_ERROR", "description": "Parametros invalidos o provider no soportado"},
                {"code": "API_ERROR", "description": "Error de la API del proveedor (Bedrock/OpenAI)"},
                {"code": "NETWORK_ERROR", "description": "Error de red o dependencia faltante (boto3/openai)"},
                {"code": "PARSE_ERROR", "description": "La respuesta del LLM no es JSON valido"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def json_schema_types_reference() -> str:
    """Referencia de tipos JSON Schema."""
    return (
        "# Tipos JSON Schema\n\n"
        "| Tipo | Descripcion | Ejemplo |\n"
        "|------|-------------|---------|\n"
        "| object | Objeto clave-valor | {\"name\": \"test\"} |\n"
        "| array | Lista de elementos | [1, 2, 3] |\n"
        "| string | Cadena de texto | \"hello\" |\n"
        "| integer | Numero entero | 42 |\n"
        "| number | Numero decimal | 3.14 |\n"
        "| boolean | Verdadero/falso | true |\n"
        "| null | Valor nulo | null |"
    )


def bedrock_models_reference() -> str:
    """Modelos de Bedrock soportados."""
    return (
        "# Modelos Bedrock comunes\n\n"
        "## Amazon Nova\n"
        "- amazon.nova-pro-v1:0\n"
        "- amazon.nova-lite-v1:0\n"
        "- amazon.nova-micro-v1:0\n\n"
        "## Anthropic Claude\n"
        "- anthropic.claude-3-5-sonnet-20241022-v2:0\n"
        "- anthropic.claude-3-5-haiku-20241022-v1:0\n"
        "- anthropic.claude-3-opus-20240229-v1:0\n\n"
        "## Meta Llama\n"
        "- meta.llama3-1-70b-instruct-v1:0\n"
        "- meta.llama3-1-8b-instruct-v1:0\n\n"
        "## Mistral\n"
        "- mistral.mistral-7b-instruct-v0:2\n"
        "- mistral.mixtral-8x7b-instruct-v0:1"
    )


def openai_compatible_guide() -> str:
    """Guia de endpoints OpenAI-compatible."""
    return (
        "# Endpoints OpenAI-compatible\n\n"
        "- Cualquier API que implemente el formato OpenAI Chat Completions.\n"
        "- Configura MCP_SO_OPENAI_BASE_URL con la URL base.\n"
        "- Configura MCP_SO_OPENAI_API_KEY con la API key.\n"
        "- Usa provider='openai-compatible' en invoke_structured().\n"
        "- El parametro base_url sobrescribe la configuracion global.\n"
        "\n"
        "Ejemplos compatibles: vLLM, Ollama, LM Studio, Together AI, etc."
    )


def schema_keywords_reference() -> str:
    """Referencia de keywords de JSON Schema."""
    return (
        "# Keywords JSON Schema\n\n"
        "## Objeto\n"
        "- type, properties, required, additionalProperties\n"
        "- patternProperties, minProperties, maxProperties\n\n"
        "## Array\n"
        "- items, prefixItems, minItems, maxItems, uniqueItems\n\n"
        "## String\n"
        "- minLength, maxLength, pattern, format\n\n"
        "## Numero\n"
        "- minimum, maximum, exclusiveMinimum, exclusiveMaximum, multipleOf\n\n"
        "## Combinacion\n"
        "- allOf, anyOf, oneOf, not\n\n"
        "## Reutilizacion\n"
        "- $ref, $defs, definitions\n\n"
        "## Metadata\n"
        "- title, description, default, examples, enum, const"
    )


def example_generate_schema() -> str:
    """Ejemplo de generacion de schema."""
    return (
        "# Ejemplo: generate_schema\n\n"
        "```\n"
        "generate_schema(\n"
        "    example={'name': 'Juan', 'age': 30, 'active': True},\n"
        "    name='user_schema',\n"
        "    strict=True\n"
        ")\n"
        "```\n"
        "Retorna: schema (dict), field_count (int), warnings (list)"
    )


def example_invoke_structured() -> str:
    """Ejemplo de invocacion estructurada."""
    return (
        "# Ejemplo: invoke_structured\n\n"
        "```\n"
        "invoke_structured(\n"
        "    prompt='Extrae los datos del usuario',\n"
        "    schema={'type': 'object', 'properties': {...}},\n"
        "    provider='bedrock-converse',\n"
        "    model_id='amazon.nova-pro-v1:0'\n"
        ")\n"
        "```\n"
        "Retorna: result (dict), provider (str), model_id (str), usage (dict)"
    )
