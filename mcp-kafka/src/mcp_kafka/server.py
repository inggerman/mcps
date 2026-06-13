"""Servidor FastMCP para mcp-kafka."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData

from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging
from mcp_kafka.config import settings
from mcp_kafka.tools import (
    consumer_group_offsets,
    consumer_groups_list,
    consume_messages,
    produce_message,
    topic_describe,
    topics_list,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-kafka",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:  # noqa: ARG001
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
        raise SdkMcpError(ErrorData(code=-32603, message=f"Error interno: {exc}")) from exc


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
    logger.info("consumer_group_offsets completado", group_id=group_id, partitions=result["partition_count"])
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
    result = _handle(produce_message, topic=topic, value=value, key=key, partition=partition, headers=headers)
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
    logger.info("consume_messages llamado", topic=topic, group_id=group_id, from_beginning=from_beginning)
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
