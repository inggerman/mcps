"""Tests unitarios para kafka_tools (mocking de confluent-kafka)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from mcp_kafka.tools.kafka_tools import (
    _parse_message,
    _poll_loop,
    produce_message,
    topic_describe,
    topics_list,
)
from mcp_shared.errors import ApiError, ValidationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_msg(
    partition: int = 0,
    offset: int = 10,
    key: bytes | None = b"mykey",
    value: bytes | None = b'{"event": "test"}',
    error: MagicMock | None = None,
    headers: list | None = None,
) -> MagicMock:
    msg = MagicMock()
    msg.partition.return_value = partition
    msg.offset.return_value = offset
    msg.key.return_value = key
    msg.value.return_value = value
    msg.error.return_value = error
    msg.timestamp.return_value = (1, 1700000000000)
    msg.headers.return_value = headers or []
    return msg


# ---------------------------------------------------------------------------
# _parse_message
# ---------------------------------------------------------------------------


class TestParseMessage:
    def test_parses_json_value(self) -> None:
        msg = _mock_msg(value=b'{"id": 1}')
        result = _parse_message(msg, parse_json=True)
        assert result["value"] == {"id": 1}

    def test_fallback_to_string_on_invalid_json(self) -> None:
        msg = _mock_msg(value=b"plain text")
        result = _parse_message(msg, parse_json=True)
        assert result["value"] == "plain text"

    def test_no_json_parse(self) -> None:
        msg = _mock_msg(value=b'{"id": 1}')
        result = _parse_message(msg, parse_json=False)
        assert result["value"] == '{"id": 1}'

    def test_none_value(self) -> None:
        msg = _mock_msg(value=None)
        result = _parse_message(msg, parse_json=True)
        assert result["value"] is None

    def test_none_key(self) -> None:
        msg = _mock_msg(key=None)
        result = _parse_message(msg, parse_json=False)
        assert result["key"] is None

    def test_key_decoded(self) -> None:
        msg = _mock_msg(key=b"order-123")
        result = _parse_message(msg, parse_json=False)
        assert result["key"] == "order-123"

    def test_headers_decoded(self) -> None:
        msg = _mock_msg(headers=[(b"trace-id", b"abc")])
        result = _parse_message(msg, parse_json=False)
        assert result["headers"] == {"trace-id": "abc"}

    def test_partition_and_offset(self) -> None:
        msg = _mock_msg(partition=2, offset=99)
        result = _parse_message(msg, parse_json=False)
        assert result["partition"] == 2
        assert result["offset"] == 99


# ---------------------------------------------------------------------------
# _poll_loop
# ---------------------------------------------------------------------------


class TestPollLoop:
    def _make_kafka_error_cls(self, eof_code: int = -191) -> MagicMock:
        ke = MagicMock()
        ke._PARTITION_EOF = eof_code
        return ke

    def test_returns_messages(self) -> None:
        msgs = [_mock_msg(offset=i) for i in range(3)]
        consumer = MagicMock()
        consumer.poll.side_effect = [*msgs, None, None]

        result = _poll_loop(
            consumer,
            "topic",
            max_messages=10,
            timeout=5.0,
            parse_json=True,
            kafka_error_cls=self._make_kafka_error_cls(),
        )
        assert len(result) == 3

    def test_stops_at_max_messages(self) -> None:
        msgs = [_mock_msg(offset=i) for i in range(10)]
        consumer = MagicMock()
        consumer.poll.side_effect = msgs

        result = _poll_loop(
            consumer,
            "topic",
            max_messages=3,
            timeout=5.0,
            parse_json=True,
            kafka_error_cls=self._make_kafka_error_cls(),
        )
        assert len(result) == 3

    def test_breaks_on_partition_eof(self) -> None:
        eof_error = MagicMock()
        eof_error.code.return_value = -191
        eof_msg = _mock_msg(error=eof_error)

        consumer = MagicMock()
        consumer.poll.side_effect = [_mock_msg(offset=0), eof_msg]

        result = _poll_loop(
            consumer,
            "topic",
            max_messages=10,
            timeout=5.0,
            parse_json=True,
            kafka_error_cls=self._make_kafka_error_cls(),
        )
        assert len(result) == 1

    def test_raises_api_error_on_non_eof_error(self) -> None:
        err = MagicMock()
        err.code.return_value = -1
        err_msg = _mock_msg(error=err)

        consumer = MagicMock()
        consumer.poll.side_effect = [err_msg]

        with pytest.raises(ApiError):
            _poll_loop(
                consumer,
                "topic",
                max_messages=10,
                timeout=5.0,
                parse_json=True,
                kafka_error_cls=self._make_kafka_error_cls(),
            )


# ---------------------------------------------------------------------------
# topics_list
# ---------------------------------------------------------------------------


class TestTopicsList:
    @patch("mcp_kafka.tools.kafka_tools._get_admin_client")
    def test_returns_topics(self, mock_admin: MagicMock) -> None:
        t1 = MagicMock()
        t1.partitions = {0: MagicMock(), 1: MagicMock()}
        t1.error = None
        t2 = MagicMock()
        t2.partitions = {0: MagicMock()}
        t2.error = None

        metadata = MagicMock()
        metadata.topics = {"orders": t1, "payments": t2}
        metadata.cluster_id = "cluster-1"
        metadata.brokers = {0: MagicMock(), 1: MagicMock()}
        mock_admin.return_value.list_topics.return_value = metadata

        result = topics_list()
        assert result["count"] == 2
        assert result["broker_count"] == 2
        assert any(t["name"] == "orders" for t in result["topics"])

    @patch("mcp_kafka.tools.kafka_tools._get_admin_client")
    def test_excludes_internal_topics(self, mock_admin: MagicMock) -> None:
        internal = MagicMock()
        internal.partitions = {0: MagicMock()}
        internal.error = None
        normal = MagicMock()
        normal.partitions = {0: MagicMock()}
        normal.error = None

        metadata = MagicMock()
        metadata.topics = {"__consumer_offsets": internal, "my-topic": normal}
        metadata.cluster_id = "c1"
        metadata.brokers = {}
        mock_admin.return_value.list_topics.return_value = metadata

        result = topics_list(exclude_internal=True)
        names = [t["name"] for t in result["topics"]]
        assert "__consumer_offsets" not in names
        assert "my-topic" in names

    @patch("mcp_kafka.tools.kafka_tools._get_admin_client")
    def test_prefix_filter(self, mock_admin: MagicMock) -> None:
        t = MagicMock()
        t.partitions = {0: MagicMock()}
        t.error = None

        metadata = MagicMock()
        metadata.topics = {"order.created": t, "payment.done": t}
        metadata.cluster_id = "c1"
        metadata.brokers = {}
        mock_admin.return_value.list_topics.return_value = metadata

        result = topics_list(prefix="order")
        assert result["count"] == 1
        assert result["topics"][0]["name"] == "order.created"


# ---------------------------------------------------------------------------
# topic_describe
# ---------------------------------------------------------------------------


class TestTopicDescribe:
    def test_empty_topic_raises(self) -> None:
        with pytest.raises(ValidationError):
            topic_describe("")

    @patch("mcp_kafka.tools.kafka_tools._get_admin_client")
    def test_describes_partitions(self, mock_admin: MagicMock) -> None:
        p0 = MagicMock()
        p0.leader = 1
        p0.replicas = [1, 2]
        p0.isrs = [1, 2]
        p0.error = None

        topic_meta = MagicMock()
        topic_meta.partitions = {0: p0}
        topic_meta.error = None

        metadata = MagicMock()
        metadata.topics = {"my-topic": topic_meta}
        mock_admin.return_value.list_topics.return_value = metadata

        result = topic_describe("my-topic")
        assert result["topic"] == "my-topic"
        assert result["partition_count"] == 1
        assert result["replication_factor"] == 2
        assert result["partitions"][0]["leader"] == 1

    @patch("mcp_kafka.tools.kafka_tools._get_admin_client")
    def test_not_found_raises(self, mock_admin: MagicMock) -> None:
        metadata = MagicMock()
        metadata.topics = {}
        mock_admin.return_value.list_topics.return_value = metadata

        with pytest.raises(ValidationError):
            topic_describe("nonexistent")


# ---------------------------------------------------------------------------
# produce_message
# ---------------------------------------------------------------------------


class TestProduceMessage:
    def test_empty_topic_raises(self) -> None:
        with pytest.raises(ValidationError):
            produce_message("", value="test")

    @patch("mcp_kafka.tools.kafka_tools.settings")
    def test_dict_value_serialized_as_json(self, mock_settings: MagicMock) -> None:
        mock_settings.bootstrap_servers = "localhost:9092"
        mock_settings.base_config.return_value = {"bootstrap.servers": "localhost:9092"}
        mock_settings.consume_timeout = 5.0

        captured: dict = {}

        with patch("confluent_kafka.Producer") as mock_producer_cls:
            producer_inst = MagicMock()
            mock_producer_cls.return_value = producer_inst
            producer_inst.flush.return_value = 0

            def fake_produce(topic: str, **kwargs: Any) -> None:
                captured["value"] = kwargs.get("value")
                on_delivery = kwargs.get("on_delivery")
                fake_msg = MagicMock()
                fake_msg.topic.return_value = topic
                fake_msg.partition.return_value = 0
                fake_msg.offset.return_value = 5
                fake_msg.timestamp.return_value = (1, 1700000000)
                if on_delivery:
                    on_delivery(None, fake_msg)

            producer_inst.produce.side_effect = fake_produce

            result = produce_message("orders", value={"id": 1, "amount": 99.5})

        import json

        assert json.loads(captured["value"].decode()) == {"id": 1, "amount": 99.5}
        assert result["offset"] == 5
