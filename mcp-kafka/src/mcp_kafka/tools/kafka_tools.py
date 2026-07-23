"""Herramientas Kafka para mcp-kafka.

Usa confluent-kafka (librdkafka) para operaciones de administración,
producción y consumo de mensajes.
"""

from __future__ import annotations

import json
from typing import Any

from mcp_shared.errors import ApiError, NetworkError, ValidationError

from mcp_kafka.config import settings

_CONFLUENT_MISSING = "confluent-kafka no está instalado. Ejecuta: pip install confluent-kafka"
_DEFAULT_GROUP_ID = "mcp-kafka-consumer"


def _get_admin_client() -> Any:
    """Crea y retorna un AdminClient de confluent-kafka."""
    try:
        from confluent_kafka.admin import AdminClient
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    try:
        return AdminClient(settings.base_config())
    except Exception as exc:
        raise NetworkError(
            url=settings.bootstrap_servers,
            reason=f"No se puede conectar al cluster Kafka: {exc}",
        ) from exc


def _validate_topic(topic: str) -> None:
    if not topic or not topic.strip():
        raise ValidationError(field="topic", message="El nombre del topic no puede estar vacío.")


# ---------------------------------------------------------------------------
# topics_list
# ---------------------------------------------------------------------------


def topics_list(
    prefix: str | None = None,
    exclude_internal: bool = True,
) -> dict[str, Any]:
    """Lista todos los topics del cluster Kafka.

    Args:
        prefix: Filtrar topics que empiezan con este prefijo.
        exclude_internal: Si True excluye topics internos (``__``). Default True.

    Returns:
        Dict con ``topics`` (list de dicts con name, partitions, replication_factor),
        ``count`` (int), ``cluster_id`` (str).

    Raises:
        NetworkError: Si no se puede conectar al cluster.
    """
    admin = _get_admin_client()

    try:
        metadata = admin.list_topics(timeout=settings.admin_timeout)
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error listando topics: {exc}",
        ) from exc

    topics_out = []
    for name, topic_meta in metadata.topics.items():
        if exclude_internal and name.startswith("__"):
            continue
        if prefix and not name.startswith(prefix):
            continue
        topics_out.append(
            {
                "name": name,
                "partitions": len(topic_meta.partitions),
                "error": str(topic_meta.error) if topic_meta.error else None,
            }
        )

    topics_out.sort(key=lambda t: t["name"])

    return {
        "topics": topics_out,
        "count": len(topics_out),
        "cluster_id": metadata.cluster_id or "unknown",
        "broker_count": len(metadata.brokers),
    }


# ---------------------------------------------------------------------------
# topic_describe
# ---------------------------------------------------------------------------


def topic_describe(topic: str) -> dict[str, Any]:
    """Describe un topic Kafka: particiones, líder, replicas e ISR.

    Args:
        topic: Nombre del topic.

    Returns:
        Dict con ``topic``, ``partitions`` (list con id, leader, replicas, isr, offsets).

    Raises:
        ValidationError: Si el topic no existe o el nombre está vacío.
        NetworkError: Si no se puede conectar.
    """
    _validate_topic(topic)
    admin = _get_admin_client()

    try:
        metadata = admin.list_topics(topic=topic, timeout=settings.admin_timeout)
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error describiendo topic '{topic}': {exc}",
        ) from exc

    if topic not in metadata.topics:
        raise ValidationError(
            field="topic",
            message=f"Topic '{topic}' no encontrado en el cluster.",
            value=topic,
        )

    topic_meta = metadata.topics[topic]
    if topic_meta.error:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error en topic '{topic}': {topic_meta.error}",
        )

    partitions = []
    for pid, part_meta in sorted(topic_meta.partitions.items()):
        partitions.append(
            {
                "id": pid,
                "leader": part_meta.leader,
                "replicas": list(part_meta.replicas),
                "isr": list(part_meta.isrs),
                "error": str(part_meta.error) if part_meta.error else None,
            }
        )

    return {
        "topic": topic,
        "partitions": partitions,
        "partition_count": len(partitions),
        "replication_factor": len(partitions[0]["replicas"]) if partitions else 0,
    }


# ---------------------------------------------------------------------------
# consumer_groups_list
# ---------------------------------------------------------------------------


