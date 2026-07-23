"""Resources de solo lectura para mcp-event-driven."""

from __future__ import annotations

import json


def event_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-event-driven",
            "version": "1.0.0",
            "schemas_path": "./schemas",
        },
        indent=2,
        ensure_ascii=False,
    )


def event_json_schema_guide() -> str:
    return (
        "# Guia JSON Schema\n\n"
        "## Conceptos\n"
        "- Schema: describe estructura de datos JSON\n"
        "- Type: object, string, number, array, boolean, null\n"
        "- Properties: campos del objeto\n"
        "- Required: campos obligatorios\n\n"
        "## Ejemplo\n"
        '{\n  "type": "object",\n  "properties": {\n    "id": {"type": "string"}\n  },\n  "required": ["id"]\n}\n\n'
        "## Keywords utiles\n"
        "- $ref: referenciar otro schema\n"
        "- allOf, anyOf, oneOf: composicion\n"
        "- enum: valores fijos\n"
        "- pattern: regex\n"
        "- minimum/maximum: rangos"
    )


def event_asyncapi_guide() -> str:
    return (
        "# Guia AsyncAPI\n\n"
        "## Conceptos\n"
        "- Estándar para APIs asincronas\n"
        "- Similar a OpenAPI pero para eventos\n"
        "- Version: 2.0.0 o 3.0.0\n\n"
        "## Estructura\n"
        "- asyncapi: version\n"
        "- info: metadata (title, version)\n"
        "- channels: topicos/colas\n"
        "- components: schemas reutilizables\n\n"
        "## Ejemplo\n"
        '{\n  "asyncapi": "2.0.0",\n  "info": {"title": "Orders"},\n  "channels": {\n    "order/created": {\n      "subscribe": {...}\n    }\n  }\n}\n\n'
        "## Tools\n"
        "- event_parse_schema(filename)\n"
        "- event_analyze_choreography()"
    )


def event_choreography_guide() -> str:
    return (
        "# Coreografia (Choreography)\n\n"
        "## Concepto\n"
        "- Cada servicio reacciona a eventos sin orquestador central\n"
        "- Desacoplamiento total entre servicios\n"
        "- Escalabilidad natural\n\n"
        "## Patrones\n"
        "- Event Notification: notificar que algo paso\n"
        "- Event-Carried State Transfer: evento lleva datos completos\n"
        "- Event Sourcing: almacenar todos los eventos como fuente de verdad\n\n"
        "## Ventajas\n"
        "- Sin punto unico de fallo\n"
        "- Servicios independientes\n"
        "- Facil agregar nuevos consumidores\n\n"
        "## Desventajas\n"
        "- Dificil rastrear flujo completo\n"
        "- Posibles bucles de eventos\n"
        "- Consistencia eventual"
    )


def event_orchestration_guide() -> str:
    return (
        "# Orquestacion (Orchestration)\n\n"
        "## Concepto\n"
        "- Un orquestador central coordina los servicios\n"
        "- Flujo explicito y controlable\n"
        "- Saga pattern para transacciones distribuidas\n\n"
        "## Patrones\n"
        "- Saga: secuencia de transacciones locales\n"
        "- Compensating Transaction: deshacer en caso de fallo\n"
        "- Process Manager: coordenador con estado\n\n"
        "## Ventajas\n"
        "- Flujo visible y rastreable\n"
        "- Manejo de errores explicito\n"
        "- Estado centralizado\n\n"
        "## Desventajas\n"
        "- Orquestador como punto unico de fallo\n"
        "- Mayor acoplamiento\n"
        "- Complejidad en el orquestador"
    )


def event_sourcing_guide() -> str:
    return (
        "# Event Sourcing\n\n"
        "## Concepto\n"
        "- Almacenar eventos como fuente de verdad\n"
        "- Estado derivado de replay de eventos\n"
        "- Inmutable: eventos nunca se borran\n\n"
        "## Estructura\n"
        "- Event Store: almacen de eventos\n"
        "- Projections: vistas derivadas\n"
        "- Snapshots: optimizacion para replay largo\n\n"
        "## Ventajas\n"
        "- Audit trail completo\n"
        "- Time travel: estado en cualquier momento\n"
        "- Replay para debugging\n"
        "- Desacoplamiento natural\n\n"
        "## Desventajas\n"
        "- Complejidad de implementacion\n"
        "- Eventos inmutables requieren compensacion\n"
        "- Latencia en projections"
    )


def event_cqrs_guide() -> str:
    return (
        "# CQRS (Command Query Responsibility Segregation)\n\n"
        "## Concepto\n"
        "- Separar lectura (Query) de escritura (Command)\n"
        "- Modelos distintos para cada operacion\n"
        "- Combinable con Event Sourcing\n\n"
        "## Estructura\n"
        "- Command Side: valida y ejecuta comandos, emite eventos\n"
        "- Query Side: projections optimizadas para lectura\n"
        "- Sync: eventos mantienen query side actualizada\n\n"
        "## Ventajas\n"
        "- Lecturas optimizadas independientemente\n"
        "- Escalabilidad independiente\n"
        "- Modelos especializados\n\n"
        "## Desventajas\n"
        "- Complejidad arquitectonica\n"
        "- Consistencia eventual entre modelos\n"
        "- Infraestructura adicional"
    )


