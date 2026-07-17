"""Shared MCP stdio Content-Length framing helpers."""

from __future__ import annotations

import json
import sys
from typing import Any, Iterator


def read_messages() -> Iterator[dict[str, Any]]:
    while True:
        headers: dict[str, str] = {}
        while True:
            line = sys.stdin.buffer.readline()
            if not line:
                return
            if line in (b"\r\n", b"\n"):
                break
            try:
                text = line.decode("utf-8").strip()
            except UnicodeDecodeError:
                continue
            if ":" in text:
                key, value = text.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        if "content-length" not in headers:
            continue
        length = int(headers["content-length"])
        body = sys.stdin.buffer.read(length)
        if not body:
            return
        try:
            msg = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(msg, dict):
            yield msg


def write_message(msg: dict[str, Any]) -> None:
    data = json.dumps(msg, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(data)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()