def consumer_groups_list(prefix: str | None = None) -> dict[str, Any]:
    """Lista todos los consumer groups del cluster.

    Args:
        prefix: Filtrar groups que empiezan con este prefijo.

    Returns:
        Dict con ``groups`` (list de dicts con group_id, state, members),
        ``count`` (int).

    Raises:
        NetworkError: Si no se puede conectar al cluster.
    """
    try:
        from confluent_kafka.admin import AdminClient
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    admin = AdminClient(settings.base_config())

    try:
        future = admin.list_consumer_groups(request_timeout=settings.admin_timeout)
        result = future.result()
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error listando consumer groups: {exc}",
        ) from exc

    groups_out = []
    for group in result.valid:
        group_id = group.group_id
        if prefix and not group_id.startswith(prefix):
            continue
        groups_out.append(
            {
                "group_id": group_id,
                "state": str(group.state) if hasattr(group, "state") else "unknown",
                "is_simple": getattr(group, "is_simple_consumer_group", False),
            }
        )

    groups_out.sort(key=lambda g: g["group_id"])

    return {
        "groups": groups_out,
        "count": len(groups_out),
        "errors": [str(e) for e in (result.errors or [])],
    }


# ---------------------------------------------------------------------------
# consumer_group_offsets
# ---------------------------------------------------------------------------


def consumer_group_offsets(group_id: str, topics: list[str] | None = None) -> dict[str, Any]:
    """Obtiene los offsets actuales de un consumer group.

    Args:
        group_id: ID del consumer group.
        topics: Lista de topics a consultar. None = todos los topics del grupo.

    Returns:
        Dict con ``group_id``, ``offsets`` (list con topic, partition, offset, lag estimado).

    Raises:
        ValidationError: Si el group_id está vacío.
        NetworkError: Si no se puede conectar.
    """
    if not group_id or not group_id.strip():
        raise ValidationError(field="group_id", message="El group_id no puede estar vacío.")

    try:
        from confluent_kafka import TopicPartition
        from confluent_kafka.admin import AdminClient
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    admin = AdminClient(settings.base_config())

    topic_partitions = None
    if topics:
        topic_partitions = [TopicPartition(t, -1) for t in topics]

    try:
        future = admin.list_consumer_group_offsets(
            [{"group_id": group_id, "partitions": topic_partitions}],  # type: ignore[list-item]
            request_timeout=settings.admin_timeout,
        )
        results = future.result()  # type: ignore[attr-defined]
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error obteniendo offsets del grupo '{group_id}': {exc}",
        ) from exc

    offsets_out = []
    for group_result in results.values():
        if group_result.error:
            raise ApiError(
                url=settings.bootstrap_servers,
                status_code=0,
                response_body=f"Error en grupo '{group_id}': {group_result.error}",
            )
        for tp, offset_info in (group_result.topic_partitions or {}).items():
            offsets_out.append(
                {
                    "topic": tp.topic,
                    "partition": tp.partition,
                    "offset": offset_info.offset if offset_info.offset >= 0 else "OFFSET_INVALID",
                    "metadata": getattr(offset_info, "metadata", "") or "",
                }
            )

    offsets_out.sort(key=lambda x: (x["topic"], x["partition"]))

    return {
        "group_id": group_id,
        "offsets": offsets_out,
        "partition_count": len(offsets_out),
    }


# ---------------------------------------------------------------------------
# produce_message
# ---------------------------------------------------------------------------


