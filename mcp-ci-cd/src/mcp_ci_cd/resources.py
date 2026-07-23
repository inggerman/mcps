"""Resources de solo lectura para mcp-ci-cd."""

from __future__ import annotations

import json


def cicd_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-ci-cd",
            "version": "1.0.0",
            "project_path": ".",
            "default_lint_cmd": "uv run ruff check",
            "default_test_cmd": "uv run pytest",
            "default_deploy_cmd": "echo 'Despliegue simulado exitoso'",
        },
        indent=2,
        ensure_ascii=False,
    )


def cicd_pipeline_guide() -> str:
    return (
        "# Guia de pipelines CI/CD\n\n"
        "## Concepto\n"
        "- Pipeline: secuencia de stages (lint, test, build, deploy)\n"
        "- Cada stage debe pasar para continuar\n"
        "- Falla rapida (fail fast)\n\n"
        "## Stages tipicos\n"
        "1. Lint: ruff, flake8, eslint\n"
        "2. Test: pytest, jest, junit\n"
        "3. Build: docker build, mvn package\n"
        "4. Security: bandit, snyk, trivy\n"
        "5. Deploy: kubectl, helm, terraform\n\n"
        "## Mejores practicas\n"
        "- Pipeline reproducible\n"
        "- Cache de dependencias\n"
        "- Paralelizar stages independientes\n"
        "- Notificaciones en cada falla"
    )


def cicd_github_actions() -> str:
    return (
        "# GitHub Actions\n\n"
        "## Estructura\n"
        "```\n"
        ".github/workflows/ci.yml\n"
        "```\n\n"
        "## Ejemplo basico\n"
        "```yaml\n"
        "name: CI\n"
        "on: [push, pull_request]\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python@v5\n"
        "      - run: pip install uv\n"
        "      - run: uv run pytest\n"
        "```\n\n"
        "## Triggers\n"
        "- push: en ramas especificas\n"
        "- pull_request: en PRs\n"
        "- schedule: cron\n"
        "- workflow_dispatch: manual"
    )


def cicd_gitlab_ci() -> str:
    return (
        "# GitLab CI/CD\n\n"
        "## Estructura\n"
        "```\n"
        ".gitlab-ci.yml\n"
        "```\n\n"
        "## Ejemplo basico\n"
        "```yaml\n"
        "stages:\n"
        "  - lint\n"
        "  - test\n"
        "  - deploy\n\n"
        "lint:\n"
        "  stage: lint\n"
        "  script: ruff check .\n\n"
        "test:\n"
        "  stage: test\n"
        "  script: pytest\n\n"
        "deploy:\n"
        "  stage: deploy\n"
        "  script: echo 'Deploy'\n"
        "  only: main\n"
        "```\n\n"
        "## Features\n"
        "- Runners auto-escalables\n"
        "- Artifacts entre jobs\n"
        "- Environments (review, staging, prod)"
    )


def cicd_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- cicd_run_pipeline()\n"
        "- cicd_run_lint()\n"
        "- cicd_run_tests()\n"
        "- cicd_validate_config()\n"
        "- cicd_generate_workflow()\n\n"
        "## Variables .env\n"
        "- CICD_PROJECT_PATH\n"
        "- CICD_LINT_CMD\n"
        "- CICD_TEST_CMD\n"
        "- CICD_DEPLOY_CMD"
    )


def cicd_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno de CI/CD"},
                {"code": -32001, "description": "Stage failed: lint"},
                {"code": -32002, "description": "Stage failed: test"},
                {"code": -32003, "description": "Stage failed: deploy"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def cicd_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## Pipeline falla en lint\n"
        "- Verificar ruff/flake8 instalado\n"
        "- Revisar configuracion de linting\n"
        "- Corregir errores reportados\n\n"
        "## Pipeline falla en test\n"
        "- Ejecutar tests localmente\n"
        "- Verificar dependencias\n"
        "- Revisar fixtures\n\n"
        "## Pipeline falla en deploy\n"
        "- Verificar credenciales\n"
        "- Verificar target de despliegue\n"
        "- Revisar permisos\n\n"
        "## Pipeline lento\n"
        "- Cache de dependencias\n"
        "- Paralelizar jobs\n"
        "- Usar runners mas potentes"
    )


def cicd_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Ejemplo 1: Pipeline completo\n"
        "cicd_run_pipeline()\n\n"
        "## Ejemplo 2: Solo lint\n"
        'cicd_run_lint(cmd="ruff check src/")\n\n'
        "## Ejemplo 3: Solo tests\n"
        'cicd_run_tests(cmd="pytest -v")\n\n'
        "## Ejemplo 4: Generar workflow\n"
        'cicd_generate_workflow(platform="github")\n\n'
        "## Ejemplo 5: Validar config\n"
        "cicd_validate_config()"
    )


