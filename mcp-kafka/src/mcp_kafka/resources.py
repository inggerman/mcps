"""Resources de solo lectura para mcp-kafka."""

from __future__ import annotations

import json


def kafka_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-kafka",
            "bootstrap_servers": "localhost:9092",
            "security_protocol": "PLAINTEXT",
            "consume_timeout": 5.0,
            "max_consume_messages": 50,
            "admin_timeout": 10.0,
        },
        indent=2,
        ensure_ascii=False,
    )


def kafka_concepts() -> str:
    return (
        "# Conceptos Kafka\n\n"
        "## Topic\n"
        "Categoria/feed donde los mensajes son publicados.\n\n"
        "## Partition\n"
        "Division de un topic para paralelismo. Cada partition es un log ordenado.\n\n"
        "## Offset\n"
        "Identificador secuencial de un mensaje dentro de una partition.\n\n"
        "## Consumer Group\n"
        "Grupo de consumers que comparten la carga de lectura de topics.\n\n"
        "## Broker\n"
        "Nodo del cluster Kafka que almacena datos.\n\n"
        "## Replication Factor\n"
        "Numero de copias de cada partition en diferentes brokers."
    )


def kafka_produce_guide() -> str:
    return (
        "# Guia: produce_message\n\n"
        "## Parametros\n"
        "- `topic` (requerido): Topic destino\n"
        "- `value`: Mensaje (string o dict, dict se serializa a JSON)\n"
        "- `key`: Clave para particionado\n"
        "- `partition`: Partition especifica (opcional)\n"
        "- `headers`: Headers como dict string->string\n\n"
        "## Ejemplo\n"
        "```\n"
        "produce_message(\n"
        "    topic='orders',\n"
        "    value={'order_id': 123, 'total': 99.99},\n"
        "    key='customer-42'\n"
        ")\n"
        "```\n\n"
        "## Notas\n"
        "- acks='all' por defecto (espera todas las replicas)\n"
        "- Si value es dict, se serializa a JSON automaticamente"
    )


def kafka_consume_guide() -> str:
    return (
        "# Guia: consume_messages\n\n"
        "## Parametros\n"
        "- `topic` (requerido): Topic a consumir\n"
        "- `group_id`: Consumer group (default 'mcp-kafka-consumer')\n"
        "- `max_messages`: Maximo de mensajes (default 50)\n"
        "- `from_beginning`: Leer desde el inicio (default false)\n"
        "- `timeout`: Timeout en segundos (default 5)\n"
        "- `parse_json`: Parsear valores como JSON (default true)\n\n"
        "## Ejemplo\n"
        "```\n"
        "consume_messages(\n"
        "    topic='orders',\n"
        "    group_id='order-processor',\n"
        "    max_messages=10,\n"
        "    from_beginning=True\n"
        ")\n"
        "```"
    )


def kafka_topic_management() -> str:
    return (
        "# Gestion de Topics\n\n"
        "## Herramientas disponibles\n"
        "- `topics_list` — listar topics\n"
        "- `topic_describe` — describir un topic\n"
        "- `create_topic` — crear un nuevo topic\n"
        "- `delete_topic` — eliminar un topic\n"
        "- `topic_partitions` — obtener particiones\n"
        "- `topic_config` — obtener/actualizar configuracion\n\n"
        "## Mejores practicas\n"
        "- Usa nombres descriptivos: `orders`, `user-events`\n"
        "- Partition count segun throughput esperado\n"
        "- Replication factor >= 3 para produccion\n"
        "- Usa retencion adecuada (retention.ms)"
    )


def kafka_consumer_groups() -> str:
    return (
        "# Consumer Groups\n\n"
        "## Herramientas disponibles\n"
        "- `consumer_groups_list` — listar grupos\n"
        "- `consumer_group_offsets` — offsets de un grupo\n"
        "- `consumer_group_describe` — describir un grupo\n"
        "- `consumer_group_reset_offsets` — resetear offsets\n"
        "- `consumer_group_delete` — eliminar un grupo\n\n"
        "## Estados de consumer groups\n"
        "| Estado | Descripcion |\n"
        "|--------|-------------|\n"
        "| Stable | Activo y estable |\n"
        "| PreparingRebalance | Rebalanceando |\n"
        "| CompletingRebalance | Completando rebalance |\n"
        "| Empty | Sin miembros activos |\n"
        "| Dead | Grupo eliminado |"
    )


