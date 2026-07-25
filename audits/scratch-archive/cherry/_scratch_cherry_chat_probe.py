"""Prove Cherry local OpenAI API can complete a no-tool chat.

Reads API server key from Cherry config/logs WITHOUT printing it.
Requires Cherry running with API server on 127.0.0.1:23333.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

APP = Path(os.environ["APPDATA"]) / "CherryStudio"
LOG = APP / "logs" / "app.2026-07-20.log"


def load_api_key() -> str:
    # Prefer config.json if present
    for candidate in (APP / "config.json", APP / "Preferences"):
        if not candidate.is_file():
            continue
        text = candidate.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'"apiKey"\s*:\s*"(cs-sk-[^"]+)"', text)
        if m:
            return m.group(1)
    # Fallback: latest log line (never print)
    if LOG.is_file():
        # share-mode read
        data = LOG.read_bytes()
        text = data.decode("utf-8", "replace")
        matches = re.findall(r'"apiKey"\s*:\s*"(cs-sk-[^"]+)"', text)
        if matches:
            return matches[-1]
    raise SystemExit("api key not found in config/logs")


def main() -> int:
    key = load_api_key()
    body = {
        "model": "deepseek:deepseek-v4-pro",
        "messages": [{"role": "user", "content": "Reply with exactly: PONG"}],
        "max_tokens": 32,
        "stream": False,
    }
    req = urllib.request.Request(
        "http://127.0.0.1:23333/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8", "replace")
            status = resp.status
    except Exception as e:
        # Do not include headers/key
        print(json.dumps({"ok": False, "error_type": type(e).__name__, "error": str(e)[:200]}))
        return 1
    data = json.loads(raw)
    content = ""
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        content = ""
    print(
        json.dumps(
            {
                "ok": status == 200 and bool(content),
                "status": status,
                "model_requested": body["model"],
                "content_len": len(content or ""),
                "content_preview": (content or "")[:80],
                "api_key_len": len(key),
                "api_key_prefix": key[:6] + "...",
            }
        )
    )
    return 0 if status == 200 and content else 2


if __name__ == "__main__":
    raise SystemExit(main())
