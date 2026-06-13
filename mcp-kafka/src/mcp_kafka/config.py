"""Configuración del servidor mcp-kafka."""

from __future__ import annotations

from typing import Any

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from mcp_shared.config import BaseMcpSettings


class KafkaSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_KAFKA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    bootstrap_servers: str = Field(
        default="localhost:9092",
        description=(
            "Brokers Kafka (comma-separated). "
            "Variable: MCP_KAFKA_BOOTSTRAP_SERVERS. "
            "Ej: localhost:9092 o broker1:9092,broker2:9092"
        ),
    )
    security_protocol: str = Field(
        default="PLAINTEXT",
        description=(
            "Protocolo de seguridad: PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL. "
            "Variable: MCP_KAFKA_SECURITY_PROTOCOL."
        ),
    )
    sasl_mechanism: str | None = Field(
        default=None,
        description="Mecanismo SASL: PLAIN, SCRAM-SHA-256, SCRAM-SHA-512. Variable: MCP_KAFKA_SASL_MECHANISM.",
    )
    sasl_username: str | None = Field(
        default=None,
        description="Usuario SASL. Variable: MCP_KAFKA_SASL_USERNAME.",
    )
    sasl_password: str | None = Field(
        default=None,
        description="Contraseña SASL. Variable: MCP_KAFKA_SASL_PASSWORD.",
    )
    ssl_ca_location: str | None = Field(
        default=None,
        description="Ruta al CA certificate para SSL. Variable: MCP_KAFKA_SSL_CA_LOCATION.",
    )
    consume_timeout: float = Field(
        default=5.0,
        ge=0.5,
        le=60.0,
        description="Timeout en segundos para consumir mensajes. Variable: MCP_KAFKA_CONSUME_TIMEOUT.",
    )
    max_consume_messages: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Número máximo de mensajes a consumir por llamada. Variable: MCP_KAFKA_MAX_CONSUME_MESSAGES.",
    )
    admin_timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="Timeout en segundos para operaciones admin (list topics, etc.). Variable: MCP_KAFKA_ADMIN_TIMEOUT.",
    )

    def base_config(self) -> dict[str, Any]:
        """Retorna la configuración base de confluent-kafka."""
        cfg: dict[str, Any] = {
            "bootstrap.servers": self.bootstrap_servers,
            "security.protocol": self.security_protocol,
        }
        if self.sasl_mechanism:
            cfg["sasl.mechanism"] = self.sasl_mechanism
        if self.sasl_username:
            cfg["sasl.username"] = self.sasl_username
        if self.sasl_password:
            cfg["sasl.password"] = self.sasl_password
        if self.ssl_ca_location:
            cfg["ssl.ca.location"] = self.ssl_ca_location
        return cfg

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["bootstrap_servers"] = self.bootstrap_servers
        base["security_protocol"] = self.security_protocol
        return base


settings = KafkaSettings()
