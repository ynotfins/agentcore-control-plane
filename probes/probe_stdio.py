from __future__ import annotations

import json
import os
import subprocess
import sys
import time


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: probe_stdio.py '<json command spec>'", file=sys.stderr)
        return 2
    spec = json.loads(sys.argv[1])
    env = os.environ.copy()
    env.update(spec.get("env", {}))
    proc = subprocess.Popen(
        [spec["command"], *spec.get("args", [])],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "mcp-control-plane-probe", "version": "0.1.0"},
        },
    }
    assert proc.stdin and proc.stdout
    proc.stdin.write(json.dumps(initialize) + "\n")
    proc.stdin.flush()
    started = time.time()
    line = proc.stdout.readline()
    if not line:
        print(json.dumps({"status": "launch_failed", "stderr": proc.stderr.read() if proc.stderr else ""}))
        return 1
    init_response = json.loads(line)
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}) + "\n")
    proc.stdin.flush()
    tools_line = proc.stdout.readline()
    elapsed = int((time.time() - started) * 1000)
    proc.terminate()
    print(json.dumps({"status": "healthy", "latency_ms": elapsed, "initialize": init_response, "tools": json.loads(tools_line)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
