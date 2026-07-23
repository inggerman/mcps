"""Resources de solo lectura para mcp-snyk."""

from __future__ import annotations

import json


def snyk_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-snyk",
            "version": "1.0.0",
            "project_path": ".",
            "has_token": False,
        },
        indent=2,
        ensure_ascii=False,
    )


def snyk_basics() -> str:
    return (
        "# Snyk Basics\n\n"
        "## Que es Snyk\n"
        "- Plataforma de seguridad para developers\n"
        "- SAST: Static Application Security Testing\n"
        "- SCA: Software Composition Analysis\n"
        "- IaC: Infrastructure as Code scanning\n"
        "- Container: container image scanning\n\n"
        "## Productos\n"
        "- Snyk Open Source: dependencias\n"
        "- Snyk Code: SAST\n"
        "- Snyk IaC: Terraform, CloudFormation\n"
        "- Snyk Container: Docker images\n"
        "- Snyk AppRisk: risk prioritization\n\n"
        "## CLI vs API\n"
        "- CLI: integracion local y CI/CD\n"
        "- API: integracion programatica\n"
        "- Web UI: dashboard y gestion\n"
        "- IDE plugins: VS Code, IntelliJ\n\n"
        "## Integraciones\n"
        "- GitHub, GitLab, Bitbucket\n"
        "- Jenkins, GitHub Actions, CircleCI\n"
        "- Kubernetes, Docker, Terraform Cloud\n"
        "- Jira, Slack, ServiceNow"
    )


def snyk_best_practices() -> str:
    return (
        "# Snyk Best Practices\n\n"
        "## Escaneo\n"
        "- Escanear en cada PR\n"
        "- Escanear antes de deploy\n"
        "- Escanear imagenes en build time\n"
        "- Escanear IaC antes de apply\n\n"
        "## Priorizacion\n"
        "- Fix por severidad (critical/high primero)\n"
        "- Considerar exploitability\n"
        "- Usar Snyk Priority Score\n"
        "- Reachability analysis\n\n"
        "## Remediation\n"
        "- Upgrade dependencias afectadas\n"
        "- Usar patches de Snyk si no hay upgrade\n"
        "- Ignore con justificacion y expiry\n"
        "- Documentar excepciones\n\n"
        "## CI/CD\n"
        "- Fail build en critical vulns\n"
        "- Gate en merge to main\n"
        "- Monitor continuo post-deploy\n"
        "- Auto-PR con Snyk Fix PRs\n\n"
        "## Policy\n"
        "- .snyk policy file\n"
        "- Org-level policies\n"
        "- Ignorar con expiry date\n"
        "- Revisar ignores periodicamente"
    )


def snyk_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- snyk_run_test()\n"
        "- snyk_auth(api_token)\n"
        "- snyk_monitor()\n"
        "- snyk_code_test()\n"
        "- snyk_iac_test()\n"
        "- snyk_container_test(image)\n"
        "- snyk_ignore(issue_id)\n"
        "- snyk_policy()\n"
        "- snyk_projects()\n"
        "- snyk_org_list()\n"
        "- snyk_test_severity_filter(severity)\n"
        "- snyk_test_file(file_path)\n"
        "- snyk_dependency_tree()\n"
        "- snyk_wizard()\n"
        "- snyk_log4shell()\n\n"
        "## Variables .env\n"
        "- SNYK_PROJECT_PATH\n"
        "- SNYK_API_TOKEN\n"
        "- SNYK_MCP_TRANSPORT\n"
        "- SNYK_MCP_PORT"
    )


