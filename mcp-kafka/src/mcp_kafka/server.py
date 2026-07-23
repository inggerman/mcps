"""Servidor FastMCP para mcp-kafka."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_kafka.config import settings
from mcp_kafka.tools import (
    alter_topic_config,
    broker_list,
    list_acls,
    cluster_metadata,
    consume_messages,
    consumer_group_delete,
    consumer_group_describe,
    consumer_group_offsets,
    consumer_group_reset_offsets,
    consumer_groups_list,
    create_topic,
    delete_topic,
    produce_batch,
    produce_message,
    topic_describe,
    topic_offsets,
    topic_partitions,
    topics_list,
)
from mcp_kafka import resources as res

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-kafka",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-kafka")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()


mcp = FastMCP(
    name="mcp-kafka",
    instructions=(
        "Servidor MCP para Apache Kafka. "
        "Herramientas: topics_list, topic_describe, consumer_groups_list, "
        "consumer_group_offsets, produce_message, consume_messages. "
        "Configura el broker con MCP_KAFKA_BOOTSTRAP_SERVERS. "
        "Soporta SASL/SSL para clusters seguros (MSK, Confluent Cloud, etc.)."
    ),
    lifespan=lifespan,
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__, exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="topics_list",
    description=(
        "Lista todos los topics del cluster Kafka. "
        "Parámetros: prefix (string opcional, filtrar por prefijo), "
        "exclude_internal (bool, default true, excluye topics __). "
        "Retorna: topics[], count, cluster_id, broker_count."
    ),
)
def tool_topics_list(
    prefix: str | None = None,
    exclude_internal: bool = True,
) -> dict[str, Any]:
    logger.info("topics_list llamado", prefix=prefix)
    result = _handle(topics_list, prefix=prefix, exclude_internal=exclude_internal)
    logger.info("topics_list completado", count=result["count"])
    return result


@mcp.tool(
    name="topic_describe",
    description=(
        "Describe un topic Kafka: particiones, líder, réplicas e ISR. "
        "Parámetros: topic (requerido). "
        "Retorna: topic, partition_count, replication_factor, partitions[]."
    ),
)
def tool_topic_describe(topic: str) -> dict[str, Any]:
    logger.info("topic_describe llamado", topic=topic)
    result = _handle(topic_describe, topic=topic)
    logger.info("topic_describe completado", topic=topic, partitions=result["partition_count"])
    return result


@mcp.tool(
    name="consumer_groups_list",
    description=(
        "Lista todos los consumer groups del cluster Kafka. "
        "Parámetros: prefix (string opcional, filtrar por prefijo). "
        "Retorna: groups[], count, errors[]."
    ),
)
def tool_consumer_groups_list(prefix: str | None = None) -> dict[str, Any]:
    logger.info("consumer_groups_list llamado", prefix=prefix)
    result = _handle(consumer_groups_list, prefix=prefix)
    logger.info("consumer_groups_list completado", count=result["count"])
    return result


@mcp.tool(
    name="consumer_group_offsets",
    description=(
        "Obtiene los offsets actuales de un consumer group. "
        "Parámetros: group_id (requerido), topics (list de strings opcional). "
        "Retorna: group_id, offsets[] (topic, partition, offset), partition_count."
    ),
)
def tool_consumer_group_offsets(
    group_id: str,
    topics: list[str] | None = None,
) -> dict[str, Any]:
    logger.info("consumer_group_offsets llamado", group_id=group_id)
    result = _handle(consumer_group_offsets, group_id=group_id, topics=topics)
    logger.info(
        "consumer_group_offsets completado", group_id=group_id, partitions=result["partition_count"]
    )
    return result


@mcp.tool(
    name="produce_message",
    description=(
        "Produce un mensaje en un topic Kafka. "
        "Parámetros: topic (requerido), value (string o dict → se serializa como JSON), "
        "key (string opcional), partition (int opcional), headers (dict opcional). "
        "Retorna: topic, partition, offset, timestamp_ms, key, value_size_bytes."
    ),
)
def tool_produce_message(
    topic: str,
    value: str | dict[str, Any] = "",
    key: str | None = None,
    partition: int | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    logger.info("produce_message llamado", topic=topic, key=key)
    result = _handle(
        produce_message, topic=topic, value=value, key=key, partition=partition, headers=headers
    )
    logger.info("produce_message completado", topic=topic, offset=result["offset"])
    return result


@mcp.tool(
    name="consume_messages",
    description=(
        "Consume mensajes de un topic Kafka. "
        "Parámetros: topic (requerido), group_id (default 'mcp-kafka-consumer'), "
        "max_messages (int, default 50), from_beginning (bool, default false), "
        "timeout (float segundos, default 5), parse_json (bool, default true). "
        "Retorna: topic, group_id, messages[] (partition, offset, key, value, timestamp_ms, headers), count."
    ),
)
def tool_consume_messages(
    topic: str,
    group_id: str = "mcp-kafka-consumer",
    max_messages: int | None = None,
    from_beginning: bool = False,
    timeout: float | None = None,
    parse_json: bool = True,
) -> dict[str, Any]:
    logger.info(
        "consume_messages llamado", topic=topic, group_id=group_id, from_beginning=from_beginning
    )
    result = _handle(
        consume_messages,
        topic=topic,
        group_id=group_id,
        max_messages=max_messages,
        from_beginning=from_beginning,
        timeout=timeout,
        parse_json=parse_json,
    )
    logger.info("consume_messages completado", topic=topic, count=result["count"])
    return result


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="create_topic",
    description="Crea un nuevo topic Kafka. Parametros: topic (requerido), num_partitions (default 1), replication_factor (default 1).",
)
def tool_create_topic(topic: str, num_partitions: int = 1, replication_factor: int = 1) -> dict[str, Any]:
    logger.info("create_topic llamado", topic=topic)
    return _handle(create_topic, topic=topic, num_partitions=num_partitions, replication_factor=replication_factor)


@mcp.tool(
    name="delete_topic",
    description="Elimina un topic Kafka. Parametros: topic (requerido).",
)
def tool_delete_topic(topic: str) -> dict[str, Any]:
    logger.info("delete_topic llamado", topic=topic)
    return _handle(delete_topic, topic=topic)


@mcp.tool(
    name="topic_partitions",
    description="Obtiene las particiones de un topic. Parametros: topic (requerido). Retorna: partition_count, partitions[].",
)
def tool_topic_partitions(topic: str) -> dict[str, Any]:
    logger.info("topic_partitions llamado", topic=topic)
    return _handle(topic_partitions, topic=topic)


@mcp.tool(
    name="topic_offsets",
    description="Obtiene los offsets begin/end de cada particion de un topic. Parametros: topic (requerido).",
)
def tool_topic_offsets(topic: str) -> dict[str, Any]:
    logger.info("topic_offsets llamado", topic=topic)
    return _handle(topic_offsets, topic=topic)


@mcp.tool(
    name="cluster_metadata",
    description="Obtiene metadata completa del cluster: brokers, topics, controller. Retorna: cluster_id, brokers[], broker_count, topic_count.",
)
def tool_cluster_metadata() -> dict[str, Any]:
    logger.info("cluster_metadata llamado")
    return _handle(cluster_metadata)


@mcp.tool(
    name="broker_list",
    description="Lista los brokers del cluster Kafka. Retorna: brokers[], count.",
)
def tool_broker_list() -> dict[str, Any]:
    logger.info("broker_list llamado")
    return _handle(broker_list)


@mcp.tool(
    name="produce_batch",
    description="Produce un lote de mensajes en un topic. Parametros: topic (requerido), messages (list de dicts con 'value' y 'key' opcional).",
)
def tool_produce_batch(topic: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    logger.info("produce_batch llamado", topic=topic, count=len(messages))
    return _handle(produce_batch, topic=topic, messages=messages)


@mcp.tool(
    name="consumer_group_describe",
    description="Describe un consumer group: estado, miembros, asignaciones. Parametros: group_id (requerido).",
)
def tool_consumer_group_describe(group_id: str) -> dict[str, Any]:
    logger.info("consumer_group_describe llamado", group_id=group_id)
    return _handle(consumer_group_describe, group_id=group_id)


@mcp.tool(
    name="consumer_group_reset_offsets",
    description="Resetea offsets de un consumer group. Parametros: group_id, topic, partition (default -1 = todas), offset ('earliest' o 'latest').",
)
def tool_consumer_group_reset_offsets(group_id: str, topic: str, partition: int = -1, offset: str = "earliest") -> dict[str, Any]:
    logger.info("consumer_group_reset_offsets llamado", group_id=group_id, topic=topic)
    return _handle(consumer_group_reset_offsets, group_id=group_id, topic=topic, partition=partition, offset=offset)


@mcp.tool(
    name="consumer_group_delete",
    description="Elimina un consumer group del cluster. Parametros: group_id (requerido).",
)
def tool_consumer_group_delete(group_id: str) -> dict[str, Any]:
    logger.info("consumer_group_delete llamado", group_id=group_id)
    return _handle(consumer_group_delete, group_id=group_id)


@mcp.tool(
    name="alter_topic_config",
    description="Modifica la configuracion de un topic. Parametros: topic (requerido), config (dict string->string, ej: {'retention.ms': '86400000'}).",
)
def tool_alter_topic_config(topic: str, config: dict[str, str]) -> dict[str, Any]:
    logger.info("alter_topic_config llamado", topic=topic)
    return _handle(alter_topic_config, topic=topic, config=config)


@mcp.tool(
    name="list_acls",
    description="Lista ACLs del cluster Kafka. Parametros: principal (string opcional), topic (string opcional), group_id (string opcional). Retorna: acls[], count.",
)
def tool_list_acls(principal: str | None = None, topic: str | None = None, group_id: str | None = None) -> dict[str, Any]:
    logger.info("list_acls llamado")
    return _handle(list_acls, principal=principal, topic=topic, group_id=group_id)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("kafka://configuration")
def res_config() -> str:
    return res.kafka_configuration()


@mcp.resource("kafka://concepts")
def res_concepts() -> str:
    return res.kafka_concepts()


@mcp.resource("kafka://produce-guide")
def res_produce() -> str:
    return res.kafka_produce_guide()


@mcp.resource("kafka://consume-guide")
def res_consume() -> str:
    return res.kafka_consume_guide()


@mcp.resource("kafka://topic-management")
def res_topic_mgmt() -> str:
    return res.kafka_topic_management()


@mcp.resource("kafka://consumer-groups")
def res_cg() -> str:
    return res.kafka_consumer_groups()


@mcp.resource("kafka://security-guide")
def res_sec() -> str:
    return res.kafka_security_guide()


@mcp.resource("kafka://best-practices")
def res_best() -> str:
    return res.kafka_best_practices()


@mcp.resource("kafka://error-codes")
def res_errors() -> str:
    return res.kafka_error_codes()


@mcp.resource("kafka://troubleshooting")
def res_trouble() -> str:
    return res.kafka_troubleshooting()


@mcp.resource("kafka://quick-reference")
def res_quick() -> str:
    return res.kafka_quick_reference()


@mcp.resource("kafka://performance-tips")
def res_perf() -> str:
    return res.kafka_performance_tips()


@mcp.resource("kafka://examples")
def res_examples() -> str:
    return res.kafka_examples()


@mcp.resource("kafka://broker-management")
def res_brokers() -> str:
    return res.kafka_broker_management()


@mcp.resource("kafka://partitioning-guide")
def res_partitioning() -> str:
    return res.kafka_partitioning_guide()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")
