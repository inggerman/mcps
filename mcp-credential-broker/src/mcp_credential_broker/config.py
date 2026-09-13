"""Configuracion del servidor mcp-credential-broker."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class BrokerSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="BROKER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Vault backend ---
    vault_url: str = Field(
        default="http://vault.mrrobot.fs",
        description="URL de la API de Vault. Variable: BROKER_VAULT_URL.",
    )
    vault_token: str = Field(
        default="",
        description="Token de Vault. Variable: BROKER_VAULT_TOKEN.",
    )
    vault_allowed_paths: str = Field(
        default="",
        description="Comma-separated allowed path prefixes. Variable: BROKER_VAULT_ALLOWED_PATHS.",
    )
    vault_timeout: float = Field(
        default=15.0,
        ge=1.0,
        le=60.0,
        description="Timeout HTTP para Vault en segundos. Variable: BROKER_VAULT_TIMEOUT.",
    )

    # --- File backend ---
    file_allowed_dirs: str = Field(
        default="",
        description="Comma-separated allowed directory prefixes for file backend. Variable: BROKER_FILE_ALLOWED_DIRS.",
    )

    # --- Keychain backend ---
    keychain_enabled: bool = Field(
        default=True,
        description="Habilita el backend OS keychain (requiere 'keyring'). Variable: BROKER_KEYCHAIN_ENABLED.",
    )

    # --- HITL ---
    hitl_timeout_seconds: int = Field(
        default=120,
        ge=10,
        le=600,
        description="Segundos antes de que el prompt HITL expire. Variable: BROKER_HITL_TIMEOUT_SECONDS.",
    )
    hitl_auto_deny: bool = Field(
        default=False,
        description="Si true, deniega automaticamente todo reveal sin mostrar prompt. Variable: BROKER_HITL_AUTO_DENY.",
    )

    # --- run_with_creds ---
    default_command_timeout: int = Field(
        default=120,
        ge=5,
        le=3600,
        description="Timeout por defecto para run_with_creds en segundos. Variable: BROKER_DEFAULT_COMMAND_TIMEOUT.",
    )
    max_stdout_bytes: int = Field(
        default=65536,
        ge=1024,
        le=1048576,
        description="Max bytes de stdout a retornar. Variable: BROKER_MAX_STDOUT_BYTES.",
    )

    # --- Env backend ---
    env_allowed_prefixes: str = Field(
        default="",
        description="Comma-separated env var name prefixes allowed for env backend. Vacio = todas. Variable: BROKER_ENV_ALLOWED_PREFIXES.",
    )

    # --- SSH backend ---
    ssh_hosts: str = Field(
        default="",
        description=(
            "Comma-separated host aliases for SSH backend: 'alias:ip'. "
            "Ej: 'windows:100.73.65.63,wsl:100.115.230.9'. Variable: BROKER_SSH_HOSTS."
        ),
    )
    ssh_key_ref: str = Field(
        default="vault:secret/credential-broker/ssh-key#private",
        description=(
            "Credential_ref de la SSH key privada usada por el backend SSH. "
            "Se resuelve via cualquier backend (vault, env, file). Variable: BROKER_SSH_KEY_REF."
        ),
    )
    ssh_default_user: str = Field(
        default="german",
        description="Usuario SSH por defecto. Variable: BROKER_SSH_DEFAULT_USER.",
    )
    ssh_default_port: int = Field(
        default=22,
        ge=1,
        le=65535,
        description="Puerto SSH por defecto. Variable: BROKER_SSH_DEFAULT_PORT.",
    )
    ssh_timeout: float = Field(
        default=15.0,
        ge=1.0,
        le=120.0,
        description="Timeout SSH en segundos. Variable: BROKER_SSH_TIMEOUT.",
    )

    # --- LM Studio (process_with_local_llm) ---
    lmstudio_url: str = Field(
        default="http://host.docker.internal:1234/v1",
        description="URL base de LM Studio (compatible OpenAI). Variable: BROKER_LMSTUDIO_URL.",
    )
    lmstudio_model: str = Field(
        default="qwen3-8b",
        description="Modelo local por defecto para process_with_local_llm. Variable: BROKER_LMSTUDIO_MODEL.",
    )
    lmstudio_timeout: int = Field(
        default=120,
        ge=5,
        le=600,
        description="Timeout LM Studio en segundos. Variable: BROKER_LMSTUDIO_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["vault_url"] = self.vault_url
        base["keychain_enabled"] = self.keychain_enabled
        base["hitl_auto_deny"] = self.hitl_auto_deny
        base["ssh_hosts"] = self.ssh_hosts
        base["lmstudio_url"] = self.lmstudio_url
        base["lmstudio_model"] = self.lmstudio_model
        return base

    @property
    def vault_allowed_path_list(self) -> list[str]:
        if not self.vault_allowed_paths:
            return []
        return [p.strip() for p in self.vault_allowed_paths.split(",") if p.strip()]

    @property
    def file_allowed_dir_list(self) -> list[str]:
        if not self.file_allowed_dirs:
            return []
        return [p.strip() for p in self.file_allowed_dirs.split(",") if p.strip()]

    @property
    def env_allowed_prefix_list(self) -> list[str]:
        if not self.env_allowed_prefixes:
            return []
        return [p.strip() for p in self.env_allowed_prefixes.split(",") if p.strip()]

    @property
    def ssh_host_map(self) -> dict[str, str]:
        """Parsea 'windows:100.73.65.63,wsl:100.115.230.9' → {'windows': '100.73.65.63', ...}."""
        if not self.ssh_hosts:
            return {}
        result: dict[str, str] = {}
        for entry in self.ssh_hosts.split(","):
            entry = entry.strip()
            if ":" in entry:
                alias, ip = entry.split(":", 1)
                result[alias.strip()] = ip.strip()
        return result


settings = BrokerSettings()