def snyk_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "Snyk CLI no encontrado"},
                {"code": -32002, "description": "Error de autenticacion"},
                {"code": -32003, "description": "Error ejecutando snyk"},
                {"code": -32004, "description": "API token no configurado"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def snyk_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## Snyk CLI no encontrado\n"
        "- Instalar: npm install -g snyk\n"
        "- Verificar PATH\n"
        "- Usar modo mock para testing\n\n"
        "## Error de autenticacion\n"
        "- Verificar SNYK_API_TOKEN\n"
        "- Ejecutar snyk auth\n"
        "- Verificar expiry del token\n"
        "- Verificar permisos de org\n\n"
        "## No se encuentran vulnerabilidades\n"
        "- Verificar que exista package.json/lockfile\n"
        "- Verificar que el proyecto tenga dependencias\n"
        "- Probar con --all-projects\n"
        "- Verificar que el manifest este actualizado\n\n"
        "## Error en container test\n"
        "- Verificar que la imagen exista localmente\n"
        "- Verificar permisos de Docker\n"
        "- Verificar registry access\n"
        "- Probar con --platform linux/amd64\n\n"
        "## IaC test no encuentra archivos\n"
        "- Verificar directorio de trabajo\n"
        "- Verificar extensiones (.tf, .yaml, .json)\n"
        "- Usar --file para archivo especifico"
    )


def snyk_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Test basico\n"
        "snyk_run_test()\n\n"
        "## Code test (SAST)\n"
        "snyk_code_test()\n\n"
        "## IaC test\n"
        "snyk_iac_test()\n\n"
        "## Container test\n"
        'snyk_container_test(image="myapp:latest")\n\n'
        "## Filtrar por severidad\n"
        'snyk_test_severity_filter(severity="high")\n\n'
        "## Ignorar vulnerabilidad\n"
        'snyk_ignore(issue_id="SNYK-JS-LODASH-590103")\n\n'
        "## Listar proyectos\n"
        "snyk_projects()"
    )


def snyk_oss_guide() -> str:
    return (
        "# Snyk Open Source (SCA)\n\n"
        "## Que hace\n"
        "- Escanea dependencias (npm, pip, maven, etc.)\n"
        "- Compara con vulnerability database\n"
        "- Reporta vulnerabilidades con CVE/CWE\n"
        "- Sugiere fixes y upgrades\n\n"
        "## Lenguajes soportados\n"
        "- JavaScript/TypeScript (npm, yarn)\n"
        "- Python (pip, poetry)\n"
        "- Java (Maven, Gradle)\n"
        "- Go (modules)\n"
        "- .NET (NuGet)\n"
        "- Ruby (gems)\n"
        "- PHP (composer)\n"
        "- Scala (sbt)\n\n"
        "## Comandos\n"
        "- snyk test: escanea y reporta\n"
        "- snyk monitor: registro continuo\n"
        "- snyk wizard: crea policy file\n"
        "- snyk fix: auto-fix PRs\n\n"
        "## Salida\n"
        "- Vulnerabilidad: title, severity, package\n"
        "- CVE: identificador unico\n"
        "- Fix: version sugerida\n"
        "- Paths: como se llega a la dependencia\n"
        "- Exploit maturity: proof-of-concept, exploited"
    )


def snyk_code_guide() -> str:
    return (
        "# Snyk Code (SAST)\n\n"
        "## Que hace\n"
        "- Analiza codigo fuente estaticamente\n"
        "- Detecta vulnerabilidades de seguridad\n"
        "- AI-powered analysis\n"
        "- False positive reduction\n\n"
        "## Lenguajes soportados\n"
        "- JavaScript/TypeScript\n"
        "- Python\n"
        "- Java\n"
        "- Go\n"
        "- C/C++\n"
        "- C#/.NET\n"
        "- PHP\n"
        "- Ruby\n"
        "- Scala\n"
        "- Kotlin\n\n"
        "## Tipos de hallazgos\n"
        "- Injection: SQL, Command, XSS\n"
        "- Path Traversal\n"
        "- Hardcoded Secrets\n"
        "- Insecure Crypto\n"
        "- SSRF\n"
        "- Deserialization\n"
        "- Open Redirect\n\n"
        "## Comandos\n"
        "- snyk code test: escanea codigo\n"
        "- snyk code --report: reporta a Snyk\n\n"
        "## Mejores practicas\n"
        "- Escanear en cada commit\n"
        "- Usar IDE plugin para feedback rapido\n"
        "- Priorizar por data flow\n"
        "- Fix issues antes de merge"
    )


