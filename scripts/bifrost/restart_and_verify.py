#!/usr/bin/env python3
"""Execute two complete restart cycles in dependency order and run verification after each.

Dependency Order:
1. Bifrost Gateway
2. AgentCore ChatGPT compatibility proxy
3. OpenAI tunnel-client
"""

import os
import subprocess
import time
import winreg
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "bifrost" / "verify_chatgpt_profile.py"
STOP_SCRIPT = REPO_ROOT / "ops" / "bifrost" / "Stop-AgentCoreBifrostGateway.ps1"
START_SCRIPT = REPO_ROOT / "ops" / "bifrost" / "Start-AgentCoreBifrostGateway.ps1"
PROXY_SCRIPT = Path(r"C:\Users\ynotf\.config\tunnel-client\agentcore-mcp-compat-proxy.cjs")
TUNNEL_CLIENT_EXE = Path(r"C:\Users\ynotf\AppData\Local\OpenAI\tunnel-client\tunnel-client.exe")
TUNNEL_CLIENT_CONFIG = Path(r"C:\Users\ynotf\.config\tunnel-client\agentcore-gateway.yaml")


def get_user_env(name: str) -> str:
    val = os.environ.get(name, "")
    if val:
        return val
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return val
    except Exception:
        return ""


def stop_all() -> None:
    print("[STOP] Stopping tunnel-client, compat-proxy, and Bifrost...")
    # Stop tunnel-client
    subprocess.run(["powershell", "-Command", "Stop-Process -Name 'tunnel-client' -Force -ErrorAction SilentlyContinue"], capture_output=True)
    # Stop proxy node processes
    subprocess.run(["powershell", "-Command", "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*agentcore-mcp-compat-proxy.cjs*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"], capture_output=True)
    # Stop Bifrost
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(STOP_SCRIPT)], capture_output=True)
    time.sleep(2)


def start_all() -> tuple[subprocess.Popen | None, subprocess.Popen | None]:
    print("[START] Starting Bifrost Gateway...")
    res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(START_SCRIPT)], capture_output=True, text=True)
    print(f"  Bifrost start output: {res.stdout.strip()}")

    # Prepare environment for background processes
    env = dict(os.environ)
    vk = get_user_env("BIFROST_MCP_VK_CHATGPT")
    if vk:
        env["BIFROST_MCP_VK_CHATGPT"] = vk
        env["BIFROST_MCP_AUTHORIZATION"] = f"Bearer {vk}"

    print("[START] Starting AgentCore ChatGPT compatibility proxy (18081)...")
    proxy_proc = subprocess.Popen(["node", str(PROXY_SCRIPT)], env=env)
    time.sleep(2)

    print("[START] Starting OpenAI tunnel-client...")
    tunnel_proc = None
    if TUNNEL_CLIENT_EXE.exists():
        tunnel_proc = subprocess.Popen([str(TUNNEL_CLIENT_EXE), "run", "--config", str(TUNNEL_CLIENT_CONFIG)], env=env)
        time.sleep(3)
    else:
        print("  WARNING: tunnel-client.exe not found at path")

    return proxy_proc, tunnel_proc


def run_cycle(cycle_number: int) -> bool:
    print(f"\n=======================================================")
    print(f"  RESTART CYCLE {cycle_number}")
    print(f"=======================================================")

    stop_all()
    proxy_proc, tunnel_proc = start_all()

    print(f"\n[VERIFY] Running verification suite for Cycle {cycle_number}...")
    res = subprocess.run(["python", str(VERIFY_SCRIPT)], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)

    passed = res.returncode == 0 and "FAIL" not in res.stdout
    print(f"Cycle {cycle_number} Verdict: {'PASS' if passed else 'FAIL'}")

    return passed


def main() -> None:
    print("Beginning 2-cycle restart persistence test...")
    cycle1_pass = run_cycle(1)
    cycle2_pass = run_cycle(2)

    print("\n=======================================================")
    print("  RESTART PERSISTENCE FINAL RESULTS")
    print("=======================================================")
    print(f"Cycle 1: {'PASS' if cycle1_pass else 'FAIL'}")
    print(f"Cycle 2: {'PASS' if cycle2_pass else 'FAIL'}")

    if cycle1_pass and cycle2_pass:
        print("\nRESTART_PERSISTENCE_TEST_PASSED")
    else:
        print("\nRESTART_PERSISTENCE_TEST_FAILED")


if __name__ == "__main__":
    main()
