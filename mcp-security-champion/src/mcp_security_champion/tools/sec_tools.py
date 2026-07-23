"""
Lógica de mcp-security-champion.

Simula análisis estático básico (SAST) para secretos, funciones inseguras y compliance financiero.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from mcp_shared.errors import FileNotFoundError


def sec_audit_code(file_path: Path) -> dict[str, Any]:
    """Audita código en busca de hardcoded secrets o funciones inseguras."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    findings = []

    # Expresiones regulares simples
    patterns = {
        "Hardcoded Password/Token": r"(?i)(password|token|secret)\s*=\s*['\"][a-zA-Z0-9_\-]+['\"]",
        "Unsafe Function (eval)": r"\beval\(",
        "Unsafe Function (exec)": r"\bexec\(",
        "Weak Crypto (md5)": r"\bhashlib\.md5\(",
    }

    for i, line in enumerate(lines):
        for vuln_name, regex in patterns.items():
            if re.search(regex, line):
                findings.append(
                    {"vulnerability": vuln_name, "line": i + 1, "snippet": line.strip()[:100]}
                )

    return {"file": file_path.name, "vulnerabilities_found": len(findings), "findings": findings}


def sec_financial_compliance(file_path: Path) -> dict[str, Any]:
    """Revisa normativas PCI-DSS simples (ej. uso de enmascaramiento de datos)."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    content = file_path.read_text(encoding="utf-8")

    notes: list[str] = []
    compliance: dict[str, Any] = {
        "pci_dss": {
            "status": "PASS",
            "notes": notes,
        }
    }

    # Si detecta variables que parezcan tarjetas de crédito sin enmascarar
    if re.search(r"(?i)(card_number|credit_card|pan)\s*=\s*", content):
        if "mask(" not in content.lower() and "hash(" not in content.lower():
            compliance["pci_dss"]["status"] = "FAIL"
            notes.append("Posible manejo de PAN (Primary Account Number) sin enmascaramiento.")

    # Si detecta http:// en lugar de https:// para integraciones
    if "http://" in content and "localhost" not in content and "127.0.0.1" not in content:
        compliance["pci_dss"]["status"] = "FAIL"
        notes.append("Uso de HTTP detectado. PCI-DSS exige TLS/HTTPS para comunicaciones externas.")

    return {"file": file_path.name, "compliance": compliance}


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def check_secrets(file_path: Path) -> dict[str, Any]:
    """Escanea un archivo en busca de posibles secrets expuestos."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    secret_patterns = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "AWS Secret Key": r"(?i)aws_secret\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]",
        "Generic API Key": r"(?i)api[_-]?key\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]",
        "Private Key": r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
        "JWT Token": r"eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+",
        "Database URL": r"(?i)(postgres|mysql|mongodb)://[^:\s]+:[^@\s]+@",
        "GitHub Token": r"gh[pousr]_[A-Za-z0-9]{36}",
    }

    findings: list[dict[str, Any]] = []

    for i, line in enumerate(lines, 1):
        for name, pattern in secret_patterns.items():
            if re.search(pattern, line):
                findings.append({
                    "type": name,
                    "line": i,
                    "snippet": line.strip()[:100],
                })

    return {
        "file": file_path.name,
        "secrets_found": len(findings),
        "findings": findings,
        "clean": len(findings) == 0,
    }


def scan_dependencies(project_path: Path) -> dict[str, Any]:
    """Escanea dependencias del proyecto buscando paquetes con vulnerabilidades conocidas."""
    pyproject = project_path / "pyproject.toml"
    requirements = project_path / "requirements.txt"

    deps: list[str] = []

    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        in_deps = False
        for line in content.splitlines():
            if "dependencies" in line and "[" in line:
                in_deps = True
                continue
            if in_deps:
                if "]" in line:
                    break
                dep = line.strip().strip('"').strip("'")
                if dep:
                    deps.append(dep)

    if requirements.exists():
        for line in requirements.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                deps.append(line)

    known_vulnerable = {
        "requests<2.31": "CVE-2023-32681",
        "cryptography<41.0": "Multiple CVEs",
        "pyyaml<6.0.1": "CVE-2020-14343",
        "jinja2<3.1.3": "CVE-2024-22195",
    }

    vulnerabilities: list[dict[str, str]] = []
    for dep in deps:
        dep_lower = dep.lower().replace(" ", "")
        for vuln_dep, cve in known_vulnerable.items():
            if vuln_dep in dep_lower:
                vulnerabilities.append({"dependency": dep, "cve": cve})

    return {
        "total_dependencies": len(deps),
        "dependencies": deps[:50],
        "vulnerabilities_found": len(vulnerabilities),
        "vulnerabilities": vulnerabilities,
    }


