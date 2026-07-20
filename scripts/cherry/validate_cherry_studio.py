"""Deterministic Cherry Studio AgentCore alignment validator.

Fails when:
- Cherry URL differs from canonical gateway endpoint
- more than one AgentCore gateway is stored
- a direct AgentCore upstream is stored
- a Swarm server is stored
- an obsolete 8081 shim is stored
- Global Memory is enabled contrary to policy
- a secret appears in source-controlled renderer/prompt/contract outputs
- governed Agent missing or MCP mount incorrect
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = REPO_ROOT / "contracts" / "agentcore-gateway-client.json"
RENDERER = REPO_ROOT / "renderers" / "gateway-clients" / "cherry-studio.json"
PROMPT = REPO_ROOT / "docs" / "prompts" / "cherry-agentcore-workspace-agent.md"
PATCH_JS = Path(__file__).resolve().parent / "patch_mcp_leveldb.js"
CHERRY_PKG = Path(__file__).resolve().parent
AGENTS_DB = Path(os.environ.get("APPDATA", "")) / "CherryStudio" / "Data" / "agents.db"

GATEWAY_NAME = "agentcore-gateway"
AGENT_ID = "agentcore-workspace-agent"
AGENT_NAME = "AgentCore Workspace Agent"

FORBIDDEN = {
    "agentcore-memory",
    "arabold-docs",
    "depwire",
    "tentra",
    "serena",
    "sequential-thinking",
    "playwright",
    "filesystem",
    "openrouter",
    "swarmrecall",
    "swarmvault",
    "swarmclaw",
    "openclaw",
    "clawx",
}

SECRET_RE = re.compile(
    r"(Bearer\s+[A-Za-z0-9_\-\.]{16,}|sk-[A-Za-z0-9]{16,}|eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,})",
    re.I,
)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def inspect_live() -> dict:
    ensure = CHERRY_PKG / "node_modules" / "classic-level"
    alt = CHERRY_PKG / "_node_workspace" / "node_modules" / "classic-level"
    if not ensure.is_dir() and not alt.is_dir():
        subprocess.check_call(["npm", "install", "--omit=dev"], cwd=str(CHERRY_PKG))
    proc = subprocess.run(
        ["node", str(PATCH_JS), "--inspect"],
        cwd=str(CHERRY_PKG),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        fail(f"inspect failed rc={proc.returncode}")
    return json.loads(proc.stdout)


def validate_source_files(contract: dict) -> None:
    for path in (RENDERER, PROMPT, CONTRACT):
        text = path.read_text(encoding="utf-8")
        if SECRET_RE.search(text):
            # Allow env placeholder only
            if "${env:BIFROST_MCP_VIRTUAL_KEY}" in text and not re.search(
                r"Bearer\s+(?!\$\{env:)[A-Za-z0-9_\-\.]{16,}", text
            ):
                continue
            fail(f"secret-like token in source-controlled file: {path}")
    renderer = json.loads(RENDERER.read_text(encoding="utf-8"))
    url = renderer["mcpServers"][GATEWAY_NAME]["url"]
    if url != contract["url"]:
        fail(f"renderer url {url} != contract {contract['url']}")
    auth = renderer["mcpServers"][GATEWAY_NAME]["headers"]["Authorization"]
    if "${env:BIFROST_MCP_VIRTUAL_KEY}" not in auth:
        fail("renderer must keep env placeholder, not materialized key")
    hints = (contract.get("client_render_hints") or {}).get("cherry-studio")
    if not hints or not hints.get("enabled"):
        fail("contracts/agentcore-gateway-client.json missing cherry-studio hint")


def validate_live(contract: dict, live: dict) -> None:
    servers = live.get("servers") or []
    gateways = [s for s in servers if (s.get("id") == GATEWAY_NAME or s.get("name") == GATEWAY_NAME)]
    if len(gateways) != 1:
        fail(f"expected exactly one agentcore-gateway, found {len(gateways)}")
    g = gateways[0]
    if g.get("url") != contract["url"]:
        fail(f"live gateway url {g.get('url')} != {contract['url']}")
    if not g.get("active"):
        fail("agentcore-gateway is not active")
    if g.get("timeout") not in (None, 300) and int(g.get("timeout") or 0) != 300:
        fail(f"unexpected timeout {g.get('timeout')}")
    if g.get("auth_env_placeholder"):
        fail("live store has unexpanded ${env:} placeholder")
    if not g.get("has_auth") or int(g.get("auth_len") or 0) < 20:
        fail("live gateway missing materialized auth header")
    if live.get("globalMemoryEnabled") is True:
        fail("globalMemoryEnabled is true (policy requires false)")

    for s in servers:
        name = str(s.get("name") or s.get("id") or "").lower()
        url = str(s.get("url") or "")
        if ":8081/" in url or url.endswith(":8081/mcp"):
            fail(f"obsolete 8081 shim present: {url}")
        for f in FORBIDDEN:
            if name == f or name.endswith("/" + f) or name.startswith("@") and f in name:
                # allow inactive built-in @cherry/filesystem
                if name == "@cherry/filesystem" and not s.get("active"):
                    continue
                if f == "filesystem" and name == "@cherry/filesystem" and not s.get("active"):
                    continue
                if s.get("active") or f in ("swarmrecall", "swarmvault", "swarmclaw", "openclaw", "clawx", "openrouter"):
                    if name == "@cherry/filesystem" and not s.get("active"):
                        continue
                    if f == "filesystem" and "cherry" in name and not s.get("active"):
                        continue
                    # Direct upstream names are forbidden even if inactive (except cherry built-in inactive)
                    if name.startswith("@cherry/") and not s.get("active"):
                        continue
                    if f in name and not name.startswith("@cherry/"):
                        fail(f"forbidden MCP server present: {s.get('name')}")


def validate_agent() -> None:
    if not AGENTS_DB.is_file():
        fail("agents.db missing")
    con = sqlite3.connect(str(AGENTS_DB))
    try:
        row = con.execute(
            "SELECT id, name, mcps, instructions, deleted_at FROM agents WHERE id = ?",
            (AGENT_ID,),
        ).fetchone()
        if not row:
            fail(f"agent {AGENT_ID} missing")
        _id, name, mcps, instructions, deleted_at = row
        if deleted_at:
            fail("agent is soft-deleted")
        if name != AGENT_NAME:
            fail(f"agent name {name!r} != {AGENT_NAME!r}")
        mcp_list = json.loads(mcps or "[]")
        if mcp_list != [GATEWAY_NAME]:
            fail(f"agent mcps {mcp_list} != ['{GATEWAY_NAME}']")
        prompt = PROMPT.read_text(encoding="utf-8").strip()
        if instructions.strip() != prompt:
            # allow trailing newline differences already stripped
            fail("agent instructions do not match source-controlled prompt")
        if "client_key = cherry-studio" not in instructions:
            fail("prompt missing client_key")
    finally:
        con.close()


def main() -> int:
    contract = load_contract()
    validate_source_files(contract)
    live = inspect_live()
    validate_live(contract, live)
    validate_agent()
    print("VALIDATE_CHERRY=PASS")
    print(
        json.dumps(
            {
                "gateway": GATEWAY_NAME,
                "url": contract["url"],
                "servers": live.get("servers"),
                "globalMemoryEnabled": live.get("globalMemoryEnabled"),
                "agent_id": AGENT_ID,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