def produce_message(
    topic: str,
    value: str | dict[str, Any],
    key: str | None = None,
    partition: int | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Produce un mensaje en un topic Kafka.

    Args:
        topic: Nombre del topic destino.
        value: Valor del mensaje. Si es dict se serializa a JSON automáticamente.
        key: Clave del mensaje (para particionado). None = sin clave.
        partition: Partición específica. None = usa el partitioner.
        headers: Headers del mensaje como dict string→string.

    Returns:
        Dict con ``topic``, ``partition`` (asignada), ``offset``, ``timestamp``.

    Raises:
        ValidationError: Si el topic está vacío.
        ApiError: Si hay error al producir.
    """
    _validate_topic(topic)

    try:
        from confluent_kafka import Producer
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    if isinstance(value, dict):
        value_bytes = json.dumps(value).encode("utf-8")
    else:
        value_bytes = str(value).encode("utf-8")

    key_bytes = key.encode("utf-8") if key else None

    header_list = [(k, v.encode("utf-8")) for k, v in (headers or {}).items()]

    delivery_result: dict[str, Any] = {}
    error_result: dict[str, Any] = {}

    def on_delivery(err: Any, msg: Any) -> None:
        if err:
            error_result["error"] = str(err)
        else:
            delivery_result["topic"] = msg.topic()
            delivery_result["partition"] = msg.partition()
            delivery_result["offset"] = msg.offset()
            delivery_result["timestamp"] = msg.timestamp()[1] if msg.timestamp() else None

    cfg = settings.base_config()
    cfg["acks"] = "all"
    producer = Producer(cfg)

    try:
        kwargs: dict[str, Any] = {
            "value": value_bytes,
            "key": key_bytes,
            "headers": header_list,
            "on_delivery": on_delivery,
        }
        if partition is not None:
            kwargs["partition"] = partition

        producer.produce(topic, **kwargs)
        remaining = producer.flush(timeout=settings.consume_timeout)
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error produciendo mensaje en '{topic}': {exc}",
        ) from exc

    if error_result:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error de delivery en '{topic}': {error_result['error']}",
        )

    if not delivery_result:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Timeout esperando confirmación de delivery en '{topic}'. Messages not flushed: {remaining}",
        )

    return {
        "topic": delivery_result["topic"],
        "partition": delivery_result["partition"],
        "offset": delivery_result["offset"],
        "timestamp_ms": delivery_result["timestamp"],
        "key": key,
        "value_size_bytes": len(value_bytes),
    }


# ---------------------------------------------------------------------------
# consume_messages
# ---------------------------------------------------------------------------


def _parse_message(msg: Any, parse_json: bool) -> dict[str, Any]:
    """Convierte un mensaje confluent-kafka a dict serializable."""
    raw_value = msg.value()
    if raw_value is None:
        value: Any = None
    elif parse_json:
        try:
            value = json.loads(raw_value.decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            value = raw_value.decode("utf-8", errors="replace")
    else:
        value = raw_value.decode("utf-8", errors="replace")

    raw_key = msg.key()
    key = raw_key.decode("utf-8", errors="replace") if raw_key else None

    return {
        "partition": msg.partition(),
        "offset": msg.offset(),
        "timestamp_ms": msg.timestamp()[1] if msg.timestamp() else None,
        "key": key,
        "value": value,
        "headers": {
            (k.decode("utf-8", errors="replace") if isinstance(k, bytes) else k): v.decode(
                "utf-8", errors="replace"
            )
            for k, v in (msg.headers() or [])
        },
    }


def _poll_loop(
    consumer: Any,
    topic: str,
    max_messages: int,
    timeout: float,
    parse_json: bool,
    kafka_error_cls: Any,
) -> list[dict[str, Any]]:
    """Loop de polling interno: lee hasta max_messages o agota el timeout."""
    messages_out: list[dict[str, Any]] = []
    deadline = timeout

    while len(messages_out) < max_messages and deadline > 0:
        msg = consumer.poll(timeout=min(1.0, deadline))
        deadline -= 1.0
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == kafka_error_cls._PARTITION_EOF:
                break
            raise ApiError(
                url=settings.bootstrap_servers,
                status_code=0,
                response_body=f"Error consumiendo de '{topic}': {msg.error()}",
            )
        messages_out.append(_parse_message(msg, parse_json))

    return messages_out


def consume_messages(
    topic: str,
    group_id: str = _DEFAULT_GROUP_ID,
    max_messages: int | None = None,
    from_beginning: bool = False,
    timeout: float | None = None,
    parse_json: bool = True,
) -> dict[str, Any]:
    """Consume mensajes de un topic Kafka.

    Args:
        topic: Nombre del topic.
        group_id: Consumer group ID. Default ``"mcp-kafka-consumer"``.
        max_messages: Máximo de mensajes a consumir. Default: ``settings.max_consume_messages``.
        from_beginning: Si True lee desde el principio del topic (offset earliest).
        timeout: Timeout total de espera en segundos. Default: ``settings.consume_timeout``.
        parse_json: Si True intenta parsear el valor como JSON. Default True.

    Returns:
        Dict con ``topic``, ``messages`` (list con partition, offset, key, value, timestamp),
        ``count``, ``group_id``.

    Raises:
        ValidationError: Si el topic está vacío.
        ApiError: Si hay error al consumir.
    """
    _validate_topic(topic)

    resolved_max = max_messages or settings.max_consume_messages
    resolved_timeout = timeout or settings.consume_timeout

    try:
        from confluent_kafka import Consumer, KafkaError
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    cfg = settings.base_config()
    cfg.update(
        {
            "group.id": group_id,
            "auto.offset.reset": "earliest" if from_beginning else "latest",
            "enable.auto.commit": False,
            "session.timeout.ms": 6000,
        }
    )

    consumer = Consumer(cfg)
    messages_out: list[dict[str, Any]] = []

    try:
        consumer.subscribe([topic])
        messages_out = _poll_loop(
            consumer, topic, resolved_max, resolved_timeout, parse_json, KafkaError
        )
    except (ApiError, NetworkError, ValidationError):
        raise
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error inesperado consumiendo de '{topic}': {exc}",
        ) from exc
    finally:
        consumer.close()

    return {
        "topic": topic,
        "group_id": group_id,
        "messages": messages_out,
        "count": len(messages_out),
        "from_beginning": from_beginning,
    }


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def create_topic(
    topic: str,
    num_partitions: int = 1,
    replication_factor: int = 1,
) -> dict[str, Any]:
    """Crea un nuevo topic en el cluster Kafka."""
    _validate_topic(topic)
    if num_partitions < 1:
        raise ValidationError(field="num_partitions", message="num_partitions debe ser >= 1.")
    if replication_factor < 1:
        raise ValidationError(field="replication_factor", message="replication_factor debe ser >= 1.")

    try:
        from confluent_kafka.admin import NewTopic
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    admin = _get_admin_client()
    new_topic = NewTopic(
        topic=topic,
        num_partitions=num_partitions,
        replication_factor=replication_factor,
    )
    try:
        future = admin.create_topics([new_topic])
        future[topic].result()
        return {
            "topic": topic,
            "num_partitions": num_partitions,
            "replication_factor": replication_factor,
            "created": True,
        }
    except Exception as exc:
        if "already exists" in str(exc).lower():
            raise ValidationError(
                field="topic",
                message=f"Topic '{topic}' ya existe.",
                value=topic,
            ) from exc
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error creando topic '{topic}': {exc}",
        ) from exc


def delete_topic(topic: str) -> dict[str, Any]:
    """Elimina un topic del cluster Kafka."""
    _validate_topic(topic)
    admin = _get_admin_client()
    try:
        future = admin.delete_topics([topic])
        future[topic].result()
        return {"topic": topic, "deleted": True}
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error eliminando topic '{topic}': {exc}",
        ) from exc


def topic_partitions(topic: str) -> dict[str, Any]:
    """Obtiene el numero de particiones de un topic."""
    _validate_topic(topic)
    admin = _get_admin_client()
    try:
        metadata = admin.list_topics(topic=topic, timeout=settings.admin_timeout)
        if topic not in metadata.topics:
            raise ValidationError(
                field="topic",
                message=f"Topic '{topic}' no encontrado.",
                value=topic,
            )
        return {
            "topic": topic,
            "partition_count": len(metadata.topics[topic].partitions),
            "partitions": list(metadata.topics[topic].partitions.keys()),
        }
    except (ValidationError, ApiError, NetworkError):
        raise
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error obteniendo particiones de '{topic}': {exc}",
        ) from exc


def topic_offsets(topic: str) -> dict[str, Any]:
    """Obtiene los offsets (begin/end) de cada particion de un topic."""
    _validate_topic(topic)
    try:
        from confluent_kafka import Consumer
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    cfg = settings.base_config()
    cfg["group.id"] = "mcp-kafka-offset-query"
    consumer = Consumer(cfg)
    try:
        metadata = consumer.list_topics(topic=topic, timeout=settings.admin_timeout)
        if topic not in metadata.topics:
            raise ValidationError(
                field="topic",
                message=f"Topic '{topic}' no encontrado.",
                value=topic,
            )
        from confluent_kafka import TopicPartition as TP

        offsets = []
        for pid in sorted(metadata.topics[topic].partitions.keys()):
            _, begin = consumer.get_watermark_offsets(TP(topic, pid), cached=False)
            _, end = consumer.get_watermark_offsets(TP(topic, pid), cached=False)
            offsets.append({"partition": pid, "begin_offset": begin, "end_offset": end})
        return {"topic": topic, "offsets": offsets, "partition_count": len(offsets)}
    except (ValidationError, ApiError, NetworkError):
        raise
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error obteniendo offsets de '{topic}': {exc}",
        ) from exc
    finally:
        consumer.close()


def cluster_metadata() -> dict[str, Any]:
    """Obtiene metadata completa del cluster Kafka."""
    admin = _get_admin_client()
    try:
        metadata = admin.list_topics(timeout=settings.admin_timeout)
        brokers = []
        for bid, broker in metadata.brokers.items():
            brokers.append({"id": bid, "host": broker.host, "port": broker.port})
        return {
            "cluster_id": metadata.cluster_id or "unknown",
            "brokers": brokers,
            "broker_count": len(brokers),
            "topic_count": len(metadata.topics),
            "controller_id": getattr(metadata, "controller_id", None),
        }
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error obteniendo metadata del cluster: {exc}",
        ) from exc


def broker_list() -> dict[str, Any]:
    """Lista los brokers del cluster Kafka."""
    admin = _get_admin_client()
    try:
        metadata = admin.list_topics(timeout=settings.admin_timeout)
        brokers = []
        for bid, broker in metadata.brokers.items():
            brokers.append({"id": bid, "host": broker.host, "port": broker.port})
        return {"brokers": brokers, "count": len(brokers)}
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error listando brokers: {exc}",
        ) from exc


def produce_batch(
    topic: str,
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Produce un lote de mensajes en un topic."""
    _validate_topic(topic)
    if not messages:
        raise ValidationError(field="messages", message="La lista de mensajes no puede estar vacia.")

    try:
        from confluent_kafka import Producer
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    cfg = settings.base_config()
    cfg["acks"] = "all"
    producer = Producer(cfg)

    results: list[dict[str, Any]] = []
    errors: list[str] = []

    def on_delivery(err: Any, msg: Any, idx: int) -> None:
        if err:
            errors.append(f"Mensaje {idx}: {err}")
        else:
            results.append({
                "index": idx,
                "partition": msg.partition(),
                "offset": msg.offset(),
            })

    try:
        for i, m in enumerate(messages):
            value = m.get("value", "")
            if isinstance(value, dict):
                value_bytes = json.dumps(value).encode("utf-8")
            else:
                value_bytes = str(value).encode("utf-8")
            key_bytes = str(m.get("key", "")).encode("utf-8") if m.get("key") else None
            producer.produce(
                topic,
                value=value_bytes,
                key=key_bytes,
                on_delivery=lambda err, msg, idx=i: on_delivery(err, msg, idx),
            )
        producer.flush(timeout=settings.consume_timeout)
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error produciendo batch en '{topic}': {exc}",
        ) from exc

    return {
        "topic": topic,
        "produced": len(results),
        "errors": errors,
        "results": results,
    }


