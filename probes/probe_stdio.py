from __future__ import annotations

import json
import os
import subprocess
import sys
import time


def terminate_process_tree(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: probe_stdio.py '<json command spec|@spec-file>'", file=sys.stderr)
        return 2
    spec_arg = sys.argv[1]
    if spec_arg.startswith("@"):
        with open(spec_arg[1:], encoding="utf-8-sig") as spec_file:
            spec = json.load(spec_file)
    else:
        spec = json.loads(spec_arg)
    env = os.environ.copy()
    env.update(spec.get("env", {}))
    proc = subprocess.Popen(
        [spec["command"], *spec.get("args", [])],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=spec.get("cwd") or None,
    )
    try:
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
        print(json.dumps({"status": "healthy", "latency_ms": elapsed, "initialize": init_response, "tools": json.loads(tools_line)}))
        return 0
    finally:
        terminate_process_tree(proc)


if __name__ == "__main__":
    raise SystemExit(main())
