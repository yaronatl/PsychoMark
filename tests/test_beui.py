import importlib.util
import json
from pathlib import Path

import httpx
import pytest

spec = importlib.util.spec_from_file_location(
    "beui", Path(__file__).resolve().parents[1] / "scripts/beui.py"
)
beui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(beui)


def test_catalogue_session_preserves_protocol_and_reports_tool_errors():
    requests = []

    def handle(request):
        requests.append(request)
        if request.method == "DELETE":
            return httpx.Response(204)
        body = json.loads(request.content)
        if body["method"] == "initialize":
            return httpx.Response(
                200,
                headers={"Mcp-Session-Id": "test-session"},
                json={"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": beui.PROTOCOL}},
            )
        assert request.headers["Mcp-Session-Id"] == "test-session"
        assert request.headers["MCP-Protocol-Version"] == beui.PROTOCOL
        if body["method"] == "notifications/initialized":
            return httpx.Response(202)
        assert body["params"] == {"name": "search_components", "arguments": {"query": "button"}}
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "result": {"isError": True, "content": [{"type": "text", "text": "unavailable"}]},
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ValueError, match="Be UI tool failed"):
            beui.query(client, "https://example.test/mcp", "search_components", {"query": "button"})
    assert requests[-1].method == "DELETE"


@pytest.mark.parametrize(
    "message",
    [
        {"jsonrpc": "2.0", "id": 99, "result": {}},
        {"jsonrpc": "2.0", "id": 2, "error": {"code": -32601, "message": "unknown tool"}},
    ],
)
def test_invalid_or_failed_responses_are_not_successes(message):
    response = httpx.Response(
        200, json=message, request=httpx.Request("POST", "https://example.test")
    )
    with pytest.raises(ValueError):
        beui.result(response, 2)
