#!/usr/bin/env python3
"""KIE Media MCP (stdio NDJSON) — image, video and audio generation through KIE's job API.

KIE's media models are not OpenAI-compatible: they run on ``/api/v1/jobs/createTask`` and are
read back by polling ``/api/v1/jobs/recordInfo``. OmniRoute and Bifrost cannot route that shape,
so it is exposed here as tools instead of as a model provider.

Authority: contracts/bifrost-upstream-mcp-registry.json (server id ``kie-media``).
Credential: Windows User-scope ``KIE_API_KEY`` only. Never logged, never returned.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SERVER_NAME = "kie-media"
SERVER_VERSION = "0.1.0"
DEFAULT_PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}

API_BASE = "https://api.kie.ai"
UPLOAD_BASE = "https://kieai.redpandaai.co"
TERMINAL_STATES = {"success", "fail", "failed", "error", "cancelled", "canceled"}


def _log(message: str) -> None:
    sys.stderr.write(f"[{SERVER_NAME}] {message}\n")
    sys.stderr.flush()


def _api_key() -> str:
    key = os.environ.get("KIE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("KIE_API_KEY is not set in the process environment")
    return key


def _request(method: str, url: str, *, body: dict[str, Any] | None = None, raw: bytes | None = None,
             content_type: str = "application/json", timeout: int = 120) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {_api_key()}", "Accept": "application/json"}
    data = raw
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    if data is not None:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read()[:600].decode("utf-8", "replace")
        raise RuntimeError(f"KIE HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"KIE network error: {error.reason}") from error
    try:
        return json.loads(payload)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"KIE returned non-JSON ({len(payload)} bytes)") from error


def _unwrap(result: dict[str, Any]) -> Any:
    code = result.get("code")
    if code not in (200, "200", None):
        raise RuntimeError(f"KIE code {code}: {result.get('msg') or result}")
    if result.get("success") is False:
        raise RuntimeError(f"KIE error: {result.get('msg') or result}")
    return result.get("data")


def _text(payload: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}]}


# ---------------------------------------------------------------- tools


def tool_models(arguments: dict[str, Any]) -> Any:
    """List KIE's catalogue, filtered by task type or a text query."""
    task_type = (arguments.get("task_type") or "").strip()
    query = (arguments.get("query") or "").strip().lower()
    limit = int(arguments.get("limit") or 60)

    params = {}
    if task_type:
        params["taskType"] = task_type
    url = f"{API_BASE}/api/v1/models"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = _unwrap(_request("GET", url))
    models = data.get("models") if isinstance(data, dict) else data
    models = models or []
    if query:
        models = [
            item for item in models
            if query in str(item.get("model", "")).lower()
            or query in str(item.get("title", "")).lower()
            or query in str(item.get("description", "")).lower()
        ]
    trimmed = [
        {
            "model": item.get("model"),
            "provider": item.get("provider"),
            "taskType": item.get("taskType"),
            "title": (item.get("title") or "")[:110],
        }
        for item in models[:limit]
    ]
    return {"total": len(models), "returned": len(trimmed), "models": trimmed}


def tool_model_schema(arguments: dict[str, Any]) -> Any:
    """Return the exact input contract for one model. Always call before create."""
    model = (arguments.get("model") or "").strip()
    if not model:
        raise RuntimeError("model is required")
    data = _unwrap(_request("GET", f"{API_BASE}/api/v1/models/{model}/schema"))
    if not data or not data.get("openapi"):
        return {
            "model": model,
            "openapi": None,
            "note": "KIE has not published a schema for this model yet. Do not guess input fields.",
        }
    return {"model": model, "openapi": data.get("openapi")}


def tool_create_task(arguments: dict[str, Any]) -> Any:
    """Submit a media job. Returns a taskId; poll it with kie_task_status."""
    model = (arguments.get("model") or "").strip()
    inputs = arguments.get("input")
    if not model:
        raise RuntimeError("model is required")
    if not isinstance(inputs, dict):
        raise RuntimeError("input must be an object matching the model schema")
    body: dict[str, Any] = {"model": model, "input": inputs}
    if arguments.get("callback_url"):
        body["callBackUrl"] = arguments["callback_url"]
    data = _unwrap(_request("POST", f"{API_BASE}/api/v1/jobs/createTask", body=body))
    return {
        "taskId": (data or {}).get("taskId"),
        "recordId": (data or {}).get("recordId"),
        "next": "call kie_task_status with taskId, or kie_wait_task to block until done",
    }


def _record(task_id: str) -> dict[str, Any]:
    data = _unwrap(_request("GET", f"{API_BASE}/api/v1/jobs/recordInfo?taskId={urllib.parse.quote(task_id)}"))
    if not isinstance(data, dict):
        return {"taskId": task_id, "state": "unknown", "raw": data}
    return {
        "taskId": data.get("taskId", task_id),
        "model": data.get("model"),
        "state": data.get("state"),
        "successFlag": data.get("successFlag"),
        "creditsConsumed": data.get("creditsConsumed"),
        "failCode": data.get("failCode"),
        "failMsg": data.get("failMsg"),
        "resultUrls": (data.get("response") or {}).get("resultUrls")
        or _result_urls_from_json(data.get("resultJson")),
    }


def _result_urls_from_json(raw: Any) -> Any:
    if not raw:
        return None
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        return None
    return parsed.get("resultUrls") if isinstance(parsed, dict) else None