def snyk_iac_guide() -> str:
    return (
        "# Snyk IaC\n\n"
        "## Que hace\n"
        "- Escanea Terraform, CloudFormation, ARM\n"
        "- Detecta misconfigurations\n"
        "- Compliance: CIS, PCI-DSS, GDPR\n"
        "- Cloud-specific rules\n\n"
        "## Soportado\n"
        "- Terraform (.tf)\n"
        "- AWS CloudFormation (.json/.yaml)\n"
        "- Azure ARM templates\n"
        "- Kubernetes manifests (.yaml)\n"
        "- Helm charts\n\n"
        "## Comandos\n"
        "- snyk iac test: escanea IaC files\n"
        "- snyk iac --report: reporta a Snyk\n\n"
        "## Reglas comunes\n"
        "- Security groups abiertos (0.0.0.0/0)\n"
        "- S3 buckets publicos\n"
        "- IAM policies demasiado permisivas\n"
        "- Sin encryption en reposo\n"
        "- Sin encryption en transito\n"
        "- Logging deshabilitado\n\n"
        "## Mejores practicas\n"
        "- Escanear antes de terraform apply\n"
        "- Integrar en CI/CD pipeline\n"
        "- Usar policy as code (OPA)\n"
        "- Fix antes de deploy"
    )


def snyk_container_guide() -> str:
    return (
        "# Snyk Container\n\n"
        "## Que hace\n"
        "- Escanea Docker images\n"
        "- Detecta vulnerabilidades en OS packages\n"
        "- Detecta vulnerabilidades en app dependencies\n"
        "- Dockerfile analysis\n\n"
        "## Comandos\n"
        "- snyk container test <image>\n"
        "- snyk container monitor <image>\n\n"
        "## Que escanea\n"
        "- OS packages (apt, apk, yum)\n"
        "- Language-specific dependencies\n"
        "- Dockerfile best practices\n"
        "- Base image recommendations\n\n"
        "## Salida\n"
        "- Vulnerabilidades por capa\n"
        "- Severity: critical, high, medium, low\n"
        "- Package y version afectada\n"
        "- Fix version sugerida\n"
        "- Base image alternatives\n\n"
        "## Mejores practicas\n"
        "- Escanear en build time\n"
        "- Usar base images oficiales\n"
        "- Minimizar layers y tamaño\n"
        "- Usar distroless cuando sea posible\n"
        "- Escanear antes de push al registry"
    )


def snyk_severity_guide() -> str:
    return (
        "# Snyk Severity Levels\n\n"
        "## Niveles\n"
        "- Critical: explotable, impacto severo\n"
        "- High: explotable, impacto significativo\n"
        "- Medium: posible explotacion, impacto moderado\n"
        "- Low: impacto limitado\n"
        "- Info: informativo, no vulnerable\n\n"
        "## CVSS Scoring\n"
        "- CVSS 3.1: standard de scoring\n"
        "- 0.0-3.9: Low\n"
        "- 4.0-6.9: Medium\n"
        "- 7.0-8.9: High\n"
        "- 9.0-10.0: Critical\n\n"
        "## Priorizacion\n"
        "- Snyk Priority Score (1-1000)\n"
        "- Considera: severity, reachability, exploitability\n"
        "- Malicious packages: prioridad maxima\n"
        "- Reachable vs unreachable code\n\n"
        "## Filtros CLI\n"
        "- --severity-threshold=high\n"
        "- --fail-on=all|upgradable|patchable\n"
        "- --ignore-policy: ignorar .snyk file\n\n"
        "## SLAs sugeridos\n"
        "- Critical: 7 dias\n"
        "- High: 30 dias\n"
        "- Medium: 90 dias\n"
        "- Low: 180 dias"
    )


