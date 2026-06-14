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