def event_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- event_parse_schema(filename)\n"
        "- event_analyze_choreography()\n"
        "- event_generate_mock_payload(properties)\n"
        "- event_validate_payload(schema_file, payload)\n"
        "- event_list_schemas()\n"
        "- event_create_schema(name, properties)\n"
        "- event_trace_flow(event_name)\n\n"
        "## Variables .env\n"
        "- EVENT_SCHEMAS_PATH"
    )


def event_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor de eventos"},
                {"code": -32001, "description": "FileNotFoundError: archivo no encontrado"},
                {"code": -32002, "description": "ParseError: error de parseo JSON"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def event_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## Schema no encontrado\n"
        "- Verificar EVENT_SCHEMAS_PATH\n"
        "- Usar nombre relativo al directorio de schemas\n\n"
        "## Error de parseo\n"
        "- Verificar que el archivo es JSON valido\n"
        "- Revisar sintaxis del schema\n\n"
        "## No se encuentran eventos\n"
        "- Verificar que hay archivos .json en schemas_path\n"
        "- Usar event_analyze_choreography() para escanear\n\n"
        "## Payload invalido\n"
        "- Usar event_validate_payload para verificar\n"
        "- Comparar propiedades con el schema"
    )


def event_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Ejemplo 1: Parsear schema\n"
        'event_parse_schema(filename="user_created.json")\n\n'
        "## Ejemplo 2: Analizar coreografia\n"
        "event_analyze_choreography()\n\n"
        "## Ejemplo 3: Generar payload mock\n"
        'event_generate_mock_payload(properties=["user_id", "created_at"])\n\n'
        "## Ejemplo 4: Listar schemas\n"
        "event_list_schemas()"
    )


def event_message_patterns() -> str:
    return (
        "# Patrones de mensajeria\n\n"
        "## Pub/Sub\n"
        "- Publicador no conoce suscriptores\n"
        "- Desacoplamiento total\n"
        "- Ej: Kafka, RabbitMQ topic exchanges\n\n"
        "## Point-to-Point\n"
        "- Un productor, un consumidor\n"
        "- Cola de trabajo\n"
        "- Ej: RabbitMQ queue, SQS\n\n"
        "## Request/Reply\n"
        "- Mensaje con correlation ID\n"
        "- Respuesta asincrona\n"
        "- Ej: RPC sobre message broker\n\n"
        "## Competing Consumers\n"
        "- Multiples consumidores de una cola\n"
        "- Balanceo de carga\n"
        "- Procesamiento paralelo"
    )


def event_dead_letter_queue() -> str:
    return (
        "# Dead Letter Queue (DLQ)\n\n"
        "## Concepto\n"
        "- Cola para mensajes que fallaron\n"
        "- Permite reintentos posteriores\n"
        "- Evita perder eventos\n\n"
        "## Configuracion\n"
        "- Max reintentos: 3 (tipico)\n"
        "- Backoff exponencial entre reintentos\n"
        "- DLQ separada del topico principal\n\n"
        "## Procesamiento\n"
        "- Analizar causa del fallo\n"
        "- Corregir y reenviar\n"
        "- Descartar si es irreparable\n\n"
        "## Monitoring\n"
        "- Alertar si DLQ crece\n"
        "- Tasa de fallos por servicio\n"
        "- Tiempo en DLQ"
    )


def event_idempotency() -> str:
    return (
        "# Idempotencia en eventos\n\n"
        "## Concepto\n"
        "- Procesar el mismo evento multiples veces = mismo resultado\n"
        "- Esencial en sistemas distribuidos\n"
        "- Evita efectos duplicados\n\n"
        "## Estrategias\n"
        "- Event ID: usar ID unico para deduplicar\n"
        "- Idempotency Key: clave proporcionada por cliente\n"
        "- State Machine: verificar estado antes de actuar\n\n"
        "## Implementacion\n"
        "- Tabla de eventos procesados\n"
        "- TTL en cache de deduplicacion\n"
        "- Versiones optimistas (optimistic locking)\n\n"
        "## Ejemplo\n"
        '- event_id: \"evt_123\"\n'
        '- Verificar si evt_123 ya fue procesado\n'
        '- Si si, retornar resultado cacheado\n'
        "- Si no, procesar y guardar resultado\n"
    )


def event_best_practices() -> str:
    return (
        "# Mejores practicas event-driven\n\n"
        "1. Eventos inmutables y con timestamp\n"
        "2. Nombres descriptivos: past tense (UserCreated)\n"
        "3. Schema versionado (backward compatible)\n"
        "4. Idempotencia en todos los consumidores\n"
        "5. DLQ para manejo de fallos\n"
        "6. Monitoring de latencia y throughput\n"
        "7. Eventos pequenos y especificos\n"
        "8. No incluir logica de negocio en eventos\n"
        "9. Documentar contratos con AsyncAPI\n"
        "10. Testear consumidores independientemente"
    )
