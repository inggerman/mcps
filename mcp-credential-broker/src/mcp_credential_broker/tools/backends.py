"""Backends de credenciales: Vault, env vars, archivos, OS keychain, SSH remoto.

Un credential_ref es un string con formato ``<backend>:<location>``:
  - ``vault:<path>[#<key>]``  — HashiCorp Vault KV-v2.
  - ``env:<VAR_NAME>``        — variable de entorno del proceso.
  - ``file:<path>``           — contenido de un archivo local.
  - ``keychain:<service>:<account>`` — OS keychain (Windows Credential Manager, etc.).
  - ``ssh:<host_alias>:<inner_ref>`` — SSH a host remoto, resuelve inner_ref alla.
    Ej: ``ssh:windows:env:GITHUB_TOKEN`` → SSH al Windows host, lee env var.

Ningun backend expone el valor en logs ni en excepciones.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from mcp_shared.errors import McpError, NotFoundError, ValidationError

from mcp_credential_broker.config import settings

# ---------------------------------------------------------------------------
# Resultado de resolucion
# ---------------------------------------------------------------------------


@dataclass
class ResolvedCredential:
    """Credencial resuelta. El valor NUNCA se incluye en repr ni logs."""

    ref: str
    backend: str
    value: str
    metadata: dict[str, Any]

    def safe_repr(self) -> dict[str, Any]:
        """Representacion segura para logs/respuestas — sin el valor."""
        return {
            "ref": self.ref,
            "backend": self.backend,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Parser de refs
# ---------------------------------------------------------------------------


def parse_ref(ref: str) -> tuple[str, str]:
    """Divide un credential_ref en (backend, location). Lanza ValidationError si malformado."""
    if ":" not in ref:
        raise ValidationError(field="credential_ref", message="Formato debe ser '<backend>:<location>'", value=ref)
    backend, location = ref.split(":", 1)
    backend = backend.lower().strip()
    if backend not in ("vault", "env", "file", "keychain", "ssh"):
        raise ValidationError(
            field="credential_ref",
            message=f"Backend '{backend}' no soportado. Use: vault, env, file, keychain, ssh.",
            value=ref,
        )
    if not location:
        raise ValidationError(field="credential_ref", message="Location vacia", value=ref)
    return backend, location


# ---------------------------------------------------------------------------
# Backend base
# ---------------------------------------------------------------------------


class CredentialBackend(ABC):
    """Interfaz para todos los backends de credenciales."""

    name: str = "base"

    @abstractmethod
    def resolve(self, location: str) -> ResolvedCredential:
        """Resuelve la credencial. Lanza McpError si no encuentra."""

    @abstractmethod
    def list_refs(self) -> list[dict[str, Any]]:
        """Lista las credenciales disponibles (sin valores)."""

    def store(self, location: str, value: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Almacena una credencial. No todos los backends soportan escritura."""
        raise ValidationError(field="backend", message=f"Backend '{self.name}' no soporta store.")


# ---------------------------------------------------------------------------
# Vault backend
# ---------------------------------------------------------------------------


