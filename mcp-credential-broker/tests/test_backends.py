"""Tests de backends de credenciales."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from mcp_credential_broker.tools.backends import (
    EnvBackend,
    FileBackend,
    KeychainBackend,
    VaultBackend,
    parse_ref,
    resolve_ref,
)
from mcp_shared.errors import McpError, NotFoundError, ValidationError


class TestParseRef:
    def test_vault_ref(self) -> None:
        backend, location = parse_ref("vault:secret/gitea#token")
        assert backend == "vault"
        assert location == "secret/gitea#token"

    def test_env_ref(self) -> None:
        backend, location = parse_ref("env:GITHUB_TOKEN")
        assert backend == "env"
        assert location == "GITHUB_TOKEN"

    def test_file_ref(self) -> None:
        backend, location = parse_ref("file:~/.ssh/id_rsa")
        assert backend == "file"
        assert location == "~/.ssh/id_rsa"

    def test_keychain_ref(self) -> None:
        backend, location = parse_ref("keychain:portal-x:admin")
        assert backend == "keychain"
        assert location == "portal-x:admin"

    def test_invalid_backend(self) -> None:
        with pytest.raises(ValidationError):
            parse_ref("unknown:foo")

    def test_no_colon(self) -> None:
        with pytest.raises(ValidationError):
            parse_ref("vault")


class TestEnvBackend:
    def test_resolve_existing_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_CRED_VAR", "secret123")
        backend = EnvBackend()
        cred = backend.resolve("TEST_CRED_VAR")
        assert cred.value == "secret123"
        assert cred.backend == "env"
        assert "secret123" not in cred.safe_repr()["ref"]

    def test_resolve_missing_var(self) -> None:
        backend = EnvBackend()
        with pytest.raises(NotFoundError):
            backend.resolve("NONEXISTENT_VAR_12345")

    def test_list_filters_credential_like(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_API_TOKEN", "x")
        monkeypatch.setenv("RANDOM_VAR", "y")
        backend = EnvBackend()
        refs = backend.list_refs()
        ref_names = [r["ref"] for r in refs]
        assert "env:MY_API_TOKEN" in ref_names
        assert "env:RANDOM_VAR" not in ref_names


class TestFileBackend:
    def test_resolve_existing_file(self, tmp_path) -> None:
        cred_file = tmp_path / "token.txt"
        cred_file.write_text("my-secret-token\n")
        backend = FileBackend()
        cred = backend.resolve(str(cred_file))
        assert cred.value == "my-secret-token"
        assert cred.backend == "file"

    def test_resolve_missing_file(self) -> None:
        backend = FileBackend()
        with pytest.raises(NotFoundError):
            backend.resolve("/nonexistent/path/12345.txt")


class TestVaultBackend:
    def test_resolve_missing_path_raises_not_found(self) -> None:
        backend = VaultBackend()
        with patch.object(backend, "_client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.get.return_value.status_code = 404
            mock_client.get.return_value.raise_for_status.side_effect = Exception("not found")
            with pytest.raises(NotFoundError):
                backend.resolve("secret/nonexistent#token")


class TestKeychainBackend:
    def test_resolve_disabled(self) -> None:
        from mcp_credential_broker.config import settings

        with patch.object(type(settings), "keychain_enabled", True, create=True):
            pass  # settings is a singleton; test via mock
        backend = KeychainBackend()
        # Sin keyring instalado o deshabilitado -> McpError
        with patch("mcp_credential_broker.config.settings") as mock_settings:
            mock_settings.keychain_enabled = False
            with pytest.raises(McpError):
                backend.resolve("service:account")


class TestResolveRef:
    def test_resolve_env_via_ref(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BROKER_TEST_CRED", "val123")
        cred = resolve_ref("env:BROKER_TEST_CRED")
        assert cred.value == "val123"
        assert cred.backend == "env"


class TestSSHBackend:
    """Tests del backend SSH (con paramiko mockeado)."""

    def test_parse_ssh_ref(self) -> None:
        backend, location = parse_ref("ssh:windows:env:TOKEN")
        assert backend == "ssh"
        assert location == "windows:env:TOKEN"

    def test_resolve_host_not_in_allowlist_raises(self) -> None:
        from mcp_credential_broker.tools.backends import SSHBackend

        with patch("mcp_credential_broker.tools.backends.settings") as mock_settings:
            mock_settings.ssh_host_map = {"windows": "100.73.65.63"}
            mock_settings.ssh_hosts = "windows:100.73.65.63"
            backend = SSHBackend()
            with pytest.raises(ValidationError):
                backend._resolve_host("unknown")

    def test_resolve_host_no_hosts_configured_raises(self) -> None:
        from mcp_credential_broker.tools.backends import SSHBackend

        with patch("mcp_credential_broker.tools.backends.settings") as mock_settings:
            mock_settings.ssh_host_map = {}
            mock_settings.ssh_hosts = ""
            backend = SSHBackend()
            with pytest.raises(ValidationError):
                backend._resolve_host("windows")

    def test_resolve_ssh_env_remote(self) -> None:
        from mcp_credential_broker.tools.backends import SSHBackend

        backend = SSHBackend()
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"remote-secret-value\n"
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        with patch("mcp_credential_broker.tools.backends.settings") as mock_settings:
            mock_settings.ssh_host_map = {"windows": "100.73.65.63"}
            mock_settings.ssh_default_port = 22
            mock_settings.ssh_default_user = "german"
            mock_settings.ssh_timeout = 15.0
            with patch.object(backend, "_connect", return_value=mock_client):
                cred = backend.resolve("windows:env:MY_REMOTE_TOKEN")
        assert cred.value == "remote-secret-value"
        assert cred.backend == "ssh"
        assert cred.metadata["ssh_host"] == "windows"
        assert cred.metadata["inner_backend"] == "env"
        # El valor NO esta en la metadata
        assert "remote-secret-value" not in str(cred.metadata)

    def test_resolve_ssh_file_remote(self) -> None:
        from mcp_credential_broker.tools.backends import SSHBackend

        backend = SSHBackend()
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"file-content-here\n"
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        with patch("mcp_credential_broker.tools.backends.settings") as mock_settings:
            mock_settings.ssh_host_map = {"wsl": "100.115.230.9"}
            mock_settings.ssh_timeout = 15.0
            with patch.object(backend, "_connect", return_value=mock_client):
                cred = backend.resolve("wsl:file:/etc/hostname")
        assert cred.value == "file-content-here"
        assert cred.backend == "ssh"

    def test_ssh_nested_raises(self) -> None:
        from mcp_credential_broker.tools.backends import SSHBackend

        backend = SSHBackend()
        with patch("mcp_credential_broker.tools.backends.settings") as mock_settings:
            mock_settings.ssh_host_map = {"windows": "100.73.65.63"}
            with pytest.raises(ValidationError):
                backend.resolve("windows:ssh:other:env:TOKEN")

    def test_list_ssh_hosts(self) -> None:
        from mcp_credential_broker.tools.backends import SSHBackend

        with patch("mcp_credential_broker.tools.backends.settings") as mock_settings:
            mock_settings.ssh_host_map = {"windows": "100.73.65.63", "wsl": "100.115.230.9"}
            backend = SSHBackend()
            refs = backend.list_refs()
            ref_names = [r["ref"] for r in refs]
            assert "ssh:windows" in ref_names
            assert "ssh:wsl" in ref_names
