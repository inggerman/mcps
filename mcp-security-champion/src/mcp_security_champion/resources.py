"""Resources de solo lectura para mcp-security-champion."""

from __future__ import annotations

import json


def sec_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-security-champion",
            "version": "1.0.0",
            "project_path": ".",
        },
        indent=2,
        ensure_ascii=False,
    )


def sec_owasp_top10() -> str:
    return (
        "# OWASP Top 10 (2021)\n\n"
        "## A01 - Broken Access Control\n"
        "- Restricciones de acceso incorrectas\n"
        "- Mitigacion: RBAC, ABAC, validacion server-side\n\n"
        "## A02 - Cryptographic Failures\n"
        "- Fallos criptograficos\n"
        "- Mitigacion: TLS, encripcion en reposo, no MD5/SHA1\n\n"
        "## A03 - Injection\n"
        "- SQL, NoSQL, OS command injection\n"
        "- Mitigacion: parametrized queries, ORMs, input validation\n\n"
        "## A04 - Insecure Design\n"
        "- Fallos de diseno\n"
        "- Mitigacion: threat modeling, secure design patterns\n\n"
        "## A05 - Security Misconfiguration\n"
        "- Configuracion insegura\n"
        "- Mitigacion: hardening, defaults seguros, patch management\n\n"
        "## A06 - Vulnerable and Outdated Components\n"
        "- Dependencias desactualizadas\n"
        "- Mitigacion: SCA, dependabot, snyk\n\n"
        "## A07 - Identification and Authentication Failures\n"
        "- Fallos de autenticacion\n"
        "- Mitigacion: MFA, session management, strong passwords\n\n"
        "## A08 - Software and Data Integrity Failures\n"
        "- Fallos de integridad\n"
        "- Mitigacion: signed releases, CI/CD integrity\n\n"
        "## A09 - Security Logging and Monitoring Failures\n"
        "- Fallos de monitoreo\n"
        "- Mitigacion: logging, SIEM, alerting\n\n"
        "## A10 - Server-Side Request Forgery (SSRF)\n"
        "- SSRF\n"
        "- Mitigacion: allowlists, network segmentation"
    )


def sec_pci_dss() -> str:
    return (
        "# PCI-DSS (Payment Card Industry Data Security Standard)\n\n"
        "## Requisitos principales\n"
        "1. Red de firewall y router segura\n"
        "2. No usar defaults de vendor\n"
        "3. Proteger datos almacenados (PAN)\n"
        "4. Encripcion en transmision\n"
        "5. Antivirus y software actualizado\n"
        "6. Desarrollo seguro y testing\n"
        "7. Restriccion de acceso fisico y logico\n"
        "8. Identificar y autenticar accesos\n"
        "9. Restringir acceso fisico a tarjetas\n"
        "10. Monitorear y auditar accesos\n"
        "11. Test regular de seguridad\n"
        "12. Politica de seguridad de la informacion\n\n"
        "## Enmascaramiento de PAN\n"
        "- Mostrar solo primeros 6 y ultimos 4 digitos\n"
        "- Nunca almacenar CVV/CVC\n"
        "- Tokenizacion cuando sea posible"
    )


def sec_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- sec_audit_code(filename)\n"
        "- sec_financial_compliance(filename)\n"
        "- sec_check_secrets(filename)\n"
        "- sec_scan_dependencies(project_path)\n"
        "- sec_generate_security_report(project_path)\n\n"
        "## Variables .env\n"
        "- SEC_PROJECT_PATH"
    )


def sec_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno de Security"},
                {"code": -32001, "description": "FileNotFoundError: archivo no encontrado"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def sec_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## No detecta vulnerabilidades\n"
        "- Verificar que el archivo tenga codigo Python\n"
        "- Los patrones son simples (regex)\n"
        "- No detecta vulnerabilidades logicas\n\n"
        "## Falsos positivos\n"
        "- Palabras como 'password' en comentarios\n"
        "- Variables con nombres similares\n"
        "- Revisar cada finding manualmente\n\n"
        "## Compliance falla\n"
        "- Verificar uso de HTTPS\n"
        "- Verificar enmascaramiento de PAN\n"
        "- No usar http:// para APIs externas"
    )


def sec_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Ejemplo 1: Auditar codigo\n"
        'sec_audit_code(filename="src/auth.py")\n\n'
        "## Ejemplo 2: Compliance financiero\n"
        'sec_financial_compliance(filename="src/payment.py")\n\n'
        "## Ejemplo 3: Escanear secrets\n"
        'sec_check_secrets(filename="config/settings.py")\n\n'
        "## Ejemplo 4: Reporte de seguridad\n"
        'sec_generate_security_report()'
    )


