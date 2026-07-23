"""
Lógica de negocio de mcp-git.

Ejecuta comandos de Git locales utilizando subprocess.
Implementa el flujo de commit en dos pasos (prepare_commit + confirm_commit).
"""

from __future__ import annotations

import secrets
import subprocess
from pathlib import Path
from typing import Any

from mcp_shared.errors import NotFoundError, ValidationError

# Almacenamiento en memoria para commits pendientes
# mapea token -> mensaje_de_commit
_PENDING_COMMITS: dict[str, str] = {}


def _run_git(args: list[str], repo_path: Path) -> str:
    """
    Ejecuta un comando git y retorna su salida.

    Args:
        args: Argumentos a pasar a git (ej: ['status', '--porcelain']).
        repo_path: Directorio de trabajo.

    Raises:
        ValidationError: Si el comando falla.
    """
    cmd = ["git", *args]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.stdout.rstrip("\r\n")
    except subprocess.CalledProcessError as exc:
        raise ValidationError(
            field="git_command",
            message=f"Git falló: {exc.stderr.strip()}",
        ) from exc
    except FileNotFoundError as exc:
        raise ValidationError(
            field="git",
            message="El ejecutable 'git' no se encontró en el sistema.",
        ) from exc


# ---------------------------------------------------------------------------
# Tools de Información
# ---------------------------------------------------------------------------


def get_git_status(repo_path: Path) -> dict[str, Any]:
    """Retorna el estado de git (branch actual, cambios, etc)."""
    status_porcelain = _run_git(["status", "--porcelain"], repo_path)
    branch = _run_git(["branch", "--show-current"], repo_path)

    changes = []
    if status_porcelain:
        for line in status_porcelain.splitlines():
            if len(line) >= 3:
                state = line[0:2]
                file = line[3:]
                changes.append({"state": state, "file": file})

    return {
        "branch": branch,
        "changes": changes,
        "is_clean": len(changes) == 0,
        "raw_status": status_porcelain,
    }


def get_git_diff(repo_path: Path, staged: bool = False, file_path: str = "") -> str:
    """Retorna el diff de cambios. Si staged=True, muestra lo que se va a commitear."""
    args = ["diff"]
    if staged:
        args.append("--staged")
    if file_path:
        args.append("--")
        args.append(file_path)

    return _run_git(args, repo_path)


def get_git_log(repo_path: Path, max_count: int = 10) -> str:
    """Retorna el historial de commits recientes."""
    args = ["log", f"-n{max_count}", "--oneline", "--decorate"]
    return _run_git(args, repo_path)


# ---------------------------------------------------------------------------
# Tools de Stage (Preparación)
# ---------------------------------------------------------------------------


def git_add(repo_path: Path, files: list[str]) -> str:
    """Agrega archivos al stage."""
    if not files:
        raise ValidationError(field="files", message="Debes especificar al menos un archivo o '.'")
    args = ["add", *files]
    _run_git(args, repo_path)
    return f"Se agregaron al stage: {', '.join(files)}"


def git_reset(repo_path: Path, files: list[str] | None = None) -> str:
    """Remueve archivos del stage (unstage)."""
    args = ["reset", "HEAD"]
    if files:
        args.extend(files)
        msg = f"Se removieron del stage: {', '.join(files)}"
    else:
        msg = "Se removieron todos los archivos del stage."

    _run_git(args, repo_path)
    return msg


# ---------------------------------------------------------------------------
# Flujo de Commit Seguro (Dos Pasos)
# ---------------------------------------------------------------------------


def prepare_commit(repo_path: Path, message: str) -> dict[str, Any]:
    """
    Paso 1: Prepara un commit y genera un token de confirmación.

    Verifica que haya cambios en el stage y devuelve un diff junto con
    el token que debe usarse para confirmar la operación.
    """
    if not message or len(message.strip()) < 3:
        raise ValidationError(field="message", message="El mensaje de commit debe ser descriptivo.")

    # Verificar si hay algo en stage
    staged_diff = get_git_diff(repo_path, staged=True)
    if not staged_diff:
        raise ValidationError(
            field="staged_files",
            message="No hay cambios en el stage para commitear. Usa git_add primero.",
        )

    token = "TOK-" + secrets.token_hex(4).upper()
    _PENDING_COMMITS[token] = message.strip()

    return {
        "status": "pending_confirmation",
        "token": token,
        "message": message,
        "staged_diff": staged_diff,
        "instruction": (
            "ATENCIÓN: El commit NO se ha realizado aún. "
            f"Debes pedirle al usuario confirmación y luego llamar al tool 'confirm_commit' con el token '{token}'."
        ),
    }


def confirm_commit(repo_path: Path, token: str) -> dict[str, Any]:
    """
    Paso 2: Ejecuta el commit utilizando un token válido.
    """
    if token not in _PENDING_COMMITS:
        raise NotFoundError(resource="pending_commit", identifier=token)

    message = _PENDING_COMMITS.pop(token)

    # Ejecutar commit
    try:
        # En Windows es mejor pasar el mensaje como un archivo temporal si tiene saltos de línea,
        # o usar múltiples -m
        lines = message.splitlines()
        args = ["commit"]
        for line in lines:
            if line.strip():
                args.extend(["-m", line])

        output = _run_git(args, repo_path)
        commit_hash = _run_git(["log", "-1", "--format=%H"], repo_path)

        return {
            "status": "success",
            "commit_hash": commit_hash,
            "output": output,
        }
    except Exception as exc:
        # Si falla, restaurar el token para reintentos
        _PENDING_COMMITS[token] = message
        raise exc


# ---------------------------------------------------------------------------
# Branches & Sync
# ---------------------------------------------------------------------------


