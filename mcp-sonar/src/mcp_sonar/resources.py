"""Resources de solo lectura para mcp-sonar."""

from __future__ import annotations

import json


def sonar_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-sonar",
            "version": "1.0.0",
            "host_url": "http://localhost:9000",
            "has_token": False,
        },
        indent=2,
        ensure_ascii=False,
    )


def sonar_basics() -> str:
    return (
        "# SonarQube Basics\n\n"
        "## Que es SonarQube\n"
        "- Plataforma de analisis de calidad de codigo\n"
        "- Static analysis: bugs, vulnerabilities, code smells\n"
        "- Technical debt tracking\n"
        "- Coverage y duplicacion\n\n"
        "## Productos\n"
        "- SonarQube: self-hosted\n"
        "- SonarCloud: SaaS\n"
        "- SonarLint: IDE plugin\n"
        "- Sonar Scanner: CLI para scanning\n\n"
        "## Conceptos\n"
        "- Project: proyecto a escanear\n"
        "- Component: modulo, paquete, archivo\n"
        "- Issue: bug, vulnerability, code smell\n"
        "- Metric: medida cuantitativa (coverage, debt)\n"
        "- Quality Gate: conjunto de condiciones\n"
        "- Quality Profile: set de reglas\n\n"
        "## Lenguajes soportados\n"
        "- Java, Python, JavaScript, TypeScript\n"
        "- C#, Go, C/C++, Ruby, PHP\n"
        "- Kotlin, Swift, Scala\n"
        "- HTML, CSS, XML, SQL"
    )


def sonar_best_practices() -> str:
    return (
        "# SonarQube Best Practices\n\n"
        "## Configuracion\n"
        "- Usar Quality Gates estrictos\n"
        "- Coverage minimo: 80%\n"
        "- Duplicacion maxima: 3%\n"
        "- Technical debt ratio: < 5%\n\n"
        "## CI/CD\n"
        "- Escanear en cada PR\n"
        "- Fail build si Quality Gate falla\n"
        "- Sonar-scanner en pipeline\n"
        "- PR decoration con resultados\n\n"
        "## Remediation\n"
        "- Fix issues nuevos primero\n"
        "- Priorizar por severity\n"
        "- Usar SonarLint en IDE\n"
        "- Technical debt debt reduction plan\n\n"
        "## Quality Profiles\n"
        "- Perfiles por lenguaje\n"
        "- Customizar reglas\n"
        "- Heredar de profiles estandar\n"
        "- Versionar cambios\n\n"
        "## Metrics clave\n"
        "- Coverage: porcentaje cubierto por tests\n"
        "- Duplicacion: codigo duplicado\n"
        "- Complexity: complejidad ciclomatica\n"
        "- Technical debt: tiempo para fix\n"
        "- Reliability rating: A-E\n"
        "- Security rating: A-E\n"
        "- Maintainability rating: A-E"
    )


def sonar_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- sonar_run_scan()\n"
        "- sonar_components_search(query)\n"
        "- sonar_issues_search(project_key)\n"
        "- sonar_measures_component(component, metric_keys)\n"
        "- sonar_measures_history(component, metrics)\n"
        "- sonar_qualitygates_list()\n"
        "- sonar_qualitygates_status(project_key)\n"
        "- sonar_rules_search(language, q)\n"
        "- sonar_languages_list()\n"
        "- sonar_projects_search(q)\n"
        "- sonar_project_create(name, key)\n"
        "- sonar_project_delete(key)\n"
        "- sonar_hotspots_search(project_key)\n"
        "- sonar_health()\n\n"
        "## Variables .env\n"
        "- SONAR_HOST_URL\n"
        "- SONAR_API_TOKEN\n"
        "- SONAR_PROJECT_PATH"
    )