def consumer_group_describe(group_id: str) -> dict[str, Any]:
    """Describe un consumer group: estado, miembros, asignaciones."""
    if not group_id or not group_id.strip():
        raise ValidationError(field="group_id", message="El group_id no puede estar vacio.")

    try:
        from confluent_kafka.admin import AdminClient
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    admin = AdminClient(settings.base_config())
    try:
        future = admin.describe_consumer_groups(
            [group_id], request_timeout=settings.admin_timeout
        )
        result = future.result()
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error describiendo grupo '{group_id}': {exc}",
        ) from exc

    group_info = result.get(group_id)
    if group_info is None:
        raise ValidationError(
            field="group_id",
            message=f"Consumer group '{group_id}' no encontrado.",
            value=group_id,
        )

    members = []
    for member in getattr(group_info, "members", []) or []:
        assignment = []
        for tp in getattr(member, "assignment", []) or []:
            assignment.append({"topic": tp.topic, "partition": tp.partition})
        members.append({
            "member_id": getattr(member, "member_id", ""),
            "client_id": getattr(member, "client_id", ""),
            "client_host": getattr(member, "client_host", ""),
            "assignment": assignment,
        })

    return {
        "group_id": group_id,
        "state": str(getattr(group_info, "state", "unknown")),
        "is_simple": getattr(group_info, "is_simple_consumer_group", False),
        "partition_assignor": getattr(group_info, "partition_assignor", ""),
        "members": members,
        "member_count": len(members),
    }


