"""Enroll exactly one agentcore-gateway MCP server into Cherry Studio.

Derives endpoint/auth/timeout from contracts/agentcore-gateway-client.json.
Materializes BIFROST_MCP_VIRTUAL_KEY into Cherry Local Storage (Cherry cannot
expand ${env:}). Never prints the resolved virtual key.

Cherry must be fully quit before --apply.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = REPO_ROOT / "contracts" / "agentcore-gateway-client.json"
RENDERER = REPO_ROOT / "renderers" / "gateway-clients" / "cherry-studio.json"
PATCH_JS = Path(__file__).resolve().parent / "patch_mcp_leveldb.js"
CHERRY_PKG = Path(__file__).resolve().parent

CHERRY_ROOT = Path(os.environ.get("APPDATA", "")) / "CherryStudio"
LEVELDB = CHERRY_ROOT / "Local Storage" / "leveldb"
LOCKFILE = CHERRY_ROOT / "lockfile"
BACKUP_ROOT = Path(r"E:\AgentCore-Backups")

GATEWAY_NAME = "agentcore-gateway"


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


def load_contract() -> dict:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if data.get("name") != GATEWAY_NAME:
        raise RuntimeError("gateway contract name mismatch")
    hints = (data.get("client_render_hints") or {}).get("cherry-studio") or {}
    if not hints.get("enabled", False):
        raise RuntimeError("cherry-studio client hint missing/disabled in gateway contract")
    return data


def cherry_running() -> bool:
    if LOCKFILE.exists():
        return True
    if os.name == "nt":
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
        manifest.append(
            {
                "path": str(f),
                "backup": str(target),
                "sha256": digest,
                "bytes": target.stat().st_size,
            }
        )
    if LEVELDB.is_dir():
        shutil.copytree(LEVELDB, dest / "leveldb", dirs_exist_ok=True)
    (dest / "SHA256MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return dest


def ensure_node_deps() -> None:
    nm = CHERRY_PKG / "node_modules" / "classic-level"
    alt = CHERRY_PKG / "_node_workspace" / "node_modules" / "classic-level"
    if nm.is_dir() or alt.is_dir():
        return
    print("installing classic-level under scripts/cherry (local only)")
    subprocess.check_call(["npm", "install", "--omit=dev"], cwd=str(CHERRY_PKG))


def write_import_artifact(contract: dict, vk: str) -> Path:
    url = contract["url"]
    timeout = int(contract.get("timeout_seconds") or 300)
    server = {
        "id": GATEWAY_NAME,
        "name": GATEWAY_NAME,
        "type": "streamableHttp",
        "baseUrl": url,
        "headers": {"Authorization": f"Bearer {vk}"},
        "timeout": timeout,
        "provider": "AgentCore",
        "isActive": True,
        "disabledTools": [],
    }
    out = CHERRY_ROOT / "Data" / "agentcore-gateway-mcp-import.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mcpServers": {
            GATEWAY_NAME: {
                "type": "streamableHttp",
                "url": url,
                "headers": server["headers"],
                "timeout": timeout,
            }
        },
        "servers": [server],
        "_agentcore_note": "Live enrollment prefers LevelDB patch; this JSON is import fallback only.",
    }
    out.write_text(json.dumps(payload), encoding="utf-8")
    return out


def run_patch(mode: str) -> int:
    ensure_node_deps()
    args = ["node", str(PATCH_JS)]
    if mode == "inspect":
        args.append("--inspect")
    elif mode == "apply":
        args.append("--confirm")
    else:
        args.append("--dry-run")
    proc = subprocess.run(args, cwd=str(CHERRY_PKG), text=True, capture_output=True)
    sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write LevelDB (requires Cherry quit)")
    parser.add_argument("--inspect", action="store_true", help="Inspect current MCP slice only")
    parser.add_argument("--dry-run", action="store_true", help="Show proposed patch without writing")
    args = parser.parse_args()

    if not CHERRY_ROOT.is_dir():
        print("ERROR: CherryStudio AppData root not found")
        return 2

    contract = load_contract()
    if not RENDERER.is_file():
        print("WARN: renderer missing:", RENDERER)

    if args.inspect:
        return run_patch("inspect")

    if cherry_running() and (args.apply or args.dry_run or not args.inspect):
        if args.apply:
            print("ERROR: Cherry Studio is running. Fully quit it, then re-run with --apply.")
            print(f"lockfile={LOCKFILE.exists()}")
            return 3

    vk = _user_env("BIFROST_MCP_VIRTUAL_KEY")
    if not vk:
        print("ERROR: BIFROST_MCP_VIRTUAL_KEY not set in User/process env")
        return 4
    digest = sha256(vk.encode("utf-8")).hexdigest()[:12]
    print(f"vk_present=True vk_len={len(vk)} vk_sha256_12={digest} env=BIFROST_MCP_VIRTUAL_KEY")
    print(f"contract_url={contract['url']} timeout={contract.get('timeout_seconds')}")

    backup = backup_cherry(BACKUP_ROOT)
    print(f"backup={backup}")

    import_path = write_import_artifact(contract, vk)
    print(f"wrote_import_artifact={import_path}")
    print("gateway_preview", json.dumps({"id": GATEWAY_NAME, "url": contract["url"], "headers": {"Authorization": "Bearer ***"}, "timeout": contract.get("timeout_seconds"), "isActive": True}))

    mode = "apply" if args.apply else "dry-run"
    rc = run_patch(mode)
    if rc != 0:
        return rc
    if args.apply:
        print("ENROLL_APPLY=OK")
        print("Ensure exactly one agentcore-gateway; Global Memory remains false; restart Cherry.")
    else:
        print("ENROLL_DRY_RUN=OK (re-run with --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
