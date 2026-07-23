#!/usr/bin/env python3
"""Imprime tabla resumen de MCPs: tools, env vars y puerto."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
inv = json.loads((ROOT / ".mcp_inventory.json").read_text(encoding="utf-8"))

# Extraer puertos de docker-compose.yml
ports = {}
compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
for name in inv:
    m = re.search(rf"^  {re.escape(name)}:\s*\n(?:.*\n){{0,30}}?\s+MCP_PORT:\s*\"?(\d+)\"?", compose, re.MULTILINE)
    ports[name] = m.group(1) if m else "—"

print("| Servidor | Puerto | Tools | Env vars |")
print("|----------|--------|-------|----------|")
for name, data in inv.items():
    print(f"| `{name}` | {ports[name]} | {len(data['tools'])} | {len(data['env_vars'])} |")
