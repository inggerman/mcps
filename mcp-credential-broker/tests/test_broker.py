"""Tests del broker: run_with_creds, reveal_secret, list_credentials, store_credential."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from mcp_credential_broker.tools.broker import (
    list_credentials,
    process_with_local_llm,
    reveal_secret,
    run_with_creds,
    store_credential,
)
from mcp_shared.errors import McpError, NotFoundError, ValidationError


class TestRunWithCreds:
    def test_run_echo_with_env_credential(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """El comando recibe la credencial como env var, no como argumento visible."""
        monkeypatch.setenv("BROKER_TEST_PASS", "s3cr3t-val")
        # Usar python -c para leer la env var (cross-platform, no depende de shell syntax)
        result = run_with_creds(
            command='python -c "import os; print(os.environ[\'CRED\'])"',
            credential_ref="env:BROKER_TEST_PASS",
            inject_as="CRED",
        )
        assert result["exit_code"] == 0
        # stdout contiene el valor (el comando lo imprime), pero el valor no esta en la metadata
        assert "s3cr3t-val" in result["stdout"]
        # La respuesta safe_repr no incluye el valor
        assert "s3cr3t-val" not in str(result["credential"])

    def test_run_command_exit_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BROKER_TEST_PASS", "x")
        result = run_with_creds(
            command="exit 42",
            credential_ref="env:BROKER_TEST_PASS",
        )
        assert result["exit_code"] == 42

    def test_run_empty_command_raises(self) -> None:
        with pytest.raises(ValidationError):
            run_with_creds(command="", credential_ref="env:FOO")

    def test_run_missing_credential_raises(self) -> None:
        with pytest.raises(NotFoundError):
            run_with_creds(
                command="echo hi",
                credential_ref="env:NONEXISTENT_VAR_99999",
            )


class TestRevealSecret:
    def test_reveal_denied_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BROKER_TEST_PASS", "secret-val")
        with patch("mcp_credential_broker.tools.broker.confirm_reveal", return_value=False):
            result = reveal_secret("env:BROKER_TEST_PASS", reason="test")
        assert result["revealed"] is False
        assert result["to"] == "denied"
        # El valor NO esta en el resultado
        assert "secret-val" not in str(result)

    def test_reveal_approved_returns_true_but_no_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BROKER_TEST_PASS", "secret-val")
        with patch("mcp_credential_broker.tools.broker.confirm_reveal", return_value=True):
            with patch(
                "mcp_credential_broker.tools.broker.print_value_to_user",
                return_value={"revealed": True, "to": "terminal", "ref": "env:BROKER_TEST_PASS"},
            ):
                result = reveal_secret("env:BROKER_TEST_PASS", reason="test")
        assert result["revealed"] is True
        assert result["to"] == "terminal"
        # El valor NO esta en el resultado que ve el LLM
        assert "secret-val" not in str(result)


class TestListCredentials:
    def test_list_env_credentials(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_API_KEY", "x")
        refs = list_credentials(backend="env")
        ref_names = [r["ref"] for r in refs]
        assert "env:MY_API_KEY" in ref_names

    def test_list_invalid_backend_raises(self) -> None:
        with pytest.raises(ValidationError):
            list_credentials(backend="nonexistent")


class TestStoreCredential:
    def test_store_requires_source(self) -> None:
        with pytest.raises(ValidationError):
            store_credential(ref="keychain:svc:acct")

    def test_store_both_sources_raises(self) -> None:
        with pytest.raises(ValidationError):
            store_credential(ref="keychain:svc:acct", from_env="X", from_file="Y")

    def test_store_from_missing_env_raises(self) -> None:
        with pytest.raises(NotFoundError):
            store_credential(ref="keychain:svc:acct", from_env="NONEXISTENT_99999")


class TestProcessWithLocalLLM:
    """Tests de process_with_local_llm (LM Studio mockeado)."""

    def test_process_returns_response_without_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BROKER_TEST_SECRET", "super-secret-123")
        # Mock httpx.Client para simular LM Studio
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Analizado: el token es valido"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        with patch("mcp_credential_broker.tools.broker.httpx.Client", return_value=mock_client):
            result = process_with_local_llm(
                prompt="Analiza este token",
                credential_ref="env:BROKER_TEST_SECRET",
            )
        assert "Analizado" in result["response"]
        assert result["model"] == "qwen3-8b"
        # El valor sensible NO esta en el resultado que ve el LLM
        assert "super-secret-123" not in str(result)

    def test_process_reasoning_content_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """qwen3-8b en modo thinking deja content="" y pone el output en reasoning_content."""
        monkeypatch.setenv("BROKER_TEST_SECRET", "super-secret-123")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {
                "content": "",
                "reasoning_content": "Analizado via reasoning: el token es valido"
            }}]
        }
        mock_response.raise_for_status.return_value = None
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        with patch("mcp_credential_broker.tools.broker.httpx.Client", return_value=mock_client):
            result = process_with_local_llm(
                prompt="Analiza este token",
                credential_ref="env:BROKER_TEST_SECRET",
            )
        assert "Analizado via reasoning" in result["response"]
        assert "super-secret-123" not in str(result)

    def test_process_lmstudio_down_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BROKER_TEST_SECRET", "val")
        import httpx

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.side_effect = httpx.ConnectError("Connection refused")

        with patch("mcp_credential_broker.tools.broker.httpx.Client", return_value=mock_client):
            with pytest.raises(McpError):
                process_with_local_llm(
                    prompt="test",
                    credential_ref="env:BROKER_TEST_SECRET",
                )

    def test_process_empty_prompt_raises(self) -> None:
        with pytest.raises(ValidationError):
            process_with_local_llm(prompt="", credential_ref="env:FOO")

    def test_process_missing_credential_raises(self) -> None:
        with pytest.raises(NotFoundError):
            process_with_local_llm(
                prompt="test",
                credential_ref="env:NONEXISTENT_99999",
            )
