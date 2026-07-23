#!/usr/bin/env python3
"""Genera docs/mcp-resources-summary.md con los recursos de cada MCP."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
inv = json.loads((ROOT / ".mcp_inventory.json").read_text(encoding="utf-8"))

lines = [
    "# Resumen de recursos por MCP",
    "",
    "**Generado automáticamente desde `.mcp_inventory.json`**.",
    "",
    "Para cada servidor se listan: puerto Docker, tools y variables de entorno específicas.",
    "",
]

# Obtener metadatos de puertos del generador si están disponibles
ports_path = ROOT / ".mcp_inventory.json"

# No tenemos PORT_ORDER aquí, pero usamos el orden del propio JSON.
for name, data in inv.items():
    tools = data.get("tools", [])
    envs = data.get("env_vars", [])

    lines.append(f"## {name}")
    lines.append("")
    lines.append(f"- **Tools:** {len(tools)}")
    lines.append(f"- **Variables de entorno específicas:** {len(envs)}")
    lines.append("")

    if tools:
        lines.append("### Tools")
        lines.append("")
        lines.append("| Tool | Descripción |")
        lines.append("|------|-------------|")
        for t in tools:
            desc = t["description"].replace("|", "\\|")
            lines.append(f"| `{t['name']}` | {desc} |")
        lines.append("")

    if envs:
        lines.append("### Variables de entorno")
        lines.append("")
        lines.append("| Variable | Default | Descripción |")
        lines.append("|----------|---------|-------------|")
        for e in envs:
            var = e["var"]
            default = str(e.get("default", "")).replace("|", "\\|") or "—"
            desc = (e.get("description") or "—").replace("|", "\\|")
            lines.append(f"| `{var}` | {default} | {desc} |")
        lines.append("")

out_path = ROOT / "docs" / "mcp-resources-summary.md"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Escrito {out_path}")