def cicd_security_scanning() -> str:
    return (
        "# Security Scanning en CI/CD\n\n"
        "## Tipos de scan\n"
        "- SAST: Static Application Security Testing\n"
        "- DAST: Dynamic Application Security Testing\n"
        "- SCA: Software Composition Analysis\n"
        "- Container scan: imagenes Docker\n\n"
        "## Tools\n"
        "- bandit: SAST para Python\n"
        "- snyk: SCA + container scan\n"
        "- trivy: container scan\n"
        "- semgrep: SAST multi-lenguaje\n\n"
        "## Integracion\n"
        "- Stage separado despues de test\n"
        "- Bloquear merge en criticals\n"
        "- Reportes como artifacts\n"
        "- Trend tracking"
    )


def cicd_artifacts() -> str:
    return (
        "# Artifacts en CI/CD\n\n"
        "## Concepto\n"
        "- Archivos generados durante el pipeline\n"
        "- Compartidos entre jobs\n"
        "- Retencion configurable\n\n"
        "## Tipos comunes\n"
        "- Test reports (JUnit XML, HTML)\n"
        "- Coverage reports\n"
        "- Build outputs (JAR, Docker image)\n"
        "- Security reports\n\n"
        "## Mejores practicas\n"
        "- Nombrar consistentemente\n"
        "- Versionar artifacts\n"
        "- Limpiar artifacts viejos\n"
        "- Usar artifact registry"
    )


def cicd_environments() -> str:
    return (
        "# Environments en CI/CD\n\n"
        "## Tipicos\n"
        "- dev: desarrollo local\n"
        "- staging: pre-produccion\n"
        "- production: produccion\n\n"
        "## Estrategias de despliegue\n"
        "- Rolling: reemplazo gradual\n"
        "- Blue-green: dos ambientes\n"
        "- Canary: despliegue gradual\n"
        "- Feature flags: control en runtime\n\n"
        "## Proteccion\n"
        "- Approval required para production\n"
        "- Restricted branches\n"
        "- Environment secrets separados\n"
        "- Audit trail de despliegues"
    )


def cicd_notifications() -> str:
    return (
        "# Notificaciones en CI/CD\n\n"
        "## Canales\n"
        "- Slack: webhooks\n"
        "- Email: SMTP\n"
        "- Teams: webhooks\n"
        "- PagerDuty: criticos\n\n"
        "## Eventos\n"
        "- Pipeline started\n"
        "- Pipeline success\n"
        "- Pipeline failed\n"
        "- Deployment completed\n\n"
        "## Mejores practicas\n"
        "- Notificar solo lo relevante\n"
        "- Incluir logs/reports\n"
        "- Diferenciar criticos vs info\n"
        "- Thread para seguimiento"
    )


def cicd_cache_strategy() -> str:
    return (
        "# Estrategia de cache en CI/CD\n\n"
        "## Que cachear\n"
        "- Dependencias (pip, npm, maven)\n"
        "- Build artifacts\n"
        "- Docker layers\n\n"
        "## Tools\n"
        "- actions/cache (GitHub)\n"
        "- GitLab cache\n"
        "- Docker BuildKit cache\n"
        "- Renovate para deps\n\n"
        "## Mejores practicas\n"
        "- Cache key basado en lock file\n"
        "- Restaurar cache antes de install\n"
        "- Guardar cache despues de install\n"
        "- Invalidar cache cuando sea necesario"
    )


def cicd_best_practices() -> str:
    return (
        "# Mejores practicas CI/CD\n\n"
        "1. Pipeline rapido (< 10 min)\n"
        "2. Fail fast en primera etapa\n"
        "3. Cache de dependencias\n"
        "4. Paralelizar jobs independientes\n"
        "5. Secrets en CI/CD, no en codigo\n"
        "6. Tests deterministicos\n"
        "7. Artifact versioning\n"
        "8. Environment protection\n"
        "9. Notificaciones relevantes\n"
        "10. Monitoreo de pipeline health"
    )


def cicd_deployment_strategies() -> str:
    return (
        "# Estrategias de despliegue\n\n"
        "## Rolling Update\n"
        "- Reemplazo gradual de pods/instancias\n"
        "- Cero downtime si hay replicas\n"
        "- Rollback automatico en fallo\n\n"
        "## Blue-Green\n"
        "- Dos ambientes identicos (blue y green)\n"
        "- Switch instantaneo de trafico\n"
        "- Rollback rapido (switch de vuelta)\n"
        "- Requiere mas recursos\n\n"
        "## Canary\n"
        "- Despliegue gradual a un subset\n"
        "- Monitorear metricas antes de continuar\n"
        "- Auto-rollback si metricas fallan\n"
        "- Ideal para cambios riesgosos\n\n"
        "## Feature Flags\n"
        "- Control en runtime sin redeploy\n"
        "- A/B testing\n"
        "- Rollback instantaneo (toggle off)\n"
        "- Requiere infraestructura de flags"
    )