def tool_task_status(arguments: dict[str, Any]) -> Any:
    """Read one job's state and result URLs."""
    task_id = (arguments.get("task_id") or "").strip()
    if not task_id:
        raise RuntimeError("task_id is required")
    return _record(task_id)


def tool_wait_task(arguments: dict[str, Any]) -> Any:
    """Poll until the job reaches a terminal state, up to timeout_seconds."""
    task_id = (arguments.get("task_id") or "").strip()
    if not task_id:
        raise RuntimeError("task_id is required")
    timeout = max(10, min(int(arguments.get("timeout_seconds") or 300), 900))
    interval = max(3, min(int(arguments.get("poll_seconds") or 8), 60))
    deadline = time.time() + timeout
    last: dict[str, Any] = {"taskId": task_id, "state": "unknown"}
    while time.time() < deadline:
        last = _record(task_id)
        if str(last.get("state", "")).lower() in TERMINAL_STATES:
            return last
        time.sleep(interval)
    last["note"] = f"still running after {timeout}s; poll again with kie_task_status"
    return last


def tool_upload_file(arguments: dict[str, Any]) -> Any:
    """Upload a local image/video so image-to-video and image-to-image models can use it."""
    path_value = (arguments.get("path") or "").strip()
    if not path_value:
        raise RuntimeError("path is required")
    path = Path(path_value).expanduser()
    if not path.is_file():
        raise RuntimeError(f"file not found: {path}")
    upload_path = (arguments.get("upload_path") or "images/user-uploads").strip().strip("/")
    name = (arguments.get("file_name") or path.name).strip()

    if path.stat().st_size <= 10 * 1024 * 1024:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        body = {
            "base64Data": f"data:{mime};base64,{encoded}",
            "uploadPath": upload_path,
            "fileName": name,
        }
        data = _unwrap(_request("POST", f"{UPLOAD_BASE}/api/file-base64-upload", body=body))
    else:
        boundary = "----agentcoreKieUpload"
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        parts: list[bytes] = []
        for field, value in (("uploadPath", upload_path), ("fileName", name)):
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"\r\n\r\n{value}\r\n'.encode()
            )
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n".encode()
        )
        parts.append(path.read_bytes())
        parts.append(f"\r\n--{boundary}--\r\n".encode())
        data = _unwrap(
            _request(
                "POST",
                f"{UPLOAD_BASE}/api/file-stream-upload",
                raw=b"".join(parts),
                content_type=f"multipart/form-data; boundary={boundary}",
            )
        )
    return {
        "downloadUrl": (data or {}).get("downloadUrl"),
        "fileName": (data or {}).get("fileName"),
        "note": "put downloadUrl into the model's input field named by its schema",
    }


TOOLS: list[dict[str, Any]] = [
    {
        "name": "kie_models",
        "description": (
            "List KIE's media catalogue (image, video, audio). Filter by task_type "
            "('Text to Video', 'Image to Video', 'Text to Image', 'Image to Image', "
            "'Image Editing', 'Video Editing', 'Lip Sync', 'Text to Music', 'Text to Speech') "
            "or a free-text query. Always look the model up here instead of guessing a name."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_type": {"type": "string"},
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            },
        },
    },
    {
        "name": "kie_model_schema",
        "description": (
            "Return the exact input contract for one model. Field names differ per model "
            "(image_url, input_image, first_frame_image, ...). Call this before kie_create_task."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"model": {"type": "string"}},
            "required": ["model"],
        },
    },
    {
        "name": "kie_create_task",
        "description": (
            "Submit a KIE media job. Returns a taskId. Use kie_wait_task or kie_task_status to "
            "collect the result. Billing is per call and visible as creditsConsumed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "input": {"type": "object"},
                "callback_url": {"type": "string"},
            },
            "required": ["model", "input"],
        },
    },
    {
        "name": "kie_task_status",
        "description": "Read one job's state, credit cost, and result URLs.",
        "inputSchema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
    },
    {
        "name": "kie_wait_task",
        "description": "Poll a job until it finishes (bounded). Prefer this over repeated manual polling.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "timeout_seconds": {"type": "integer", "minimum": 10, "maximum": 900},
                "poll_seconds": {"type": "integer", "minimum": 3, "maximum": 60},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "kie_upload_file",
        "description": (
            "Upload a local image or video to KIE and get a downloadUrl for image-to-video, "
            "image-to-image and video-editing models."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "upload_path": {"type": "string"},
                "file_name": {"type": "string"},
            },
            "required": ["path"],
        },
    },
]

HANDLERS = {
    "kie_models": tool_models,
    "kie_model_schema": tool_model_schema,
    "kie_create_task": tool_create_task,
    "kie_task_status": tool_task_status,
    "kie_wait_task": tool_wait_task,
    "kie_upload_file": tool_upload_file,
}


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")

    if method == "initialize":
        requested = (message.get("params") or {}).get("protocolVersion")
        version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        handler = HANDLERS.get(str(name))
        if handler is None:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"unknown tool: {name}"},
            }
        try:
            return {"jsonrpc": "2.0", "id": request_id, "result": _text(handler(arguments))}
        except Exception as error:  # noqa: BLE001 - surfaced to the caller, never crashes the pipe
            _log(f"{name} failed: {error}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": f"{name} failed: {error}"}],
                    "isError": True,
                },
            }
    if request_id is None:
        return None
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"unsupported method: {method}"},
    }


def main() -> int:
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8", errors="strict")
        except (AttributeError, ValueError):
            pass
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(message, dict):
            continue
        response = handle_request(message)
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