def sonar_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "sonar-scanner no encontrado"},
                {"code": -32002, "description": "Error de autenticacion"},
                {"code": -32003, "description": "Error en API de SonarQube"},
                {"code": -32004, "description": "host_url no configurado"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def sonar_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## sonar-scanner no encontrado\n"
        "- Instalar sonar-scanner-cli\n"
        "- Verificar PATH\n"
        "- Usar modo mock para testing\n\n"
        "## Error de autenticacion\n"
        "- Verificar SONAR_API_TOKEN\n"
        "- Verificar permisos del token\n"
        "- Verificar expiry del token\n\n"
        "## No se pueden obtener metricas\n"
        "- Verificar SONAR_HOST_URL\n"
        "- Verificar conectividad de red\n"
        "- Verificar que el proyecto exista\n"
        "- Verificar que haya un scan previo\n\n"
        "## Quality Gate falla\n"
        "- Revisar condiciones del Quality Gate\n"
        "- Verificar coverage minimo\n"
        "- Verificar duplicacion\n"
        "- Fix issues antes de re-scan\n\n"
        "## Scan no envia resultados\n"
        "- Verificar project key\n"
        "- Verificar sonar-project.properties\n"
        "- Verificar token y permisos\n"
        "- Revisar logs del scanner"
    )


def sonar_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Scan basico\n"
        "sonar_run_scan()\n\n"
        "## Buscar issues\n"
        'sonar_issues_search(project_key="my-project")\n\n'
        "## Obtener metricas\n"
        'sonar_measures_component(component="my-project", metric_keys="coverage,bugs,vulnerabilities")\n\n'
        "## Quality gate status\n"
        'sonar_qualitygates_status(project_key="my-project")\n\n'
        "## Buscar proyectos\n"
        'sonar_projects_search(q="my")\n\n'
        "## Hotspots de seguridad\n"
        'sonar_hotspots_search(project_key="my-project")\n\n'
        "## Health check\n"
        "sonar_health()"
    )


def sonar_quality_gates() -> str:
    return (
        "# SonarQube Quality Gates\n\n"
        "## Concepto\n"
        "- Conjunto de condiciones booleanas\n"
        "- Si todas pasan: GREEN (OK)\n"
        "- Si alguna falla: RED (FAIL)\n"
        "- Se evalua despues de cada scan\n\n"
        "## Condiciones tipicas\n"
        "- Coverage < 80%: FAIL\n"
        "- Duplicacion > 3%: FAIL\n"
        "- Technical debt ratio > 5%: FAIL\n"
        "- Bugs > 0: FAIL\n"
        "- Vulnerabilities > 0: FAIL\n"
        "- Code smells nuevos > 0: WARN\n\n"
        "## Way (default Quality Gate)\n"
        "- Coverage on new code < 80%\n"
        "- Duplications on new code > 3%\n"
        "- Maintainability rating on new code worse than A\n"
        "- Reliability rating on new code worse than A\n"
        "- Security rating on new code worse than A\n"
        "- Security hotspots reviewed < 100%\n\n"
        "## API\n"
        "- GET /api/qualitygates/list\n"
        "- GET /api/qualitygates/project_status\n"
        "- POST /api/qualitygates/create\n"
        "- POST /api/qualitygates/destroy\n\n"
        "## Mejores practicas\n"
        "- Usar condiciones sobre new code\n"
        "- No ser demasiado estricto inicialmente\n"
        "- Gradualmente aumentar exigencia\n"
        "- Documentar condiciones"
    )


