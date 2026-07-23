#!/usr/bin/env python3
"""Lista recursos (tools, env vars, puerto) de cada MCP desde el inventario."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
inv = json.loads((ROOT / ".mcp_inventory.json").read_text(encoding="utf-8"))

for name, data in inv.items():
    tools = data.get("tools", [])
    envs = data.get("env_vars", [])
    print(f"## {name}")
    print(f"- tools: {len(tools)}")
    for t in tools:
        desc = t["description"]
        print(f"  - `{t['name']}`: {desc[:120]}{'...' if len(desc) > 120 else ''}")
    print(f"- env_vars: {len(envs)}")
    for e in envs:
        default = e.get("default", "")
        desc = e.get("description", "") or "—"
        print(f"  - `{e['var']}`={default!r}  # {desc[:80]}{'...' if len(desc) > 80 else ''}")
    print()
