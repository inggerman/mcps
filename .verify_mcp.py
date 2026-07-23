"""Quick verification script for MCP container endpoints using httpx."""
import json

import httpx

URL = "http://localhost:8034/mcp"


def parse_response(raw: str) -> dict:
    if raw.startswith("event:"):
        for line in raw.split("\n"):
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
    return json.loads(raw)


def main() -> None:
    with httpx.Client(timeout=30) as client:
        init_payload = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "verify-script", "version": "1.0"},
            },
        }
        resp = client.post(
            URL,
            json=init_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        print(f"Initialize: {resp.status_code}")
        session_id = resp.headers.get("mcp-session-id", "")
        print(f"Session ID: {session_id}")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if session_id:
            headers["Mcp-Session-Id"] = session_id

        client.post(
            URL,
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            headers=headers,
        )

        resp = client.post(
            URL,
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers=headers,
        )
        data = parse_response(resp.text)
        tools = data.get("result", {}).get("tools", [])
        print(f"\nTools count: {len(tools)}")
        for t in tools:
            print(f"  - {t['name']}")

        resp = client.post(
            URL,
            json={"jsonrpc": "2.0", "id": 2, "method": "resources/list"},
            headers=headers,
        )
        data = parse_response(resp.text)
        resources = data.get("result", {}).get("resources", [])
        print(f"\nResources count: {len(resources)}")
        for r in resources:
            print(f"  - {r['uri']}")

        resp = client.post(
            URL,
            json={"jsonrpc": "2.0", "id": 3, "method": "resources/templates/list"},
            headers=headers,
        )
        data = parse_response(resp.text)
        templates = data.get("result", {}).get("resourceTemplates", [])
        print(f"\nResource templates count: {len(templates)}")
        for t in templates:
            print(f"  - {t['uriTemplate']}")


if __name__ == "__main__":
    main()