def sonar_metrics() -> str:
    return (
        "# SonarQube Metrics\n\n"
        "## Reliability\n"
        "- bugs: numero de bugs\n"
        "- reliability_rating: A-E\n"
        "- reliability_remediation_effort: minutos\n\n"
        "## Security\n"
        "- vulnerabilities: numero de vulnerabilidades\n"
        "- security_rating: A-E\n"
        "- security_hotspots: numero de hotspots\n"
        "- security_review_rating: A-E\n\n"
        "## Maintainability\n"
        "- code_smells: numero de code smells\n"
        "- maintainability_rating: A-E\n"
        "- technical_debt: minutos\n"
        "- technical_debt_ratio: porcentaje\n"
        "- sqale_rating: A-E\n\n"
        "## Coverage\n"
        "- coverage: porcentaje\n"
        "- line_coverage: porcentaje de lineas\n"
        "- branch_coverage: porcentaje de branches\n"
        "- tests: numero de tests\n"
        "- test_failures: tests fallidos\n"
        "- test_errors: errores\n\n"
        "## Duplicacion\n"
        "- duplicated_lines: lineas duplicadas\n"
        "- duplicated_blocks: bloques duplicados\n"
        "- duplicated_files: archivos duplicados\n"
        "- duplicated_lines_density: porcentaje\n\n"
        "## Size\n"
        "- ncloc: lineas de codigo no comentadas\n"
        "- lines: total de lineas\n"
        "- statements: numero de statements\n"
        "- functions: numero de funciones\n"
        "- classes: numero de clases\n"
        "- files: numero de archivos\n\n"
        "## Complexity\n"
        "- complexity: complejidad ciclomatica\n"
        "- cognitive_complexity: complejidad cognitiva\n"
        "- function_complexity: complejidad por funcion"
    )


def sonar_rules() -> str:
    return (
        "# SonarQube Rules\n\n"
        "## Tipos\n"
        "- BUG: posible error en codigo\n"
        "- VULNERABILITY: riesgo de seguridad\n"
        "- CODE_SMELL: mala practica\n"
        "- SECURITY_HOTSPOT: punto de revision\n\n"
        "## Severity\n"
        "- BLOCKER: debe fixearse inmediatamente\n"
        "- CRITICAL: alto impacto\n"
        "- MAJOR: impacto significativo\n"
        "- MINOR: impacto menor\n"
        "- INFO: informativo\n\n"
        "## Quality Profiles\n"
        "- Set de reglas activas por lenguaje\n"
        "- Sonar way: profile por defecto\n"
        "- Heredar y customizar\n"
        "- Activar/desactivar reglas\n\n"
        "## API\n"
        "- GET /api/rules/search: buscar reglas\n"
        "- GET /api/rules/show: detalle de regla\n"
        "- POST /api/qualityprofiles/activate_rule\n"
        "- POST /api/qualityprofiles/deactivate_rule\n\n"
        "## Ejemplos de reglas\n"
        "- python:S1234: Functions should not be too complex\n"
        "- java:S1192: String literals should not be duplicated\n"
        "- js:S3798: Variables should be declared before use\n\n"
        "## Custom rules\n"
        "- Crear via API\n"
        "- Usar plugins\n"
        "- Escribir custom rules en Java\n"
        "- Importar desde external analyzers"
    )


def sonar_scanner() -> str:
    return (
        "# Sonar Scanner\n\n"
        "## Instalacion\n"
        "- Download from sonarsource.com\n"
        "- Add to PATH\n"
        "- Verify: sonar-scanner --version\n\n"
        "## Configuracion\n"
        "- sonar-project.properties en raiz del proyecto\n"
        "- sonar.projectKey: identificador unico\n"
        "- sonar.projectName: nombre descriptivo\n"
        "- sonar.sources: directorio de codigo\n"
        "- sonar.tests: directorio de tests\n"
        "- sonar.language: lenguaje (opcional)\n"
        "- sonar.host.url: URL de SonarQube\n"
        "- sonar.login: token de autenticacion\n\n"
        "## Ejemplo sonar-project.properties\n"
        "```\n"
        "sonar.projectKey=my-project\n"
        "sonar.projectName=My Project\n"
        "sonar.sources=src\n"
        "sonar.tests=tests\n"
        "sonar.python.coverage.reportPaths=coverage.xml\n"
        "sonar.host.url=http://sonarqube:9000\n"
        "```\n\n"
        "## CI/CD\n"
        "- GitHub Actions: SonarSource/sonarqube-scan-action\n"
        "- Jenkins: SonarQube Scanner plugin\n"
        "- GitLab CI: sonar-scanner image\n"
        "- Maven: sonar:sonar goal\n\n"
        "## Parametros CLI\n"
        "- -Dsonar.projectKey=...\n"
        "- -Dsonar.host.url=...\n"
        "- -Dsonar.login=...\n"
        "- -Dsonar.branch.name=...\n"
        "- -Dsonar.pullrequest.key=..."
    )


