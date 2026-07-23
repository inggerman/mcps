import ast
import json
import re
from pathlib import Path

# json is used by clean_default for serializing list/dict defaults

root = Path(__file__).parent
mcps = sorted([d for d in root.iterdir() if d.is_dir() and d.name.startswith("mcp-")])

BASE_FIELDS = {
    "log_level", "log_format", "mcp_host", "mcp_port", "mcp_server_name",
    "mcp_debug", "mcp_workers", "mcp_transport",
}


def _safe_eval(expr: str):
    tree = ast.parse(expr, mode="eval")
    allowed = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub,
        ast.List, ast.Tuple, ast.Dict, ast.Set,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError(f"Unsafe expression: {expr}")
    return eval(compile(tree, "<default>", "eval"), {"__builtins__": {}}, {})


def clean_default(value: str) -> str:
    value = value.strip()
    if value in ("None", "null"):
        return ""
    if value == "True":
        return "true"
    if value == "False":
        return "false"
    if value == "Path.cwd()":
        return "."
    if value.startswith("Path("):
        inner = value[5:].strip(" )")
        if len(inner) >= 2 and inner[0] == inner[-1] and inner[0] in '"\'':
            return inner[1:-1]
        return inner
    try:
        evaluated = _safe_eval(value)
        if isinstance(evaluated, (list, dict, tuple, set)):
            return json.dumps(evaluated)
        return str(evaluated)
    except Exception:
        pass
    if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
        return value[1:-1]
    return value


def extract_field_info(file_path: Path) -> tuple[str, list[dict]]:
    text = file_path.read_text(encoding="utf-8")
    pm = re.search(r'env_prefix\s*=\s*["\']([^"\']*)["\']', text)
    env_prefix = pm.group(1) if pm else ""

    tree = ast.parse(text)
    env_vars = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if not isinstance(item, ast.AnnAssign) or item.value is None:
                continue
            if not (
                isinstance(item.value, ast.Call)
                and isinstance(item.value.func, ast.Name)
                and item.value.func.id == "Field"
            ):
                continue
            if isinstance(item.target, ast.Name):
                field_name = item.target.id
            else:
                continue
            default = ""
            description = ""
            for kw in item.value.keywords:
                if kw.arg == "default":
                    try:
                        default = clean_default(ast.unparse(kw.value))
                    except Exception:
                        default = ""
                elif kw.arg == "description":
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        description = " ".join(kw.value.value.split())
                    elif isinstance(kw.value, ast.JoinedStr):
                        lines = text.splitlines()
                        start = kw.value.lineno - 1
                        end = kw.value.end_lineno
                        seg = "\n".join(lines[start:end])
                        dm = re.search(r'description\s*=\s*\(([^)]+)\)', seg, re.DOTALL)
                        if dm:
                            description = " ".join(dm.group(1).split())
            env_var = env_prefix + field_name.upper()
            env_vars.append({
                "field": field_name,
                "var": env_var,
                "default": default,
                "description": description,
            })
    return env_prefix, env_vars


def extract_tools(file_path: Path) -> list[dict]:
    text = file_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    tools = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            if not (
                isinstance(deco, ast.Call)
                and isinstance(deco.func, ast.Attribute)
                and deco.func.attr == "tool"
            ):
                continue
            tool_name = node.name
            description = ""
            for kw in deco.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                    tool_name = kw.value.value
                elif kw.arg == "description" and isinstance(kw.value, ast.Constant):
                    description = " ".join(kw.value.value.split())
            tools.append({"name": tool_name, "description": description})
    return tools


inventory = {}
for mcp_dir in mcps:
    name = mcp_dir.name
    pkg = name.replace("-", "_")
    server_file = mcp_dir / "src" / pkg / "server.py"
    config_file = mcp_dir / "src" / pkg / "config.py"

    tools = extract_tools(server_file) if server_file.exists() else []
    env_prefix, env_vars = "MCP_", []
    if config_file.exists():
        env_prefix, env_vars = extract_field_info(config_file)

    inventory[name] = {"tools": tools, "env_prefix": env_prefix, "env_vars": env_vars}

out_file = root / ".mcp_inventory.json"
out_file.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Inventory written to {out_file}")
print(f"MCPs: {len(inventory)}")
for name, data in inventory.items():
    print(f"{name}: {len(data['tools'])} tools, {len(data['env_vars'])} env vars")