def generate_security_report(project_path: Path) -> dict[str, Any]:
    """Genera un reporte de seguridad completo del proyecto."""
    audit_results: list[dict[str, Any]] = []
    secret_results: list[dict[str, Any]] = []
    total_vulns = 0
    total_secrets = 0

    for f in project_path.rglob("*.py"):
        if any(part.startswith(".") for part in f.parts):
            continue
        if "__pycache__" in f.parts:
            continue
        try:
            audit = sec_audit_code(f)
            if audit["vulnerabilities_found"] > 0:
                audit_results.append({
                    "file": str(f.relative_to(project_path)),
                    "vulnerabilities": audit["vulnerabilities_found"],
                })
                total_vulns += audit["vulnerabilities_found"]

            secrets = check_secrets(f)
            if not secrets["clean"]:
                secret_results.append({
                    "file": str(f.relative_to(project_path)),
                    "secrets": secrets["secrets_found"],
                })
                total_secrets += secrets["secrets_found"]
        except Exception:
            continue

    dep_scan = scan_dependencies(project_path)

    return {
        "files_scanned": len(audit_results) + len(secret_results),
        "total_vulnerabilities": total_vulns,
        "total_secrets": total_secrets,
        "code_vulnerabilities": audit_results[:50],
        "secret_exposures": secret_results[:50],
        "dependency_issues": dep_scan["vulnerabilities_found"],
        "overall_status": "PASS" if total_vulns == 0 and total_secrets == 0 and dep_scan["vulnerabilities_found"] == 0 else "FAIL",
    }


def check_owasp_top10(file_path: Path) -> dict[str, Any]:
    """Verifica codigo contra OWASP Top 10."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    checks: list[dict[str, Any]] = []

    owasp_patterns = {
        "A03 - Injection": [
            (r"(?i)\bexec\s*\(", "exec() function detected"),
            (r"(?i)\beval\s*\(", "eval() function detected"),
            (r"(?i)cursor\.execute\s*\(\s*f['\"]", "f-string in SQL query"),
            (r"(?i)os\.system\s*\(", "os.system() detected"),
        ],
        "A02 - Cryptographic Failures": [
            (r"\bhashlib\.md5\s*\(", "MD5 is weak"),
            (r"\bhashlib\.sha1\s*\(", "SHA1 is weak"),
            (r"(?i)random\.random\s*\(\).*password", "Insecure random for password"),
        ],
        "A05 - Security Misconfiguration": [
            (r"(?i)debug\s*=\s*True", "Debug mode enabled"),
            (r"(?i)allow_origin\s*=\s*['\"]\*['\"]", "CORS wildcard"),
        ],
        "A07 - Auth Failures": [
            (r"(?i)password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password"),
            (r"(?i)token\s*=\s*['\"][^'\"]+['\"]", "Hardcoded token"),
        ],
    }

    for i, line in enumerate(lines, 1):
        for category, patterns in owasp_patterns.items():
            for pattern, message in patterns:
                if re.search(pattern, line):
                    checks.append({
                        "category": category,
                        "line": i,
                        "message": message,
                        "snippet": line.strip()[:100],
                    })

    return {
        "file": file_path.name,
        "owasp_violations": len(checks),
        "checks": checks,
    }


def audit_project_security(project_path: Path) -> dict[str, Any]:
    """Audita la seguridad de todo el proyecto."""
    report = generate_security_report(project_path)
    owasp_results: list[dict[str, Any]] = []

    for f in project_path.rglob("*.py"):
        if any(part.startswith(".") for part in f.parts):
            continue
        if "__pycache__" in f.parts:
            continue
        try:
            owasp = check_owasp_top10(f)
            if owasp["owasp_violations"] > 0:
                owasp_results.append({
                    "file": str(f.relative_to(project_path)),
                    "violations": owasp["owasp_violations"],
                    "checks": owasp["checks"][:10],
                })
        except Exception:
            continue

    return {
        "security_report": report,
        "owasp_violations": owasp_results[:50],
        "total_owasp_violations": sum(r["violations"] for r in owasp_results),
    }


def generate_security_checklist() -> list[dict[str, str]]:
    """Genera un checklist de seguridad para el proyecto."""
    return [
        {"category": "Authentication", "item": "Passwords hashed with bcrypt/argon2", "status": "pending"},
        {"category": "Authentication", "item": "MFA implemented for admin", "status": "pending"},
        {"category": "Authentication", "item": "Rate limiting on login", "status": "pending"},
        {"category": "Authorization", "item": "RBAC implemented", "status": "pending"},
        {"category": "Authorization", "item": "Resource ownership validated", "status": "pending"},
        {"category": "Input Validation", "item": "All inputs validated", "status": "pending"},
        {"category": "Input Validation", "item": "SQL queries parametrized", "status": "pending"},
        {"category": "Cryptography", "item": "No MD5/SHA1 for passwords", "status": "pending"},
        {"category": "Cryptography", "item": "TLS for all external comms", "status": "pending"},
        {"category": "Secrets", "item": "No hardcoded secrets", "status": "pending"},
        {"category": "Secrets", "item": "Secrets in vault/env", "status": "pending"},
        {"category": "Logging", "item": "Security events logged", "status": "pending"},
        {"category": "Logging", "item": "No sensitive data in logs", "status": "pending"},
        {"category": "Dependencies", "item": "Dependencies scanned", "status": "pending"},
        {"category": "Dependencies", "item": "No known vulnerable packages", "status": "pending"},
    ]


def check_https_usage(file_path: Path) -> dict[str, Any]:
    """Verifica que el codigo use HTTPS en lugar de HTTP."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    http_urls: list[dict[str, Any]] = []

    for i, line in enumerate(lines, 1):
        if "http://" in line and "localhost" not in line and "127.0.0.1" not in line and "0.0.0.0" not in line:
            http_urls.append({
                "line": i,
                "url": line.strip()[:100],
                "recommendation": "Use HTTPS instead of HTTP",
            })

    return {
        "file": file_path.name,
        "http_urls_found": len(http_urls),
        "urls": http_urls,
        "secure": len(http_urls) == 0,
    }