def sonar_issues() -> str:
    return (
        "# SonarQube Issues\n\n"
        "## Tipos\n"
        "- BUG: error en codigo\n"
        "- VULNERABILITY: riesgo seguridad\n"
        "- CODE_SMELL: mala practica\n\n"
        "## Atributos\n"
        "- rule: regla que lo detecto\n"
        "- severity: BLOCKER, CRITICAL, MAJOR, MINOR, INFO\n"
        "- status: OPEN, CONFIRMED, REOPENED, RESOLVED, CLOSED\n"
        "- resolution: FALSE-POSITIVE, WONTFIX, FIXED, REMOVED\n"
        "- debt: tiempo estimado para fix\n"
        "- line: linea del codigo\n"
        "- message: descripcion\n\n"
        "## API\n"
        "- GET /api/issues/search: buscar issues\n"
        "- POST /api/issues/do_transition: cambiar estado\n"
        "- POST /api/issues/set_severity: cambiar severidad\n"
        "- POST /api/issues/assign: asignar\n\n"
        "## Filtros comunes\n"
        "- componentKeys: por proyecto/componente\n"
        "- types: BUG, VULNERABILITY, CODE_SMELL\n"
        "- severities: BLOCKER, CRITICAL, MAJOR, MINOR\n"
        "- statuses: OPEN, CONFIRMED, RESOLVED\n"
        "- resolved: true/false\n"
        "- sinceLeakPeriod: solo nuevos\n\n"
        "## Lifecycle\n"
        "1. OPEN: detectado por scan\n"
        "2. CONFIRMED: confirmado por developer\n"
        "3. RESOLVED: fixeado o wontfix\n"
        "4. REOPENED: vuelve a aparecer\n"
        "5. CLOSED: ya no aplica\n\n"
        "## Mejores practicas\n"
        "- Fix issues nuevos antes de merge\n"
        "- Usar SonarLint para catch en IDE\n"
        "- No acumular technical debt\n"
        "- Wontfix con justificacion"
    )


def sonar_hotspots() -> str:
    return (
        "# SonarQube Security Hotspots\n\n"
        "## Concepto\n"
        "- Puntos de codigo sensibles a seguridad\n"
        "- No necesariamente vulnerabilidades\n"
        "- Requieren revision manual\n"
        "- Security-oriented code patterns\n\n"
        "## Ejemplos\n"
        "- Uso de criptografia debil\n"
        "- Concatenacion de SQL\n"
        "- Uso de eval/exec\n"
        "- HTTP requests sin TLS\n"
        "- Hardcoded passwords\n"
        "- Logging de datos sensibles\n\n"
        "## Estados\n"
        "- TO_REVIEW: pendiente de revision\n"
        "- REVIEWED: revisado\n"
        "- SAFE: no es riesgo\n"
        "- FIXED: corregido\n"
        "- ACKNOWLEDGED: aceptado\n\n"
        "## API\n"
        "- GET /api/hotspots/search: buscar hotspots\n"
        "- GET /api/hotspots/show: detalle\n"
        "- POST /api/hotspots/change_status: cambiar estado\n\n"
        "## Mejores practicas\n"
        "- Revisar todos los hotspots nuevos\n"
        "- Marcar como SAFE o FIXED\n"
        "- No ignorar hotspots\n"
        "- Integrar en PR review\n"
        "- Usar SonarLint para deteccion temprana\n\n"
        "## Diferencia con Vulnerabilities\n"
        "- Vulnerability: confirmada, explotable\n"
        "- Hotspot: posible riesgo, requiere revision\n"
        "- Hotspot puede convertirse en vulnerability\n"
        "- Hotspots son mas numerosos"
    )