class VaultBackend(CredentialBackend):
    name = "vault"

    def _client(self) -> httpx.Client:
        headers = {"Content-Type": "application/json"}
        if settings.vault_token:
            headers["X-Vault-Token"] = settings.vault_token
        return httpx.Client(
            base_url=settings.vault_url,
            headers=headers,
            timeout=settings.vault_timeout,
            verify=False,  # noqa: S501 — Vault interno HTTP en cluster
        )

    def _check_path(self, path: str) -> None:
        allowed = settings.vault_allowed_path_list
        if not allowed:
            return
        for prefix in allowed:
            if path.startswith(prefix):
                return
        raise ValidationError(field="vault_path", message=f"Path '{path}' fuera de la allowlist.", value=path)

    def resolve(self, location: str) -> ResolvedCredential:
        # location = "secret/gitea/devin-token#token"  (path#key)
        if "#" in location:
            path, key = location.rsplit("#", 1)
        else:
            path, key = location, ""
        self._check_path(path)
        try:
            with self._client() as client:
                resp = client.get(f"/v1/{path}/data")
                if resp.status_code == 404:
                    raise NotFoundError(resource="vault_secret", identifier=path) from None
                resp.raise_for_status()
                data = resp.json().get("data", {}).get("data", {})
                if not key:
                    # Sin key explicita: si hay un solo campo, devolverlo; si hay varios, error.
                    if len(data) == 1:
                        value = next(iter(data.values()))
                    else:
                        raise ValidationError(
                            field="vault_key",
                            message=f"Path '{path}' tiene {len(data)} claves. Especifique con '#key'.",
                            value=location,
                        )
                else:
                    if key not in data:
                        raise NotFoundError(resource="vault_key", identifier=f"{path}#{key}") from None
                    value = data[key]
                return ResolvedCredential(
                    ref=f"vault:{location}",
                    backend="vault",
                    value=str(value),
                    metadata={"path": path, "key": key or "(auto)", "num_keys": len(data)},
                )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise McpError("Vault: token invalido o ausente.") from exc
            raise McpError(f"Vault API error: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise McpError(f"Vault: error de red — {exc}") from exc

    def list_refs(self) -> list[dict[str, Any]]:
        # Lista solo los paths raiz de cada mount (metadata listing recursivo es costoso).
        refs: list[dict[str, Any]] = []
        try:
            with self._client() as client:
                resp = client.get("/v1/sys/mounts")
                resp.raise_for_status()
                mounts = resp.json().get("data", {})
                for mount_path, mount_info in mounts.items():
                    if mount_info.get("type") == "kv" and mount_info.get("options", {}).get("version") == "2":
                        refs.append({
                            "ref": f"vault:{mount_path}",
                            "backend": "vault",
                            "type": "kv-v2-mount",
                            "metadata": {"mount": mount_path},
                        })
        except (httpx.HTTPError, McpError):
            pass  # Vault inalcanzable — no listamos
        return refs


# ---------------------------------------------------------------------------
# Env backend
# ---------------------------------------------------------------------------


class EnvBackend(CredentialBackend):
    name = "env"

    def _check_allowed(self, var_name: str) -> None:
        prefixes = settings.env_allowed_prefix_list
        if not prefixes:
            return
        for prefix in prefixes:
            if var_name.startswith(prefix):
                return
        raise ValidationError(
            field="env_var",
            message=f"Variable '{var_name}' fuera de los prefijos permitidos.",
            value=var_name,
        )

    def resolve(self, location: str) -> ResolvedCredential:
        var_name = location.strip()
        self._check_allowed(var_name)
        if var_name not in os.environ:
            raise NotFoundError(resource="env_var", identifier=var_name) from None
        return ResolvedCredential(
            ref=f"env:{var_name}",
            backend="env",
            value=os.environ[var_name],
            metadata={"var_name": var_name},
        )

    def list_refs(self) -> list[dict[str, Any]]:
        prefixes = settings.env_allowed_prefix_list
        refs: list[dict[str, Any]] = []
        for var_name in sorted(os.environ):
            if prefixes and not any(var_name.startswith(p) for p in prefixes):
                continue
            # Heuristica: solo listar vars que parezcan credenciales
            lower = var_name.lower()
            if any(kw in lower for kw in ("token", "pass", "key", "secret", "cred", "api")):
                refs.append({
                    "ref": f"env:{var_name}",
                    "backend": "env",
                    "type": "env_var",
                    "metadata": {"var_name": var_name},
                })
        return refs


# ---------------------------------------------------------------------------
# File backend
# ---------------------------------------------------------------------------


class FileBackend(CredentialBackend):
    name = "file"

    def _check_allowed(self, file_path: str) -> None:
        allowed = settings.file_allowed_dir_list
        if not allowed:
            return
        resolved = str(Path(file_path).expanduser().resolve())
        for prefix in allowed:
            if resolved.startswith(str(Path(prefix).resolve())):
                return
        raise ValidationError(
            field="file_path",
            message=f"Ruta '{file_path}' fuera de los directorios permitidos.",
            value=file_path,
        )

    def resolve(self, location: str) -> ResolvedCredential:
        file_path = location.strip()
        self._check_allowed(file_path)
        path = Path(file_path).expanduser()
        if not path.is_file():
            raise NotFoundError(resource="file", identifier=file_path) from None
        try:
            content = path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError as exc:
            raise McpError(f"Error leyendo archivo: {exc}") from exc
        return ResolvedCredential(
            ref=f"file:{location}",
            backend="file",
            value=content,
            metadata={"path": str(path), "size_bytes": path.stat().st_size},
        )

    def list_refs(self) -> list[dict[str, Any]]:
        # No listamos archivos arbitrariamente — requerir path explicito.
        return []


# ---------------------------------------------------------------------------
# Keychain backend (OS credential store via keyring)
# ---------------------------------------------------------------------------


class KeychainBackend(CredentialBackend):
    name = "keychain"

    def _get_keyring(self) -> Any:
        if not settings.keychain_enabled:
            raise McpError("Backend keychain deshabilitado (BROKER_KEYCHAIN_ENABLED=false).")
        try:
            import keyring  # type: ignore[import-not-found]
        except ImportError:
            raise McpError("Libreria 'keyring' no instalada. Instala con: pip install keyring") from None
        return keyring

    def resolve(self, location: str) -> ResolvedCredential:
        # location = "service:account"
        if ":" not in location:
            raise ValidationError(
                field="keychain_location",
                message="Formato debe ser 'service:account'",
                value=location,
            )
        service, account = location.split(":", 1)
        keyring = self._get_keyring()
        value = keyring.get_password(service, account)
        if value is None:
            raise NotFoundError(resource="keychain_entry", identifier=f"{service}:{account}") from None
        return ResolvedCredential(
            ref=f"keychain:{location}",
            backend="keychain",
            value=value,
            metadata={"service": service, "account": account},
        )

    def list_refs(self) -> list[dict[str, Any]]:
        # keyring no soporta listing nativo en todos los backends.
        return []

    def store(self, location: str, value: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if ":" not in location:
            raise ValidationError(
                field="keychain_location",
                message="Formato debe ser 'service:account'",
                value=location,
            )
        service, account = location.split(":", 1)
        keyring = self._get_keyring()
        keyring.set_password(service, account, value)
        return {"stored": True, "ref": f"keychain:{location}", "service": service, "account": account}


# ---------------------------------------------------------------------------
# SSH backend — resuelve credenciales en host remoto via SSH
# ---------------------------------------------------------------------------


class SSHBackend(CredentialBackend):
    """Backend que SSHa a un host remoto y resuelve un inner_ref alla.

    Ref format: ``ssh:<host_alias>:<inner_ref>``
    Ej: ``ssh:windows:env:GITHUB_TOKEN`` → SSH al Windows host, lee env var.

    La SSH key se resuelve via ``settings.ssh_key_ref`` (default: Vault).
    Los hosts permitidos se configuran en ``settings.ssh_hosts``.
    """

    name = "ssh"

    def _resolve_host(self, alias: str) -> str:
        host_map = settings.ssh_host_map
        if not host_map:
            raise ValidationError(
                field="ssh_hosts",
                message="No hay hosts SSH configurados (BROKER_SSH_HOSTS vacio).",
                value=alias,
            )
        if alias not in host_map:
            raise ValidationError(
                field="ssh_host",
                message=f"Host '{alias}' no esta en la allowlist. Configurados: {list(host_map)}",
                value=alias,
            )
        return host_map[alias]

    def _get_ssh_key(self) -> str:
        """Resuelve la SSH key privada via el backend configurado."""
        try:
            cred = resolve_ref(settings.ssh_key_ref)
            return cred.value
        except (McpError, ValidationError, NotFoundError) as exc:
            raise McpError(
                f"No se pudo resolver la SSH key desde '{settings.ssh_key_ref}': {exc}",
            ) from exc

    def _connect(self, host_ip: str) -> Any:
        """Abre conexion SSH al host. Retorna el cliente paramiko."""
        try:
            import paramiko  # type: ignore[import-not-found]
        except ImportError:
            raise McpError("Libreria 'paramiko' no instalada. Instala con: pip install paramiko") from None

        key_str = self._get_ssh_key()
        try:
            pkey = paramiko.Ed25519Key.from_private_key(
                __import__("io").StringIO(key_str),
            )
        except paramiko.SSHException:
            try:
                pkey = paramiko.RSAKey.from_private_key(
                    __import__("io").StringIO(key_str),
                )
            except paramiko.SSHException as exc:
                raise McpError(f"SSH key invalida o formato no soportado: {exc}") from exc

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # noqa: S507 — hosts en allowlist
        try:
            client.connect(
                hostname=host_ip,
                port=settings.ssh_default_port,
                username=settings.ssh_default_user,
                pkey=pkey,
                timeout=settings.ssh_timeout,
                allow_agent=False,
                look_for_keys=False,
            )
        except Exception as exc:
            raise McpError(f"SSH: no se pudo conectar a {host_ip}:{settings.ssh_default_port} — {exc}") from exc
        return client

    def resolve(self, location: str) -> ResolvedCredential:
        # location = "host_alias:inner_ref"
        if ":" not in location:
            raise ValidationError(
                field="ssh_location",
                message="Formato debe ser 'host_alias:inner_ref' (ej: 'windows:env:TOKEN')",
                value=location,
            )
        alias, inner_ref = location.split(":", 1)
        alias = alias.strip()
        host_ip = self._resolve_host(alias)

        # Resolver el inner_ref remotamente via SSH
        inner_backend, inner_location = parse_ref(inner_ref)
        if inner_backend == "ssh":
            raise ValidationError(
                field="ssh_nested",
                message="SSH anidado no soportado (ssh:ssh:...).",
                value=location,
            )

        client = self._connect(host_ip)
        try:
            value = self._resolve_remote(client, inner_backend, inner_location)
        finally:
            client.close()

        return ResolvedCredential(
            ref=f"ssh:{location}",
            backend="ssh",
            value=value,
            metadata={
                "ssh_host": alias,
                "ssh_ip": host_ip,
                "inner_backend": inner_backend,
                "inner_ref": inner_ref,
            },
        )

    def _resolve_remote(self, client: Any, backend: str, location: str) -> str:
        """Ejecuta comandos en el host remoto para resolver la credencial."""
        if backend == "env":
            # Leer env var remota: 'echo $VAR' en Unix, 'echo %VAR%' en Windows
            # Detectamos si es Windows o Unix por el shell
            cmd = f'echo "${location}"'  # Unix-style (WSL, Linux)
            value = self._exec_remote(client, cmd).strip()
            if not value or value == "${location}":
                # Intentar Windows-style
                cmd = f"echo %{location}%"
                value = self._exec_remote(client, cmd).strip()
                if value == f"%{location}%":
                    raise NotFoundError(resource="ssh_env_var", identifier=location) from None
            return value

        if backend == "file":
            # Leer archivo remoto via cat
            cmd = f"cat '{location}'"
            try:
                value = self._exec_remote(client, cmd)
            except McpError:
                raise NotFoundError(resource="ssh_file", identifier=location) from None
            return value.strip()

        if backend == "vault":
            # En el host remoto, usar el cliente vault si existe
            # location = "path#key"
            if "#" in location:
                path, key = location.rsplit("#", 1)
            else:
                path, key = location, ""
            cmd = f"vault kv get -field={key or 'value'} {path} 2>/dev/null"
            value = self._exec_remote(client, cmd).strip()
            if not value:
                raise NotFoundError(resource="ssh_vault", identifier=location) from None
            return value

        if backend == "keychain":
            # Keychain remoto no soportado directamente via SSH
            raise McpError(
                "Backend keychain remoto via SSH no soportado. "
                "Use 'ssh:host:cmd:...' para ejecutar un comando que lea el keychain.",
            )

        raise ValidationError(
            field="ssh_inner_backend",
            message=f"Backend '{backend}' no soportado via SSH remoto.",
            value=backend,
        )

    def _exec_remote(self, client: Any, command: str) -> str:
        """Ejecuta un comando via SSH y retorna stdout."""
        try:
            _stdin, stdout, stderr = client.exec_command(command, timeout=settings.ssh_timeout)
            output = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0 and not output:
                raise McpError(f"SSH command failed (exit {exit_code}): {err.strip()}")
            return output
        except McpError:
            raise
        except Exception as exc:
            raise McpError(f"SSH exec error: {exc}") from exc

    def list_refs(self) -> list[dict[str, Any]]:
        """Lista los hosts SSH configurados (sin conectar)."""
        refs: list[dict[str, Any]] = []
        for alias, ip in settings.ssh_host_map.items():
            refs.append({
                "ref": f"ssh:{alias}",
                "backend": "ssh",
                "type": "ssh-host",
                "metadata": {"alias": alias, "ip": ip},
            })
        return refs


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


_BACKENDS: dict[str, CredentialBackend] = {
    "vault": VaultBackend(),
    "env": EnvBackend(),
    "file": FileBackend(),
    "keychain": KeychainBackend(),
    "ssh": SSHBackend(),
}


def get_backend(name: str) -> CredentialBackend:
    if name not in _BACKENDS:
        raise ValidationError(field="backend", message=f"Backend '{name}' no registrado.", value=name)
    return _BACKENDS[name]


def resolve_ref(ref: str) -> ResolvedCredential:
    """Resuelve un credential_ref completo usando el backend apropiado."""
    backend_name, location = parse_ref(ref)
    backend = get_backend(backend_name)
    return backend.resolve(location)


def list_all_refs(backend_filter: str | None = None) -> list[dict[str, Any]]:
    """Lista todas las credenciales disponibles (sin valores)."""
    refs: list[dict[str, Any]] = []
    names = [backend_filter] if backend_filter else list(_BACKENDS)
    for name in names:
        if name not in _BACKENDS:
            continue
        try:
            refs.extend(_BACKENDS[name].list_refs())
        except McpError:
            pass  # Backend no disponible — saltar
    return refs
