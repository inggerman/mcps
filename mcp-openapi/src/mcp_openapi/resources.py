"""Resources de solo lectura para mcp-openapi."""

from __future__ import annotations

import json


def openapi_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-openapi",
            "version": "1.0.0",
            "spec": "./openapi.yaml",
            "allow_invoke": False,
        },
        indent=2,
        ensure_ascii=False,
    )


def openapi_spec_basics() -> str:
    return (
        "# OpenAPI Specification Basics\n\n"
        "## Versiones\n"
        "- OpenAPI 3.1.0 (latest)\n"
        "- OpenAPI 3.0.x\n"
        "- Swagger 2.0 (legacy)\n\n"
        "## Estructura\n"
        "- openapi: version\n"
        "- info: title, version, description\n"
        "- servers: URLs base\n"
        "- paths: endpoints y operaciones\n"
        "- components: schemas, securitySchemes\n"
        "- tags: agrupacion de operaciones\n"
        "- security: seguridad global\n\n"
        "## Path Items\n"
        "- get, post, put, patch, delete, options, head\n"
        "- parameters: path, query, header, cookie\n"
        "- requestBody: body de la peticion\n"
        "- responses: codigos de respuesta\n"
        "- operationId: identificador unico"
    )


def openapi_best_practices() -> str:
    return (
        "# OpenAPI Best Practices\n\n"
        "## Diseno\n"
        "- Usar operationId descriptivo y unico\n"
        "- Incluir summary y description en cada operacion\n"
        "- Usar tags para agrupar operaciones\n"
        "- Definir examples en responses\n\n"
        "## Versionado\n"
        "- Versionar la API en la URL o header\n"
        "- Mantener compatibilidad hacia atras\n"
        "- Documentar cambios entre versiones\n\n"
        "## Seguridad\n"
        "- Definir securitySchemes\n"
        "- Usar OAuth2 o API Key\n"
        "- No exponer secrets en el spec\n"
        "- Validar scopes por operacion\n\n"
        "## Schemas\n"
        "- Reutilizar schemas con $ref\n"
        "- Definir required fields\n"
        "- Usar format (date-time, email, uuid)\n"
        "- Incluir examples en schemas"
    )


def openapi_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- openapi_list_operations()\n"
        "- openapi_describe_operation(operation_id)\n"
        "- openapi_invoke(operation_id, ...)\n"
        "- openapi_get_spec_info()\n"
        "- openapi_list_endpoints()\n"
        "- openapi_get_schemas()\n"
        "- openapi_validate_spec()\n"
        "- openapi_generate_client_code(language)\n\n"
        "## Variables .env\n"
        "- OPENAPI_SPEC\n"
        "- OPENAPI_ALLOWED_ROOT\n"
        "- OPENAPI_ALLOW_INVOKE\n"
        "- OPENAPI_ALLOWED_HOSTS"
    )


def openapi_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "ValidationError: campo invalido"},
                {"code": -32002, "description": "Spec no encontrado o invalido"},
                {"code": -32003, "description": "Host no permitido"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def openapi_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## Spec no carga\n"
        "- Verificar OPENAPI_SPEC path\n"
        "- Verificar OPENAPI_ALLOWED_ROOT\n"
        "- El archivo debe ser YAML o JSON valido\n\n"
        "## No se puede invocar\n"
        "- Verificar OPENAPI_ALLOW_INVOKE=true\n"
        "- Verificar OPENAPI_ALLOWED_HOSTS\n"
        "- El host debe estar en la lista\n\n"
        "## Spec invalido\n"
        "- Debe tener campo 'openapi' o 'swagger'\n"
        "- Debe tener seccion 'info'\n"
        "- Debe tener seccion 'paths'\n\n"
        "## Operacion no encontrada\n"
        "- Verificar operationId exacto\n"
        "- Usar openapi_list_operations para ver disponibles"
    )


def openapi_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Listar operaciones\n"
        "openapi_list_operations()\n\n"
        "## Describir operacion\n"
        'openapi_describe_operation(operation_id="getUser")\n\n'
        "## Invocar operacion\n"
        'openapi_invoke(operation_id="getUser", path_parameters={"id": "123"})\n\n'
        "## Generar cliente Python\n"
        'openapi_generate_client_code(language="python")\n\n'
        "## Validar spec\n"
        "openapi_validate_spec()"
    )


def openapi_security() -> str:
    return (
        "# OpenAPI Security\n\n"
        "## Tipos de autenticacion\n"
        "- apiKey: header, query, o cookie\n"
        "- http: Basic, Bearer\n"
        "- oauth2: flows (implicit, password, clientCredentials, authorizationCode)\n"
        "- openIdConnect: OpenID Connect\n"
        "- mutualTLS: certificados mutuos\n\n"
        "## Configuracion\n"
        "```yaml\n"
        "components:\n"
        "  securitySchemes:\n"
        "    BearerAuth:\n"
        "      type: http\n"
        "      scheme: bearer\n"
        "      bearerFormat: JWT\n"
        "security:\n"
        "  - BearerAuth: []\n"
        "```\n\n"
        "## Mejores practicas\n"
        "- Usar HTTPS siempre\n"
        "- Definir scopes por operacion\n"
        "- Documentar como obtener tokens\n"
        "- Incluir ejemplos de autenticacion"
    )


