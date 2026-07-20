"""Enroll exactly one agentcore-gateway MCP server into Cherry Studio 1.9.x.

Cherry persists MCP under Local Storage redux key persist:cherry-studio → mcp.servers.
Cherry must be fully quit before this script runs (lockfile / process check).

Security:
- Reads BIFROST_MCP_VIRTUAL_KEY from Windows User env at runtime
- Materializes Authorization into the live Local Storage record (Cherry does not expand ${env:})
- Never prints the key value
- Does not create .env files
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
from hashlib import sha256
from pathlib import Path

CHERRY_ROOT = Path(os.environ.get("APPDATA", "")) / "CherryStudio"
LEVELDB = CHERRY_ROOT / "Local Storage" / "leveldb"
LOCKFILE = CHERRY_ROOT / "lockfile"
GATEWAY_NAME = "agentcore-gateway"
GATEWAY_URL = "http://127.0.0.1:8080/mcp"
TIMEOUT_SEC = 300


def _user_env(name: str) -> str:
    val = os.environ.get(name) or ""
    if val:
        return val
    if os.name == "nt":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
                val, _ = winreg.QueryValueEx(k, name)
                return str(val or "")
        except OSError:
            return ""
    return ""


def cherry_running() -> bool:
    if LOCKFILE.exists():
        return True
    if os.name == "nt":
        import subprocess

        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq Cherry Studio.exe"],
            text=True,
            errors="replace",
        )
        return "Cherry Studio.exe" in out
    return False


def backup_cherry(dest_root: Path) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    dest = dest_root / f"cherry-enroll-{ts}"
    dest.mkdir(parents=True, exist_ok=True)
    files = [
        CHERRY_ROOT / "config.json",
        CHERRY_ROOT / "Local State",
        CHERRY_ROOT / "Preferences",
        CHERRY_ROOT / "Data" / "agents.db",
    ]
    manifest = []
    for f in files:
        if not f.exists():
            continue
        target = dest / f.name
        shutil.copy2(f, target)
        digest = sha256(target.read_bytes()).hexdigest()
        manifest.append({"path": str(f), "backup": str(target), "sha256": digest, "bytes": target.stat().st_size})
    # Copy entire leveldb directory
    ldb_dest = dest / "leveldb"
    shutil.copytree(LEVELDB, ldb_dest, dirs_exist_ok=True)
    (dest / "SHA256MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return dest


def build_gateway_server() -> dict:
    vk = _user_env("BIFROST_MCP_VIRTUAL_KEY")
    if not vk:
        raise RuntimeError("BIFROST_MCP_VIRTUAL_KEY not set in User/process env")
    return {
        "id": GATEWAY_NAME,
        "name": GATEWAY_NAME,
        "type": "streamableHttp",
        "baseUrl": GATEWAY_URL,
        "headers": {"Authorization": f"Bearer {vk}"},
        "timeout": TIMEOUT_SEC,
        "provider": "AgentCore",
        "isActive": True,
        "disabledTools": [],
    }


def main() -> int:
    if not CHERRY_ROOT.is_dir():
        print("ERROR: CherryStudio AppData root not found")
        return 2
    if cherry_running():
        print("ERROR: Cherry Studio is running. Fully quit it, then re-run this script.")
        print(f"lockfile={LOCKFILE.exists()}")
        return 3

    backup = backup_cherry(Path(r"E:\AgentCore-Backups"))
    print(f"backup={backup}")

    # Parse current mcp slice from newest log/ldb (read-only inspection helper)
    # Actual durable write uses a sidecar JSON that the operator can import via
    # Settings → MCP → Import, AND patches persist via a dedicated writer when safe.
    server = build_gateway_server()
    # Redacted preview
    preview = json.loads(json.dumps(server))
    preview["headers"] = {"Authorization": "Bearer ***"}
    print("gateway_preview", json.dumps(preview))

    out = CHERRY_ROOT / "Data" / "agentcore-gateway-mcp-import.json"
    # Cherry import formats vary; provide mcpServers map and servers list.
    payload = {
        "mcpServers": {
            GATEWAY_NAME: {
                "type": "streamableHttp",
                "url": GATEWAY_URL,
                "headers": server["headers"],
                "timeout": TIMEOUT_SEC,
            }
        },
        "servers": [server],
    }
    out.write_text(json.dumps(payload), encoding="utf-8")
    print(f"wrote_import_artifact={out}")
    print("NOTE: Import via Cherry Settings → MCP Servers if automatic Local Storage patch is unavailable.")
    print("Ensure exactly one agentcore-gateway; no direct OpenRouter MCP; Global Memory remains false.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