def sec_secure_coding() -> str:
    return (
        "# Secure Coding Practices\n\n"
        "## Input Validation\n"
        "- Validar toda entrada externa\n"
        "- Usar allowlists, no blocklists\n"
        "- Sanitizar HTML/XSS\n"
        "- Parametrizar queries SQL\n\n"
        "## Authentication\n"
        "- Hash passwords con bcrypt/argon2\n"
        "- Nunca almacenar passwords en texto plano\n"
        "- Implementar rate limiting\n"
        "- Usar MFA cuando sea posible\n\n"
        "## Session Management\n"
        "- Tokens aleatorios y suficientemente largos\n"
        "- Expiracion de sesion\n"
        "- Secure, HttpOnly, SameSite cookies\n"
        "- Rotacion de tokens\n\n"
        "## Error Handling\n"
        "- No exponer stack traces\n"
        "- Logging de errores sin datos sensibles\n"
        "- Mensajes genericos al usuario\n\n"
        "## Cryptography\n"
        "- Usar AES-256 para encripcion\n"
        "- Nunca MD5 o SHA1 para passwords\n"
        "- IV unico por encripcion\n"
        "- Keys derivadas con PBKDF2/Argon2"
    )


def sec_threat_modeling() -> str:
    return (
        "# Threat Modeling\n\n"
        "## STRIDE\n"
        "- **S**poofing: suplantacion de identidad\n"
        "- **T**ampering: modificacion de datos\n"
        "- **R**epudiation: negacion de acciones\n"
        "- **I**nformation Disclosure: fuga de datos\n"
        "- **D**enial of Service: indisponibilidad\n"
        "- **E**levation of Privilege: escalada de privilegios\n\n"
        "## DREAD (Risk Rating)\n"
        "- **D**amage Potential: cuanto dano\n"
        "- **R**eproducibility: facil de reproducir\n"
        "- **E**xploitability: facil de explotar\n"
        "- **A**ffected Users: cuantos usuarios\n"
        "- **D**iscoverability: facil de descubrir\n\n"
        "## Process\n"
        "1. Identificar assets\n"
        "2. Crear diagrama de arquitectura\n"
        "3. Identificar amenazas (STRIDE)\n"
        "4. Clasificar riesgos (DREAD)\n"
        "5. Definir mitigaciones\n"
        "6. Validar y documentar"
    )


def sec_dependency_scanning() -> str:
    return (
        "# Dependency Scanning\n\n"
        "## Tipos\n"
        "- SCA (Software Composition Analysis)\n"
        "- License compliance\n"
        "- Outdated dependencies\n\n"
        "## Tools\n"
        "- pip-audit: vulnerabilidades en pip\n"
        "- safety: base de datos de vulns\n"
        "- snyk: SCA + container scan\n"
        "- dependabot: GitHub automatico\n"
        "- renovate: multi-plataforma\n\n"
        "## Mejores practicas\n"
        "- Scan en CI/CD\n"
        "- Actualizar regularmente\n"
        "- Lock files versionados\n"
        "- Renovar deps no patchear\n"
        "- Monitorear CVEs"
    )


def sec_secrets_management() -> str:
    return (
        "# Secrets Management\n\n"
        "## Tipos de secrets\n"
        "- API keys\n"
        "- Database passwords\n"
        "- Certificados privados\n"
        "- Tokens de servicio\n\n"
        "## Tools\n"
        "- HashiCorp Vault: secrets centralizados\n"
        "- AWS Secrets Manager: cloud native\n"
        "- Azure Key Vault: cloud native\n"
        "- doppler: secrets en desarrollo\n"
        "- .env files: solo desarrollo local\n\n"
        "## Mejores practicas\n"
        "- Nunca en codigo fuente\n"
        "- Nunca en repos git\n"
        "- Rotacion regular\n"
        "- Acceso basado en roles\n"
        "- Auditoria de acceso\n"
        "- .gitignore para .env"
    )


