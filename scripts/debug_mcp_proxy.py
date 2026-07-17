#!/usr/bin/env python3
"""Debug wrapper: log raw MCP stdin bytes then proxy to agentcore_memory server."""
from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

LOG = Path(r"H:\AgentRuntime\bifrost\logs\mcp-stdin-debug.bin")
TARGET = Path(__file__).resolve().parent / "agentcore_memory" / "server.py"


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [sys.executable, "-u", str(TARGET)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )
    assert proc.stdin and proc.stdout and proc.stderr

    def pump_out() -> None:
        assert proc.stdout
        while True:
            chunk = proc.stdout.read(1)
            if not chunk:
                break
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()

    def pump_err() -> None:
        assert proc.stderr
        data = proc.stderr.read()
        if data:
            Path(r"H:\AgentRuntime\bifrost\logs\mcp-stderr-debug.txt").write_bytes(data)

    threading.Thread(target=pump_out, daemon=True).start()
    threading.Thread(target=pump_err, daemon=True).start()

    with LOG.open("ab") as fh:
        while True:
            chunk = sys.stdin.buffer.read(1)
            if not chunk:
                break
            fh.write(chunk)
            fh.flush()
            proc.stdin.write(chunk)
            proc.stdin.flush()
    try:
        proc.stdin.close()
    except Exception:
        pass
    return proc.wait()


if __name__ == "__main__":
    raise SystemExit(main())
