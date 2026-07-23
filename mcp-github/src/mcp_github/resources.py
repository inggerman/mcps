"""Resources de solo lectura para mcp-github.

Expone metadatos, guias y consejos sobre la API de GitHub
como URIs accesibles para el modelo a traves de `@mcp.resource`.
"""

from __future__ import annotations

import json

from mcp_github.config import settings


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


def github_api_endpoints() -> str:
    """Endpoints principales de la API REST de GitHub."""
    return json.dumps(
        {
            "endpoints": [
                {"method": "GET", "path": "/repos/{owner}/{repo}/issues", "description": "Listar issues"},
                {"method": "POST", "path": "/repos/{owner}/{repo}/issues", "description": "Crear issue"},
                {"method": "GET", "path": "/repos/{owner}/{repo}/issues/{number}", "description": "Obtener issue"},
                {"method": "POST", "path": "/repos/{owner}/{repo}/issues/{number}/comments", "description": "Comentar issue"},
                {"method": "POST", "path": "/repos/{owner}/{repo}/pulls", "description": "Crear PR"},
                {"method": "GET", "path": "/repos/{owner}/{repo}/pulls/{number}", "description": "Obtener PR"},
                {"method": "GET", "path": "/repos/{owner}/{repo}/pulls/{number}/files", "description": "Archivos del PR"},
                {"method": "GET", "path": "/repos/{owner}/{repo}/branches", "description": "Listar branches"},
                {"method": "GET", "path": "/repos/{owner}/{repo}/commits", "description": "Listar commits"},
                {"method": "GET", "path": "/repos/{owner}/{repo}/contents/{path}", "description": "Contenido de archivo"},
                {"method": "GET", "path": "/users/{username}", "description": "Info de usuario"},
                {"method": "GET", "path": "/repos/{owner}/{repo}", "description": "Info del repo"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def github_authentication_guide() -> str:
    """Guia de autenticacion con GitHub."""
    return (
        "# Autenticacion GitHub\n\n"
        "- Crear un Personal Access Token (PAT) en GitHub Settings > Developer settings.\n"
        "- Permisos recomendados: repo, read:org, read:user.\n"
        "- Configurar GITHUB_TOKEN en .env o variable de entorno.\n"
        "- El token se envia como Bearer en el header Authorization.\n"
        "- Para GitHub Enterprise: configurar GITHUB_API_URL con la URL base."
    )


def issue_management_tips() -> str:
    """Consejos de gestion de issues."""
    return (
        "# Gestion de issues\n\n"
        "- Usa titulos descriptivos y concisos.\n"
        "- Incluye pasos para reproducir en el body.\n"
        "- Usa labels para categorizar (bug, feature, enhancement, etc).\n"
        "- Asigna personas con assignees.\n"
        "- Vincula issues con PRs usando 'Closes #123'.\n"
        "- Usa milestones para agrupar issues por sprint/release."
    )


def pull_request_best_practices() -> str:
    """Mejores practicas para Pull Requests."""
    return (
        "# Mejores practicas PR\n\n"
        "- Manten los PRs pequenos y enfocados (max ~400 lineas).\n"
        "- Escribe una descripcion clara: que cambia y por que.\n"
        "- Usa templates de PR si el repo los tiene.\n"
        "- Solicita review de al menos una persona.\n"
        "- Resuelve conflicts antes de merge.\n"
        "- Usa squash merge para historial limpio.\n"
        "- Elimina la branch despues del merge."
    )


def github_rate_limits() -> str:
    """Informacion sobre rate limits de GitHub API."""
    return (
        "# Rate limits GitHub API\n\n"
        "- Autenticado: 5,000 requests/hora.\n"
        "- Sin autenticar: 60 requests/hora.\n"
        "- GitHub Apps: 5,000/hora por instalacion.\n"
        "- Search API: 30 requests/minuto.\n"
        "- Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset.\n"
        "- HTTP 403 con 'rate limit exceeded' cuando se excede."
    )


def github_configuration() -> str:
    """Configuracion actual del servidor GitHub."""
    return json.dumps(
        {
            "api_url": settings.api_url,
            "owner": settings.owner or "(no configurado)",
            "repo": settings.repo or "(no configurado)",
            "timeout_seconds": settings.timeout_seconds,
            "has_token": bool(settings.token),
        },
        indent=2,
        ensure_ascii=False,
    )


def common_github_workflows() -> str:
    """Flujos de trabajo comunes con GitHub."""
    return (
        "# Flujos comunes\n\n"
        "- **Crear issue**: github_create_issue(title, body, labels)\n"
        "- **Ver issue**: github_get_issue(issue_number)\n"
        "- **Comentar**: github_add_issue_comment(issue_number, body)\n"
        "- **Crear PR**: github_create_pull_request(title, head, base, body)\n"
        "- **Ver diff PR**: github_get_pull_request_diff(pull_number)\n"
        "- **Listar issues**: github_list_issues(state='open')\n"
        "- **Listar branches**: github_list_branches()\n"
        "- **Listar commits**: github_list_commits(sha='main')\n"
        "- **Leer archivo**: github_get_file_content(path)\n"
        "- **Info repo**: github_get_repo_info()"
    )


def github_error_codes() -> str:
    """Codigos de error comunes de GitHub API."""
    return json.dumps(
        {
            "errors": [
                {"code": 401, "description": "No autenticado o token invalido"},
                {"code": 403, "description": "Prohibido o rate limit excedido"},
                {"code": 404, "description": "Recurso no encontrado"},
                {"code": 410, "description": "Recurso eliminado permanentemente"},
                {"code": 422, "description": "Validacion fallida (campo invalido)"},
                {"code": 451, "description": "Eliminado por razones legales"},
                {"code": 500, "description": "Error interno de GitHub"},
                {"code": 503, "description": "Servicio no disponible temporalmente"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def github_markdown_syntax() -> str:
    """Sintaxis Markdown soportada en GitHub."""
    return (
        "# Markdown en GitHub\n\n"
        "- **Negrita**: `**texto**`\n"
        "- *Cursiva*: `*texto*`\n"
        "- ~~Tachado~~: `~~texto~~`\n"
        "- Codigo inline: `` `codigo` ``\n"
        "- Bloque de codigo: ``` ```lang ... ``` ```\n"
        "- Enlaces: `[texto](url)`\n"
        "- Listas: `- item` o `1. item`\n"
        "- Tablas: `| col1 | col2 |`\n"
        "- Menciones: `@usuario`\n"
        "- Referencias: `#123` (issue), `@usuario/repo`\n"
        "- Task lists: `- [ ] pendiente` / `- [x] hecho`"
    )


def github_branch_strategy() -> str:
    """Estrategias de branching comunes."""
    return (
        "# Estrategias de branching\n\n"
        "- **Git Flow**: main, develop, feature/*, release/*, hotfix/*\n"
        "- **GitHub Flow**: main + feature branches (simple)\n"
        "- **Trunk-based**: main + branches cortas (CI intensivo)\n"
        "- Convencion: `feature/descripcion`, `fix/bug-desc`, `chore/task`\n"
        "- Protege main con branch protection rules.\n"
        "- Requiere PR review antes de merge."
    )


def github_security_tips() -> str:
    """Consejos de seguridad para GitHub."""
    return (
        "# Seguridad GitHub\n\n"
        "- Nunca commitear tokens o secretos.\n"
        "- Usa GitHub Secrets para CI/CD.\n"
        "- Configura .gitignore correctamente.\n"
        "- Revisa dependencias con Dependabot.\n"
        "- Habilita 2FA en tu cuenta.\n"
        "- Usa tokens con permisos minimos necesarios.\n"
        "- Rota tokens periodicamente.\n"
        "- Revisa el audit log de la organizacion."
    )


def github_release_guide() -> str:
    """Guia de releases en GitHub."""
    return (
        "# Releases GitHub\n\n"
        "- Usa Semantic Versioning: MAJOR.MINOR.PATCH (ej: 1.2.3).\n"
        "- Crea tags antes de releases: `git tag v1.0.0`.\n"
        "- Usa GitHub Releases para changelogs.\n"
        "- Incluye binarios o assets en el release.\n"
        "- Auto-genera release notes con GitHub.\n"
        "- Vincula issues cerrados con 'Closes #123'."
    )


def example_create_issue() -> str:
    """Ejemplo de creacion de issue."""
    return (
        "# Ejemplo: github_create_issue\n\n"
        "```\n"
        "github_create_issue(\n"
        "    title='Bug: login falla en Safari',\n"
        "    body='## Descripcion\\n\\nEl login falla cuando...\\n\\n## Pasos\\n1. Abrir Safari\\n2. ...',\n"
        "    labels=['bug', 'frontend']\n"
        ")\n"
        "```\n"
        "Retorna: number, url, title"
    )


def example_create_pr() -> str:
    """Ejemplo de creacion de PR."""
    return (
        "# Ejemplo: github_create_pull_request\n\n"
        "```\n"
        "github_create_pull_request(\n"
        "    title='Fix: corregir login en Safari',\n"
        "    head='fix/safari-login',\n"
        "    base='main',\n"
        "    body='## Cambios\\n\\n- Corregido manejo de cookies en Safari\\n\\nCloses #42'\n"
        ")\n"
        "```\n"
        "Retorna: number, url, title, state"
    )