def consumer_group_reset_offsets(
    group_id: str,
    topic: str,
    partition: int = -1,
    offset: str = "earliest",
) -> dict[str, Any]:
    """Resetea los offsets de un consumer group a earliest o latest."""
    if not group_id or not group_id.strip():
        raise ValidationError(field="group_id", message="El group_id no puede estar vacio.")
    _validate_topic(topic)

    try:
        from confluent_kafka import TopicPartition
        from confluent_kafka.admin import AdminClient
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    admin = AdminClient(settings.base_config())

    if offset not in ("earliest", "latest"):
        raise ValidationError(
            field="offset",
            message="offset debe ser 'earliest' o 'latest'.",
            value=offset,
        )

    tp = TopicPartition(topic, partition)
    if offset == "earliest":
        tp.offset = -2
    else:
        tp.offset = -1

    try:
        future = admin.alter_consumer_group_offsets(
            [{"group_id": group_id, "partitions": [tp]}],
            request_timeout=settings.admin_timeout,
        )
        future.result()
        return {
            "group_id": group_id,
            "topic": topic,
            "partition": partition,
            "reset_to": offset,
            "success": True,
        }
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error reseteando offsets del grupo '{group_id}': {exc}",
        ) from exc


def consumer_group_delete(group_id: str) -> dict[str, Any]:
    """Elimina un consumer group del cluster."""
    if not group_id or not group_id.strip():
        raise ValidationError(field="group_id", message="El group_id no puede estar vacio.")

    try:
        from confluent_kafka.admin import AdminClient
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    admin = AdminClient(settings.base_config())
    try:
        future = admin.delete_consumer_groups([group_id], request_timeout=settings.admin_timeout)
        future.result()
        return {"group_id": group_id, "deleted": True}
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error eliminando grupo '{group_id}': {exc}",
        ) from exc