def sec_api_security() -> str:
    return (
        "# API Security (OWASP API Top 10)\n\n"
        "## API1 - Broken Object Level Authorization (BOLA)\n"
        "- Acceso a objetos sin validacion\n"
        "- Mitigacion: validar ownership\n\n"
        "## API2 - Broken Authentication\n"
        "- Auth debil o mal implementada\n"
        "- Mitigacion: OAuth2, JWT, MFA\n\n"
        "## API3 - Broken Object Property Level Authorization\n"
        "- Exceso de datos en respuestas\n"
        "- Mitigacion: DTOs, field selection\n\n"
        "## API4 - Unrestricted Resource Consumption\n"
        "- Sin rate limiting o quotas\n"
        "- Mitigacion: rate limit, quotas\n\n"
        "## API5 - Broken Function Level Authorization\n"
        "- Funciones admin expuestas\n"
        "- Mitigacion: RBAC en endpoints\n\n"
        "## API6 - Unrestricted Access to Sensitive Business Flows\n"
        "- Flujos criticos sin proteccion\n"
        "- Mitigacion: anti-automation\n\n"
        "## API7 - SSRF\n"
        "- Server-side requests no controladas\n"
        "- Mitigacion: allowlists\n\n"
        "## API8 - Security Misconfiguration\n"
        "- Config insegura\n"
        "- Mitigacion: hardening\n\n"
        "## API9 - Improper Inventory Management\n"
        "- APIs no documentadas o viejas\n"
        "- Mitigacion: API inventory\n\n"
        "## API10 - Unsafe Consumption of APIs\n"
        "- Confianza excesiva en APIs terceros\n"
        "- Mitigacion: validar y sanitizar"
    )


def sec_container_security() -> str:
    return (
        "# Container Security\n\n"
        "## Imagenes\n"
        "- Usar imagenes oficiales minimas (slim, alpine)\n"
        "- Escanear imagenes (trivy, grype)\n"
        "- No ejecutar como root\n"
        "- Multi-stage builds\n\n"
        "## Runtime\n"
        "- Read-only filesystem\n"
        "- Drop capabilities innecesarias\n"
        "- Resource limits (CPU, memory)\n"
        "- Network policies\n\n"
        "## Secrets en containers\n"
        "- No bake secrets en imagen\n"
        "- Usar docker secrets o k8s secrets\n"
        "- Variables de entorno con cuidado\n\n"
        "## Registry\n"
        "- Usar registry privado\n"
        "- Scan automatico en push\n"
        "- Politica de retencion\n"
        "- Firmas de imagenes (cosign)"
    )


def sec_incident_response() -> str:
    return (
        "# Incident Response\n\n"
        "## Fases (NIST)\n"
        "1. **Preparation**: politicas, tools, entrenamiento\n"
        "2. **Detection & Analysis**: monitoreo, alertas, triage\n"
        "3. **Containment**: aislar, detener propagacion\n"
        "4. **Eradication**: eliminar causa raiz\n"
        "5. **Recovery**: restaurar servicios\n"
        "6. **Post-Incident**: lecciones aprendidas\n\n"
        "## Playbook basico\n"
        "- Detectar el incidente\n"
        "- Clasificar severidad\n"
        "- Notificar al equipo de seguridad\n"
        "- Contener el dano\n"
        "- Preservar evidencia\n"
        "- Erradicar la amenaza\n"
        "- Restaurar servicios\n"
        "- Documentar y mejorar\n\n"
        "## Contactos\n"
        "- Equipo de seguridad (SOC)\n"
        "- Legal y compliance\n"
        "- Comunicaciones\n"
        "- Autoridades (si aplica)"
    )


def sec_compliance_frameworks() -> str:
    return (
        "# Compliance Frameworks\n\n"
        "## PCI-DSS\n"
        "- Payment Card Industry Data Security Standard\n"
        "- Para procesamiento de tarjetas de credito\n"
        "- 12 requisitos principales\n\n"
        "## SOC 2\n"
        "- Service Organization Control 2\n"
        "- Security, Availability, Processing Integrity, Confidentiality, Privacy\n"
        "- Type I y Type II\n\n"
        "## ISO 27001\n"
        "- Information Security Management System (ISMS)\n"
        "- Risk-based approach\n"
        "- Continuous improvement\n\n"
        "## GDPR\n"
        "- General Data Protection Regulation\n"
        "- Datos personales de ciudadanos EU\n"
        "- Derechos: acceso, rectificacion, eliminacion\n\n"
        "## HIPAA\n"
        "- Health Insurance Portability and Accountability Act\n"
        "- Datos de salud en EE.UU.\n"
        "- Privacy Rule, Security Rule\n\n"
        "## NIST CSF\n"
        "- Cybersecurity Framework\n"
        "- Identify, Protect, Detect, Respond, Recover\n"
        "- Risk-based approach"
    )