def validate_input_handling(file_path: Path) -> dict[str, Any]:
    """Valida el manejo de entradas en un archivo Python."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    issues: list[dict[str, Any]] = []

    for i, line in enumerate(lines, 1):
        if re.search(r"(?i)cursor\.execute\s*\(\s*f['\"]", line):
            issues.append({
                "type": "SQL Injection Risk",
                "line": i,
                "detail": "f-string in SQL query. Use parameterized queries.",
            })
        if re.search(r"(?i)os\.system\s*\(", line):
            issues.append({
                "type": "Command Injection Risk",
                "line": i,
                "detail": "os.system() detected. Use subprocess with shell=False.",
            })
        if re.search(r"(?i)subprocess\.call\s*\(.*shell\s*=\s*True", line):
            issues.append({
                "type": "Command Injection Risk",
                "line": i,
                "detail": "shell=True in subprocess. Avoid if possible.",
            })
        if re.search(r"(?i)pickle\.loads?\s*\(", line):
            issues.append({
                "type": "Deserialization Risk",
                "line": i,
                "detail": "pickle.loads() is unsafe with untrusted data.",
            })

    return {
        "file": file_path.name,
        "issues_found": len(issues),
        "issues": issues,
    }


def generate_threat_model(project_name: str) -> dict[str, Any]:
    """Genera un modelo de amenazas basico para un proyecto."""
    return {
        "project": project_name,
        "stride": {
            "Spoofing": [
                "Authentication bypass",
                "Credential theft",
                "Session hijacking",
            ],
            "Tampering": [
                "Data modification in transit",
                "Unauthorized data changes",
                "Parameter tampering",
            ],
            "Repudiation": [
                "Missing audit logs",
                "Untraceable actions",
            ],
            "Information Disclosure": [
                "Error messages with sensitive data",
                "API responses with excessive data",
                "Log files with secrets",
            ],
            "Denial of Service": [
                "No rate limiting",
                "Resource exhaustion",
                "Large payload attacks",
            ],
            "Elevation of Privilege": [
                "Missing authorization checks",
                "IDOR vulnerabilities",
                "Default credentials",
            ],
        },
        "recommendations": [
            "Implement authentication and authorization",
            "Use HTTPS everywhere",
            "Add rate limiting",
            "Validate all inputs",
            "Log security events",
            "Scan dependencies regularly",
        ],
    }


def check_password_policy(file_path: Path) -> dict[str, Any]:
    """Verifica politicas de contrasenas en el codigo."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    issues: list[dict[str, Any]] = []

    for i, line in enumerate(lines, 1):
        if re.search(r"(?i)password\s*=\s*['\"][^'\"]+['\"]", line):
            issues.append({
                "type": "Hardcoded Password",
                "line": i,
                "detail": "Password hardcoded in source code.",
            })
        if re.search(r"(?i)min_length\s*=\s*[0-7]\b", line):
            issues.append({
                "type": "Weak Password Policy",
                "line": i,
                "detail": "Minimum password length is too short (< 8).",
            })
        if re.search(r"(?i)hashlib\.(md5|sha1)\s*\(", line) and "password" in line.lower():
            issues.append({
                "type": "Weak Hash for Password",
                "line": i,
                "detail": "Using MD5/SHA1 for password hashing. Use bcrypt/argon2.",
            })

    return {
        "file": file_path.name,
        "issues_found": len(issues),
        "issues": issues,
        "compliant": len(issues) == 0,
    }