def kafka_security_guide() -> str:
    return (
        "# Seguridad Kafka\n\n"
        "## Protocolos soportados\n"
        "| Protocolo | Descripcion |\n"
        "|-----------|-------------|\n"
        "| PLAINTEXT | Sin encriptacion (desarrollo) |\n"
        "| SSL | TLS encriptacion |\n"
        "| SASL_PLAINTEXT | Autenticacion sin TLS |\n"
        "| SASL_SSL | Autenticacion + TLS (recomendado) |\n\n"
        "## Mecanismos SASL\n"
        "- PLAIN: Usuario/password en texto\n"
        "- SCRAM-SHA-256: Hash SHA-256\n"
        "- SCRAM-SHA-512: Hash SHA-512 (recomendado)\n\n"
        "## Variables de entorno\n"
        "- `MCP_KAFKA_SECURITY_PROTOCOL`\n"
        "- `MCP_KAFKA_SASL_MECHANISM`\n"
        "- `MCP_KAFKA_SASL_USERNAME`\n"
        "- `MCP_KAFKA_SASL_PASSWORD`\n"
        "- `MCP_KAFKA_SSL_CA_LOCATION`"
    )


def kafka_best_practices() -> str:
    return (
        "# Mejores practicas Kafka\n\n"
        "1. **Usa keys** para garantizar orden en particiones\n"
        "2. **Partition count** = throughput / consumer capacity\n"
        "3. **Replication factor** >= 3 en produccion\n"
        "4. **acks=all** para durabilidad maxima\n"
        "5. **Compaction** para topics de estado\n"
        "6. **Retention** adecuada al caso de uso\n"
        "7. **Monitoriza lag** en consumer groups\n"
        "8. **Usa schema registry** para serializacion (Avro/Protobuf)\n"
        "9. **Idempotent producers** para evitar duplicados\n"
        "10. **No uses太多 partitions** (overhead de metadata)"
    )


def kafka_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion (parametros invalidos)"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"common_errors": {
                    "UNKNOWN_TOPIC": "Topic no existe en el cluster",
                    "UNKNOWN_GROUP": "Consumer group no encontrado",
                    "CONNECTION_REFUSED": "No se puede conectar al broker",
                    "SASL_AUTH_FAILED": "Autenticacion SASL fallida",
                    "SSL_HANDSHAKE_FAILED": "Error de handshake SSL",
                    "PRODUCE_TIMEOUT": "Timeout esperando confirmacion de delivery",
                    "CONSUME_TIMEOUT": "Timeout consumiendo mensajes",
                }},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def kafka_troubleshooting() -> str:
    return (
        "# Troubleshooting Kafka\n\n"
        "## No se puede conectar al broker\n"
        "- Verifica `MCP_KAFKA_BOOTSTRAP_SERVERS`\n"
        "- Confirma que el broker este activo\n"
        "- Revisa firewall/security groups\n\n"
        "## Error de autenticacion SASL\n"
        "- Verifica credenciales (username/password)\n"
        "- Confirma el mecanismo SASL correcto\n"
        "- Revisa `MCP_KAFKA_SECURITY_PROTOCOL`\n\n"
        "## Consumer no recibe mensajes\n"
        "- Verifica que el topic tenga mensajes\n"
        "- Revisa el `group_id` y offsets\n"
        "- Prueba `from_beginning=True`\n"
        "- Aumenta el `timeout`\n\n"
        "## Produce falla\n"
        "- Verifica que el topic exista\n"
        "- Revisa permisos ACL\n"
        "- Confirma que hay brokers disponibles"
    )


def kafka_quick_reference() -> str:
    return (
        "# Referencia rapida Kafka MCP\n\n"
        "## Tools disponibles\n"
        "| Tool | Descripcion |\n"
        "|------|-------------|\n"
        "| topics_list | Listar topics |\n"
        "| topic_describe | Describir topic |\n"
        "| consumer_groups_list | Listar consumer groups |\n"
        "| consumer_group_offsets | Offsets de un grupo |\n"
        "| produce_message | Producir mensaje |\n"
        "| consume_messages | Consumir mensajes |\n"
        "| create_topic | Crear topic |\n"
        "| delete_topic | Eliminar topic |\n"
        "| topic_partitions | Particiones de un topic |\n"
        "| topic_config | Config de un topic |\n"
        "| consumer_group_describe | Describir consumer group |\n"
        "| consumer_group_reset_offsets | Resetear offsets |\n"
        "| consumer_group_delete | Eliminar consumer group |\n"
        "| cluster_metadata | Metadata del cluster |\n"
        "| broker_list | Listar brokers |\n"
        "| produce_batch | Producir lote de mensajes |\n"
        "| topic_offsets | Offsets de un topic |\n"
        "| alter_topic_config | Modificar config de topic |\n"
        "| list_acls | Listar ACLs |\n"
        "| describe_cluster | Describir cluster |"
    )