def snyk_policy_guide() -> str:
    return (
        "# Snyk Policy File (.snyk)\n\n"
        "## Estructura\n"
        "```yaml\n"
        "version: v1.25.0\n"
        "ignore: {}\n"
        "patch: {}\n"
        "```\n\n"
        "## Ignore\n"
        "```yaml\n"
        "ignore:\n"
        "  'npm:lodash:20180101':\n"
        "    - '*':\n"
        "        reason: No fix available\n"
        "        expires: '2026-12-31'\n"
        "```\n\n"
        "## Patch\n"
        "```yaml\n"
        "patch:\n"
        "  'npm:express:20180101':\n"
        "    - express > 4.0.0:\n"
        "        patch: snyk/snyk-patch:express:20180101\n"
        "```\n\n"
        "## Comandos\n"
        "- snyk wizard: crear interactivamente\n"
        "- snyk policy: mostrar policy actual\n"
        "- snyk ignore <id>: ignorar issue\n\n"
        "## Mejores practicas\n"
        "- Commitear .snyk en el repo\n"
        "- Revisar ignores periodicamente\n"
        "- Usar expiry dates en ignores\n"
        "- Documentar reason en cada ignore\n"
        "- No ignorar critical sin aprobacion"
    )


def snyk_ci_cd() -> str:
    return (
        "# Snyk CI/CD Integration\n\n"
        "## GitHub Actions\n"
        "```yaml\n"
        "- name: Snyk Test\n"
        "  uses: snyk/actions@v0.4.0\n"
        "  with:\n"
        "    command: test\n"
        "  env:\n"
        "    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}\n"
        "```\n\n"
        "## GitLab CI\n"
        "```yaml\n"
        "snyk:\n"
        "  image: snyk/snyk:docker\n"
        "  script:\n"
        "    - snyk test --json > snyk-report.json\n"
        "  artifacts:\n"
        "    paths: [snyk-report.json]\n"
        "```\n\n"
        "## Jenkins\n"
        "- Snyk Security plugin\n"
        "- Pipeline step: snykSecurity\n"
        "- Fail build on vulnerabilities\n\n"
        "## Mejores practicas\n"
        "- Usar secrets para SNYK_TOKEN\n"
        "- Fail en critical/high\n"
        "- Generar reporte como artifact\n"
        "- PR comments con resultados\n"
        "- Monitor para continuous scanning\n"
        "- Auto-fix PRs con Snyk Fix\n\n"
        "## Gates\n"
        "- Block merge en critical\n"
        "- Warn en high\n"
        "- Info en medium/low\n"
        "- Customizable por proyecto"
    )


def snyk_api_guide() -> str:
    return (
        "# Snyk API Guide\n\n"
        "## Autenticacion\n"
        "- API token en header: Authorization: token <API_KEY>\n"
        "- Obtener token desde Snyk Account Settings\n"
        "- Service accounts para CI/CD\n\n"
        "## Endpoints comunes\n"
        "- GET /v1/orgs: listar organizaciones\n"
        "- GET /v1/org/{orgId}/projects: listar proyectos\n"
        "- POST /v1/org/{orgId}/project/{projectId}/issues: listar issues\n"
        "- POST /v1/test/npm: test package\n"
        "- POST /v1/test/gradle: test gradle project\n\n"
        "## Rate Limits\n"
        "- 2000 requests por minuto (org)\n"
        "- 400 requests por minuto (user)\n"
        "- Usar pagination para resultados grandes\n\n"
        "## Webhooks\n"
        "- Notificacion en tiempo real\n"
        "- Eventos: new issue, fixed issue\n"
        "- Configurar desde Snyk UI\n"
        "- Payload: project, issue, severity\n\n"
        "## SDKs\n"
        "- snyk-python-sdk (comunidad)\n"
        "- snyk-node-sdk (comunidad)\n"
        "- REST API directa con httpx/requests\n\n"
        "## Mejores practicas\n"
        "- Usar service accounts\n"
        "- Rotar tokens regularmente\n"
        "- Almacenar en secrets manager\n"
        "- Loggear API calls para auditoria"
    )
