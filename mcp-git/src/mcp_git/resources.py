"""Resources de solo lectura para mcp-git."""

from __future__ import annotations

import json


def git_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-git",
            "version": "1.0.0",
            "repo_path": ".",
            "default_branch": "main",
            "allow_force_push": False,
        },
        indent=2,
        ensure_ascii=False,
    )


def git_workflow_guide() -> str:
    return (
        "# Guia de workflow Git\n\n"
        "## Flujo de commit (2 pasos)\n"
        "1. git_add(files) — agrega archivos al stage\n"
        "2. prepare_commit(message) — genera token y muestra diff\n"
        "3. confirm_commit(token) — aplica el commit\n\n"
        "## Flujo de branch\n"
        "1. git_branch(name, create=True) — crea nueva rama\n"
        "2. ... trabajar ...\n"
        "3. git_push() — sube al remoto\n\n"
        "## Sync\n"
        "- git_pull() — descarga cambios remotos\n"
        "- git_push(force=False) — sube cambios"
    )


def git_commit_best_practices() -> str:
    return (
        "# Mejores practicas de commit\n\n"
        "1. Mensajes descriptivos (>3 chars)\n"
        "2. Usar conventional commits: feat:, fix:, docs:, refactor:\n"
        "3. Un commit = un cambio logico\n"
        "4. No commitear archivos generados\n"
        "5. Verificar diff antes de confirmar\n"
        "6. Commits pequenos y frecuentes\n"
        "7. No usar --force en ramas compartidas"
    )


def git_branching_strategy() -> str:
    return (
        "# Estrategia de branching\n\n"
        "## Git Flow\n"
        "- main: produccion\n"
        "- develop: integracion\n"
        "- feature/*: nuevas features\n"
        "- hotfix/*: fixes urgentes\n\n"
        "## Trunk-based\n"
        "- main + feature branches cortas\n"
        "- Integracion continua\n\n"
        "## GitHub Flow\n"
        "- main + PRs\n"
        "- Deploy desde main"
    )


def git_troubleshooting() -> str:
    return (
        "# Troubleshooting Git\n\n"
        "## Conflictos de merge\n"
        "- git status para ver archivos en conflicto\n"
        "- Editar archivos, resolver conflictos\n"
        "- git_add archivos resueltos\n"
        "- confirm_commit\n\n"
        "## Commit accidental\n"
        "- git_reset HEAD~1 (mantiene cambios)\n"
        "- git_reset --hard HEAD~1 (descarta cambios)\n\n"
        "## Branch equivocada\n"
        "- git_reset para unstage\n"
        "- git_branch correcta\n"
        "- git_add + commit"
    )


def git_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- get_git_status()\n"
        "- get_git_diff(staged, file_path)\n"
        "- get_git_log(max_count)\n"
        "- git_add(files)\n"
        "- git_reset(files)\n"
        "- git_branch(name, create)\n"
        "- prepare_commit(message)\n"
        "- confirm_commit(token)\n"
        "- git_pull()\n"
        "- git_push(force)\n\n"
        "## Variables .env\n"
        "- GIT_REPO_PATH\n"
        "- GIT_DEFAULT_BRANCH\n"
        "- GIT_ALLOW_FORCE_PUSH"
    )


def git_security_guide() -> str:
    return (
        "# Guia de seguridad Git\n\n"
        "## Proteccion\n"
        "- allow_force_push=false por defecto\n"
        "- Commit en 2 pasos evita commits accidentales\n"
        "- Token expira tras uso\n\n"
        "## Riesgos\n"
        "- No commitear secrets (.env, keys)\n"
        "- Usar .gitignore\n"
        "- Revisar diff antes de confirmar\n"
        "- --force-with-lease mas seguro que --force"
    )


def git_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno de git"},
                {"code": -32001, "description": "NotFoundError: token no encontrado"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def git_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Ejemplo 1: Commit simple\n"
        "git_add(['README.md'])\n"
        "prepare_commit('Update README')\n"
        "confirm_commit('TOK-XXXX')\n\n"
        "## Ejemplo 2: Nueva rama\n"
        "git_branch('feature/login', create=True)\n\n"
        "## Ejemplo 3: Ver cambios\n"
        "get_git_diff(staged=True)"
    )


def git_merge_guide() -> str:
    return (
        "# Guia de merge\n\n"
        "## Merge normal\n"
        "git_branch('main')\n"
        "git_merge('feature/x')\n\n"
        "## Rebase\n"
        "git_rebase('main')\n"
        "git_push(force=True)\n\n"
        "## Conflictos\n"
        "1. Identificar archivos en conflicto\n"
        "2. Resolver manualmente\n"
        "3. git_add archivos resueltos\n"
        "4. confirm_commit"
    )


def git_stash_guide() -> str:
    return (
        "# Guia de stash\n\n"
        "## Guardar cambios temporales\n"
        "git_stash(message)\n\n"
        "## Listar stashes\n"
        "git_stash_list()\n\n"
        "## Aplicar stash\n"
        "git_stash_apply(index)\n\n"
        "## Drop stash\n"
        "git_stash_drop(index)"
    )


def git_tag_guide() -> str:
    return (
        "# Guia de tags\n\n"
        "## Crear tag\n"
        "git_tag(name, message)\n\n"
        "## Listar tags\n"
        "git_tag_list()\n\n"
        "## Eliminar tag\n"
        "git_tag_delete(name)\n\n"
        "## Push tags\n"
        "git_push_tags()"
    )


def git_remote_guide() -> str:
    return (
        "# Gestion de remotos\n\n"
        "## Listar remotos\n"
        "git_remote_list()\n\n"
        "## Anadir remoto\n"
        "git_remote_add(name, url)\n\n"
        "## Eliminar remoto\n"
        "git_remote_remove(name)"
    )


def git_rebase_guide() -> str:
    return (
        "# Guia de rebase\n\n"
        "## Rebase interactivo\n"
        "git_rebase(branch)\n\n"
        "## Abortar rebase\n"
        "git_rebase_abort()\n\n"
        "## Continuar rebase\n"
        "git_rebase_continue()\n\n"
        "## Mejores practicas\n"
        "- No rebase ramas compartidas\n"
        "- Usa --force-with-lease despues de rebase\n"
        "- Rebase antes de merge para historial limpio"
    )


def git_cherry_pick_guide() -> str:
    return (
        "# Guia de cherry-pick\n\n"
        "## Aplicar commit especifico\n"
        "git_cherry_pick(commit_hash)\n\n"
        "## Abortar cherry-pick\n"
        "git_cherry_pick_abort()\n\n"
        "## Continuar cherry-pick\n"
        "git_cherry_pick_continue()\n\n"
        "## Casos de uso\n"
        "- Aplicar un bugfix en otra rama\n"
        "- Mover un commit a la rama correcta"
    )