def kafka_performance_tips() -> str:
    return (
        "# Tips de rendimiento Kafka\n\n"
        "## Produccion\n"
        "- Usa **batching** (batch.size, linger.ms)\n"
        "- **Compression** (snappy/lz4/zstd)\n"
        "- **Idempotent producer** para evitar duplicados\n"
        "- Reusa instancias de Producer\n\n"
        "## Consumo\n"
        "- Aumenta **fetch.min.bytes** para batching\n"
        "- Usa **multiple consumers** en el mismo grupo\n"
        "- **Prefetch** con fetch.max.bytes\n"
        "- Monitoriza **consumer lag**\n\n"
        "## Topics\n"
        "- Particiones suficientes para paralelismo\n"
        "- **retention.ms** adecuado al volumen\n"
        "- **segment.bytes** para optimizar storage\n"
        "- **cleanup.policy** = delete o compact"
    )


def kafka_examples() -> str:
    return (
        "# Ejemplos Kafka MCP\n\n"
        "## Ejemplo 1: Listar topics\n"
        "```\n"
        "topics_list(exclude_internal=True)\n"
        "```\n\n"
        "## Ejemplo 2: Producir un evento\n"
        "```\n"
        "produce_message(\n"
        "    topic='user-events',\n"
        "    value={'event': 'login', 'user_id': 42},\n"
        "    key='user-42'\n"
        ")\n"
        "```\n\n"
        "## Ejemplo 3: Consumir ultimos 10 mensajes\n"
        "```\n"
        "consume_messages(\n"
        "    topic='user-events',\n"
        "    max_messages=10,\n"
        "    timeout=10\n"
        ")\n"
        "```\n\n"
        "## Ejemplo 4: Ver offsets de un grupo\n"
        "```\n"
        "consumer_group_offsets(group_id='event-processor')\n"
        "```"
    )


def kafka_broker_management() -> str:
    return (
        "# Gestion de Brokers\n\n"
        "## Herramientas disponibles\n"
        "- `broker_list` — listar brokers del cluster\n"
        "- `cluster_metadata` — metadata completa del cluster\n\n"
        "## Informacion de brokers\n"
        "Cada broker retorna:\n"
        "- `id`: ID del broker\n"
        "- `host`: Hostname o IP\n"
        "- `port`: Puerto\n\n"
        "## Consideraciones\n"
        "- El controller es el broker responsable de asignar leaders\n"
        "- Minimo 3 brokers para produccion (quorum)\n"
        "- Monitoriza disk usage y network throughput\n"
        "- Usa JMX metrics para observabilidad"
    )


def kafka_partitioning_guide() -> str:
    return (
        "# Guia de Particionado\n\n"
        "## Cuantas particiones?\n"
        "- **Throughput target**: partitions = target_throughput / per_partition_throughput\n"
        "- **Consumer parallelism**: 1 partition = 1 consumer max por grupo\n"
        "- **Minimo**: 1 para topics de baja frecuencia\n"
        "- **Tipico**: 3-6 para mayoria de casos\n"
        "- **Alto**: 10-50 para high-throughput\n\n"
        "## Estrategias de key\n"
        "- **Sin key**: Round-robin entre particiones\n"
        "- **Entity ID**: Mismo entity va a misma particion (orden)\n"
        "- **Composite key**: Para control fino\n\n"
        "## Replication factor\n"
        "- RF=1: Solo desarrollo\n"
        "- RF=2: No recomendado (sin quorum)\n"
        "- RF=3: Produccion estandar\n"
        "- RF=5: Alta disponibilidad\n\n"
        "## Rebalanceo\n"
        "- Al anadir/borrar consumers en un grupo\n"
        "- Al anadir particiones (no se reordena)\n"
        "- Usa `consumer_group_describe` para ver asignaciones"
    )
