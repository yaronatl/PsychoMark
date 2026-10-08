"""Read the Be UI MCP catalogue using project config, without global Codex writes.

This small client supports Be UI's JSON responses, not arbitrary MCP transports.
Returned component code and installation commands are printed, never executed.
"""

import argparse
import json
import sys
import tomllib
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "2025-03-26"


def result(response: httpx.Response, identifier: int) -> dict:
    response.raise_for_status()
    message = response.json()
    if message.get("jsonrpc") != "2.0" or message.get("id") != identifier:
        raise ValueError("Unexpected MCP response identifier or protocol")
    if "error" in message:
        raise ValueError(f"MCP error: {message['error']}")
    value = message.get("result")
    if not isinstance(value, dict):
        raise ValueError("Missing MCP result")
    if value.get("isError"):
        raise ValueError(f"Be UI tool failed: {value.get('content', [])}")
    return value


def query(client: httpx.Client, url: str, tool: str | None, arguments: dict) -> dict:
    """Initialize a fresh MCP session and make one catalogue request."""
    headers = {"Accept": "application/json, text/event-stream"}
    initialized = client.post(
        url,
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": "psychomark-design-tools", "version": "1.0"},
            },
        },
    )
    initialization = result(initialized, 1)
    if initialization.get("protocolVersion") != PROTOCOL:
        raise ValueError("Be UI negotiated an unsupported MCP version")
    headers["MCP-Protocol-Version"] = PROTOCOL
    session = initialized.headers.get("mcp-session-id")
    if session:
        headers["Mcp-Session-Id"] = session
    try:
        client.post(
            url, headers=headers, json={"jsonrpc": "2.0", "method": "notifications/initialized"}
        ).raise_for_status()
        return result(
            client.post(
                url,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call" if tool else "tools/list",
                    "params": {"name": tool, "arguments": arguments} if tool else {},
                },
            ),
            2,
        )
    finally:
        if session:
            try:
                client.delete(url, headers=headers)
            except httpx.HTTPError:
                pass  # Session cleanup must not obscure the catalogue result or error.


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("tools")
    components = commands.add_parser("components")
    components.add_argument("--category")
    commands.add_parser("search").add_argument("query")
    commands.add_parser("component").add_argument("slug")
    install = commands.add_parser("install-command")
    install.add_argument("slug")
    install.add_argument("--package-manager", choices=["npm", "pnpm", "bun", "yarn"], default="npm")
    args = parser.parse_args()
    tool, arguments = {
        "tools": (None, {}),
        "components": (
            "list_components",
            {"category": args.category} if getattr(args, "category", None) else {},
        ),
        "search": ("search_components", {"query": getattr(args, "query", "")}),
        "component": ("get_component", {"slug": getattr(args, "slug", "")}),
        "install-command": (
            "get_install_command",
            {
                "slug": getattr(args, "slug", ""),
                "packageManager": getattr(args, "package_manager", "npm"),
            },
        ),
    }[args.command]
    try:
        config = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
        url = config["mcp_servers"]["beui"]["url"]
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            value = query(client, url, tool, arguments)
        print(json.dumps(value, ensure_ascii=False, indent=2))
    except (httpx.HTTPError, ValueError, KeyError, OSError) as error:
        print(f"Be UI unavailable: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
