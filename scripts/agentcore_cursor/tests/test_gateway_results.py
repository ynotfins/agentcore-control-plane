from __future__ import annotations

from agentcore_cursor.gateway import GatewayClient


def test_plain_text_tool_failure_is_not_reported_as_success(monkeypatch) -> None:
    client = GatewayClient.__new__(GatewayClient)
    client.session = "diagnostic-session"
    client._id = 0
    monkeypatch.setattr(
        client,
        "_post",
        lambda _payload: {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Tool execution failed: MCP tool call failed: "
                            "internal error (sanitized)"
                        ),
                    }
                ]
            },
        },
    )

    result = client.call_tool("agentcore_memory-memory_status", {})

    assert result == {
        "ok": False,
        "error": "gateway_tool_error",
        "detail": (
            "Tool execution failed: MCP tool call failed: "
            "internal error (sanitized)"
        ),
    }


def test_arbitrary_plain_text_tool_result_is_not_reported_as_success(monkeypatch) -> None:
    client = GatewayClient.__new__(GatewayClient)
    client.session = "diagnostic-session"
    client._id = 0
    monkeypatch.setattr(
        client,
        "_post",
        lambda _payload: {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": [{"type": "text", "text": "accepted"}]},
        },
    )

    result = client.call_tool("agentcore_memory-append_event", {})

    assert result == {
        "ok": False,
        "error": "unstructured_gateway_result",
        "detail": "accepted",
    }