def sonar_ci_cd() -> str:
    return (
        "# SonarQube CI/CD Integration\n\n"
        "## GitHub Actions\n"
        "```yaml\n"
        "- name: SonarQube Scan\n"
        "  uses: SonarSource/sonarqube-scan-action@v2\n"
        "  env:\n"
        "    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}\n"
        "    SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}\n"
        "```\n\n"
        "## Jenkins Pipeline\n"
        "```groovy\n"
        "stage('SonarQube') {\n"
        "  steps {\n"
        "    withSonarQubeEnv('SonarQube') {\n"
        "      sh 'sonar-scanner'\n"
        "    }\n"
        "    timeout(time: 10, unit: 'MINUTES') {\n"
        "      waitForQualityGate abortPipeline: true\n"
        "    }\n"
        "  }\n"
        "}\n"
        "```\n\n"
        "## Maven\n"
        "```bash\n"
        "mvn sonar:sonar \\\n"
        "  -Dsonar.projectKey=my-project \\\n"
        "  -Dsonar.host.url=$SONAR_HOST_URL \\\n"
        "  -Dsonar.login=$SONAR_TOKEN\n"
        "```\n\n"
        "## Mejores practicas\n"
        "- Fail build en Quality Gate RED\n"
        "- PR decoration con resultados\n"
        "- Escanear solo new code en PRs\n"
        "- Escanear full code en main\n"
        "- Usar cache para scanner\n"
        "- Parallelize para proyectos grandes\n\n"
        "## Pull Request Analysis\n"
        "- -Dsonar.pullrequest.key=PR_NUMBER\n"
        "- -Dsonar.pullrequest.branch=BRANCH\n"
        "- -Dsonar.pullrequest.base=main\n"
        "- Decoracion automatica en GitHub/GitLab"
    )


def sonar_quality_profiles() -> str:
    return (
        "# SonarQube Quality Profiles\n\n"
        "## Concepto\n"
        "- Set de reglas activas por lenguaje\n"
        "- Cada lenguaje tiene su propio profile\n"
        "- Sonar way: profile por defecto\n"
        "- Se puede heredar y customizar\n\n"
        "## Operaciones\n"
        "- Crear profile\n"
        "- Copiar profile\n"
        "- Activar/desactivar reglas\n"
        "- Asignar a proyecto\n"
        "- Comparar profiles\n\n"
        "## API\n"
        "- GET /api/qualityprofiles/search: listar\n"
        "- POST /api/qualityprofiles/create: crear\n"
        "- POST /api/qualityprofiles/copy: copiar\n"
        "- POST /api/qualityprofiles/activate_rule: activar regla\n"
        "- POST /api/qualityprofiles/deactivate_rule: desactivar regla\n"
        "- GET /api/qualityprofiles/projects: proyectos asignados\n\n"
        "## Mejores practicas\n"
        "- Empezar con Sonar way\n"
        "- Customizar gradualmente\n"
        "- No desactivar reglas critical/blocker\n"
        "- Versionar cambios de profile\n"
        "- Usar inheritance para perfiles custom\n\n"
        "## Sonar way (default)\n"
        "- Reglas mas importantes activadas\n"
        "- Balance entre strictness y noise\n"
        "- Adecuado para la mayoria de proyectos\n"
        "- Customizar para necesidades especificas\n\n"
        "## Comparison\n"
        "- Comparar profiles para ver diferencias\n"
        "- Identificar reglas faltantes\n"
        "- Migrar reglas entre profiles\n"
        "- Auditar cambios"
    )
