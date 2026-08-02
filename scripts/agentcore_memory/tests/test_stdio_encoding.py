from __future__ import annotations

import io
import json

from agentcore_memory import server


def test_main_decodes_utf8_requests_when_windows_stream_starts_as_cp1252(
    monkeypatch,
) -> None:
    expected = "Goal Mode — preserve “lossless” context"
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "diagnostic/echo",
        "params": {"text": expected},
    }
    input_bytes = io.BytesIO(
        (json.dumps(request, ensure_ascii=False) + "\n").encode("utf-8")
    )
    output_bytes = io.BytesIO()
    stdin = io.TextIOWrapper(input_bytes, encoding="cp1252")
    stdout = io.TextIOWrapper(output_bytes, encoding="cp1252", write_through=True)

    monkeypatch.setattr(server.sys, "stdin", stdin)
    monkeypatch.setattr(server.sys, "stdout", stdout)
    monkeypatch.setattr(
        server,
        "handle_request",
        lambda message: {
            "jsonrpc": "2.0",
            "id": message["id"],
            "result": {"text": message["params"]["text"]},
        },
    )

    assert server.main() == 0
    stdout.flush()
    response = json.loads(output_bytes.getvalue().decode("utf-8"))
    assert response["result"]["text"] == expected