def export_security_findings(project_path: Path) -> dict[str, Any]:
    """Exporta todos los hallazgos de seguridad del proyecto."""
    audit = audit_project_security(project_path)
    dep_scan = scan_dependencies(project_path)

    return {
        "summary": {
            "total_vulnerabilities": audit["security_report"]["total_vulnerabilities"],
            "total_secrets": audit["security_report"]["total_secrets"],
            "total_owasp_violations": audit["total_owasp_violations"],
            "dependency_issues": dep_scan["vulnerabilities_found"],
            "overall_status": audit["security_report"]["overall_status"],
        },
        "details": {
            "code_vulnerabilities": audit["security_report"]["code_vulnerabilities"],
            "secret_exposures": audit["security_report"]["secret_exposures"],
            "owasp_violations": audit["owasp_violations"],
            "dependency_vulnerabilities": dep_scan["vulnerabilities"],
        },
    }


def get_security_metrics(project_path: Path) -> dict[str, Any]:
    """Retorna metricas de seguridad del proyecto."""
    report = generate_security_report(project_path)
    dep_scan = scan_dependencies(project_path)

    py_files = list(project_path.rglob("*.py"))
    py_files = [f for f in py_files if not any(p.startswith(".") for p in f.parts) and "__pycache__" not in f.parts]

    return {
        "total_files": len(py_files),
        "files_with_vulnerabilities": len(report["code_vulnerabilities"]),
        "files_with_secrets": len(report["secret_exposures"]),
        "total_vulnerabilities": report["total_vulnerabilities"],
        "total_secrets": report["total_secrets"],
        "dependency_vulnerabilities": dep_scan["vulnerabilities_found"],
        "security_score": max(0, 100 - (report["total_vulnerabilities"] * 5 + report["total_secrets"] * 10 + dep_scan["vulnerabilities_found"] * 3)),
        "status": report["overall_status"],
    }


def generate_security_policy(project_name: str) -> str:
    """Genera una plantilla de politica de seguridad para el proyecto."""
    return "\n".join([
        f"# Security Policy - {project_name}",
        "",
        "## Reporting a Vulnerability",
        "",
        "If you discover a security vulnerability, please report it to:",
        "- Email: security@example.com",
        "- Do NOT open a public issue",
        "- Include: description, steps to reproduce, potential impact",
        "",
        "## Response Time",
        "",
        "- Acknowledgment: within 48 hours",
        "- Initial assessment: within 5 business days",
        "- Fix timeline: depends on severity (Critical: 7 days, High: 30 days, Medium: 90 days)",
        "",
        "## Supported Versions",
        "",
        "| Version | Supported |",
        "|---------|-----------|",
        "| latest  | yes       |",
        "| < 1.0   | no        |",
        "",
        "## Security Measures",
        "",
        "- Regular dependency scanning",
        "- SAST analysis in CI/CD",
        "- Secret scanning in commits",
        "- Container image scanning",
        "- Penetration testing (annual)",
        "",
        "## Best Practices for Contributors",
        "",
        "- Never commit secrets or credentials",
        "- Use parameterized queries",
        "- Validate all inputs",
        "- Use HTTPS for all external communication",
        "- Follow OWASP Top 10 guidelines",
        "- Write tests for security-critical code",
    ])