def git_branch(repo_path: Path, branch_name: str, create: bool = False) -> str:
    """Cambia de rama o crea una nueva."""
    if create:
        _run_git(["checkout", "-b", branch_name], repo_path)
        return f"Creada y cambiada a la rama: {branch_name}"
    else:
        _run_git(["checkout", branch_name], repo_path)
        return f"Cambiada a la rama: {branch_name}"


def git_pull(repo_path: Path) -> str:
    """Hace pull de los cambios remotos."""
    return _run_git(["pull"], repo_path)


def git_push(repo_path: Path, force: bool = False, allow_force: bool = False) -> str:
    """Hace push al remoto. force requiere configuración allow_force_push."""
    args = ["push"]
    if force:
        if not allow_force:
            raise ValidationError(
                field="force",
                message="Push --force está deshabilitado en la configuración del servidor (GIT_ALLOW_FORCE_PUSH=false).",
            )
        args.append("--force-with-lease")

    branch = _run_git(["branch", "--show-current"], repo_path)
    # Por si no tiene tracking
    try:
        return _run_git(args, repo_path)
    except Exception:
        # Intento con push origin HEAD
        args.extend(["origin", branch])
        return _run_git(args, repo_path)


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def git_branch_list(repo_path: Path) -> dict[str, Any]:
    """Lista todas las ramas locales y remotas."""
    output = _run_git(["branch", "-a", "--format=%(refname:short) %(objectname:short)"], repo_path)
    branches = []
    for line in output.splitlines():
        if line.strip():
            parts = line.strip().split()
            branches.append({"name": parts[0], "hash": parts[1] if len(parts) > 1 else ""})
    return {"branches": branches, "count": len(branches)}


def git_branch_delete(repo_path: Path, branch_name: str) -> str:
    """Elimina una rama local."""
    if not branch_name or not branch_name.strip():
        raise ValidationError(field="branch_name", message="El nombre de la rama no puede estar vacio.")
    _run_git(["branch", "-d", branch_name], repo_path)
    return f"Rama '{branch_name}' eliminada."


def git_merge(repo_path: Path, branch_name: str) -> str:
    """Hace merge de una rama en la rama actual."""
    if not branch_name or not branch_name.strip():
        raise ValidationError(field="branch_name", message="El nombre de la rama no puede estar vacio.")
    return _run_git(["merge", branch_name], repo_path)


def git_stash(repo_path: Path, message: str = "") -> str:
    """Guarda cambios temporales en stash."""
    args = ["stash", "push"]
    if message:
        args.extend(["-m", message])
    return _run_git(args, repo_path)


def git_stash_list(repo_path: Path) -> list[dict[str, Any]]:
    """Lista todos los stashes."""
    output = _run_git(["stash", "list"], repo_path)
    stashes = []
    if output:
        for i, line in enumerate(output.splitlines()):
            stashes.append({"index": i, "description": line.strip()})
    return stashes


def git_stash_apply(repo_path: Path, index: int = 0) -> str:
    """Aplica un stash sin eliminarlo."""
    return _run_git(["stash", "apply", f"stash@{{{index}}}"], repo_path)


def git_stash_drop(repo_path: Path, index: int = 0) -> str:
    """Elimina un stash."""
    return _run_git(["stash", "drop", f"stash@{{{index}}}"], repo_path)


def git_tag(repo_path: Path, name: str, message: str = "") -> str:
    """Crea un tag anotado."""
    if not name or not name.strip():
        raise ValidationError(field="name", message="El nombre del tag no puede estar vacio.")
    args = ["tag", "-a", name]
    if message:
        args.extend(["-m", message])
    else:
        args.extend(["-m", f"Tag {name}"])
    _run_git(args, repo_path)
    return f"Tag '{name}' creado."


def git_tag_list(repo_path: Path) -> list[dict[str, Any]]:
    """Lista todos los tags."""
    output = _run_git(["tag", "-l", "--format=%(refname:short) %(objectname:short)"], repo_path)
    tags = []
    for line in output.splitlines():
        if line.strip():
            parts = line.strip().split()
            tags.append({"name": parts[0], "hash": parts[1] if len(parts) > 1 else ""})
    return tags


def git_tag_delete(repo_path: Path, name: str) -> str:
    """Elimina un tag."""
    if not name or not name.strip():
        raise ValidationError(field="name", message="El nombre del tag no puede estar vacio.")
    _run_git(["tag", "-d", name], repo_path)
    return f"Tag '{name}' eliminado."


def git_remote_list(repo_path: Path) -> list[dict[str, Any]]:
    """Lista los remotos configurados."""
    output = _run_git(["remote", "-v"], repo_path)
    remotes: dict[str, dict[str, Any]] = {}
    for line in output.splitlines():
        if line.strip():
            parts = line.strip().split()
            if len(parts) >= 2:
                name = parts[0]
                url = parts[1]
                direction = parts[2] if len(parts) > 2 else ""
                if name not in remotes:
                    remotes[name] = {"name": name, "fetch_url": "", "push_url": ""}
                if "(fetch)" in direction:
                    remotes[name]["fetch_url"] = url
                elif "(push)" in direction:
                    remotes[name]["push_url"] = url
    return list(remotes.values())


def git_remote_add(repo_path: Path, name: str, url: str) -> str:
    """Anade un remoto."""
    if not name or not name.strip():
        raise ValidationError(field="name", message="El nombre del remoto no puede estar vacio.")
    if not url or not url.strip():
        raise ValidationError(field="url", message="La URL del remoto no puede estar vacia.")
    _run_git(["remote", "add", name, url], repo_path)
    return f"Remoto '{name}' anadido con URL: {url}"