def openapi_versioning() -> str:
    return (
        "# API Versioning\n\n"
        "## Estrategias\n"
        "- URL versioning: /v1/users\n"
        "- Header versioning: Accept-Version: v1\n"
        "- Query versioning: ?version=v1\n"
        "- Content negotiation: Accept: application/vnd.api.v1+json\n\n"
        "## OpenAPI\n"
        "- Version en info.version (semver)\n"
        "- Multiple specs por version mayor\n"
        "- Documentar breaking changes\n"
        "- Mantener changelog\n\n"
        "## Compatibilidad\n"
        "- Backward compatible: nuevo endpoint, nuevo campo opcional\n"
        "- Breaking change: eliminar endpoint, cambiar tipo, hacer campo required\n"
        "- Deprecar antes de eliminar\n"
        "- Notificar con header Sunset"
    )


def openapi_code_generation() -> str:
    return (
        "# Code Generation\n\n"
        "## Tools\n"
        "- openapi-generator: multi-lenguaje\n"
        "- swagger-codegen: legacy\n"
        "- fastapi: Python server generation\n"
        "- autorest: Microsoft\n\n"
        "## Lenguajes soportados\n"
        "- Python: httpx, requests\n"
        "- JavaScript/TypeScript: axios, fetch\n"
        "- Java: OkHttp, Retrofit\n"
        "- Go: net/http\n"
        "- C#: HttpClient\n\n"
        "## Configuracion\n"
        "- Generar en CI/CD\n"
        "- Commit generated code\n"
        "- Usar templates personalizados\n"
        "- Configurar naming conventions\n"
        "- Excluir operaciones internas"
    )


def openapi_testing() -> str:
    return (
        "# API Testing\n\n"
        "## Tipos de tests\n"
        "- Contract testing: validar spec vs implementacion\n"
        "- Functional testing: invocar operaciones\n"
        "- Load testing: rendimiento\n"
        "- Security testing: auth, authz\n\n"
        "## Tools\n"
        "- Dredd: contract testing\n"
        "- Schemathesis: property-based testing\n"
        "- Postman: manual y automated\n"
        "- pytest + httpx: Python integration\n\n"
        "## Mejores practicas\n"
        "- Test contra spec, no contra implementacion\n"
        "- Validar todos los codigos de respuesta\n"
        "- Test edge cases (empty, null, max)\n"
        "- Mock responses para desarrollo\n"
        "- CI/CD integration"
    )


def openapi_documentation() -> str:
    return (
        "# API Documentation\n\n"
        "## Tools\n"
        "- Swagger UI: interactivo\n"
        "- Redoc: clean documentation\n"
        "- Stoplight: design + docs\n"
        "- Elements: embeddable docs\n\n"
        "## Mejores practicas\n"
        "- Incluir examples en cada operacion\n"
        "- Documentar codigos de error\n"
        "- Usar tags para organizar\n"
        "- Incluir descripcion de schemas\n"
        "- Documentar autenticacion\n"
        "- Proveer quickstart guide\n"
        "- Mantener docs actualizadas con el spec\n\n"
        "## Estructura recomendada\n"
        "1. Introduccion y autenticacion\n"
        "2. Quickstart\n"
        "3. Endpoints por tag\n"
        "4. Schemas\n"
        "5. Errores comunes\n"
        "6. Changelog"
    )


def openapi_migration() -> str:
    return (
        "# OpenAPI Migration\n\n"
        "## Swagger 2.0 -> OpenAPI 3.0\n"
        "- definitions -> components/schemas\n"
        "- securityDefinitions -> components/securitySchemes\n"
        "- responses -> responses con content\n"
        "- Consumes/Produces -> content media types\n"
        "- host/basePath -> servers\n\n"
        "## OpenAPI 3.0 -> 3.1\n"
        "- JSON Schema 2020-12\n"
        "- nullable -> type: [string, null]\n"
        "- exclusiveMinimum/Maximum: numericos\n"
        "- webhooks support\n"
        "- info.summary\n\n"
        "## Tools\n"
        "- oas-normalizer: normalizar specs\n"
        "- openapi-format: formatear y filtrar\n"
        "- swagger-converter: 2.0 -> 3.0\n"
        "- Migrar gradualmente con compatibilidad"
    )


def openapi_server_mocking() -> str:
    return (
        "# Server Mocking\n\n"
        "## Tools\n"
        "- Prism: mock server from spec\n"
        "- WireMock: flexible mocking\n"
        "- Mockoon: desktop mocking\n"
        "- Stoplight Prism: validation + mocking\n\n"
        "## Beneficios\n"
        "- Desarrollo frontend sin backend\n"
        "- Tests aislados\n"
        "- Demo sin infraestructura\n"
        "- Validacion de spec\n\n"
        "## Configuracion\n"
        "- Generar respuestas desde examples\n"
        "- Usar status codes del spec\n"
        "- Validar requests contra spec\n"
        "- Soportar dynamic mocking\n"
        "- Configurar delays para testing"
    )


def openapi_webhooks() -> str:
    return (
        "# OpenAPI Webhooks\n\n"
        "## OpenAPI 3.1+\n"
        "```yaml\n"
        "webhooks:\n"
        "  newOrder:\n"
        "    post:\n"
        "      operationId: newOrderWebhook\n"
        "      requestBody:\n"
        "        content:\n"
        "          application/json:\n"
        "            schema:\n"
        "              $ref: '#/components/schemas/Order'\n"
        "      responses:\n"
        "        '200':\n"
        "          description: Acknowledged\n"
        "```\n\n"
        "## Conceptos\n"
        "- Webhooks: server-to-server callbacks\n"
        "- El cliente registra una URL\n"
        "- El server envia eventos a la URL\n"
        "- Usar HMAC para verificar autenticidad\n"
        "- Retry con exponential backoff\n\n"
        "## Mejores practicas\n"
        "- Documentar eventos disponibles\n"
        "- Incluir examples de payloads\n"
        "- Documentar codigos de respuesta esperados\n"
        "- Usar signing secrets"
    )