def alter_topic_config(
    topic: str,
    config: dict[str, str],
) -> dict[str, Any]:
    """Modifica la configuracion de un topic (retention.ms, etc.)."""
    _validate_topic(topic)
    if not config:
        raise ValidationError(field="config", message="La configuracion no puede estar vacia.")

    try:
        from confluent_kafka.admin import AdminClient, ConfigResource, ConfigSource
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    admin = AdminClient(settings.base_config())
    resource = ConfigResource(2, topic)
    for key, value in config.items():
        resource.set_config(key, value)

    try:
        future = admin.incremental_alter_configs([resource])
        future[topic].result()
        return {"topic": topic, "config_updated": config, "success": True}
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error modificando config de '{topic}': {exc}",
        ) from exc


def list_acls(
    principal: str | None = None,
    topic: str | None = None,
    group_id: str | None = None,
) -> dict[str, Any]:
    """Lista ACLs del cluster Kafka, opcionalmente filtradas."""
    try:
        from confluent_kafka.admin import AdminClient, ACLFilter, ResourcePatternFilter, ACLBinding
    except ImportError as exc:
        raise NetworkError(url=settings.bootstrap_servers, reason=_CONFLUENT_MISSING) from exc

    admin = AdminClient(settings.base_config())

    acl_filter = ACLFilter(
        resource_pattern_filter=ResourcePatternFilter(2, topic, 3),
        principal=principal,
        host="*",
        operation=2,
        permission_type=2,
    )

    try:
        future = admin.describe_acls(acl_filter, request_timeout=settings.admin_timeout)
        result = future.result()
    except Exception as exc:
        raise ApiError(
            url=settings.bootstrap_servers,
            status_code=0,
            response_body=f"Error listando ACLs: {exc}",
        ) from exc

    acls = []
    for binding in getattr(result, "acls", []) or []:
        acls.append({
            "principal": getattr(binding, "principal", ""),
            "host": getattr(binding, "host", ""),
            "operation": str(getattr(binding, "operation", "")),
            "permission_type": str(getattr(binding, "permission_type", "")),
            "resource_type": str(getattr(binding, "resource_pattern", "")),
        })

    return {"acls": acls, "count": len(acls)}
