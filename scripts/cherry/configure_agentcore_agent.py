"""Create or update the governed Cherry Agent: AgentCore Workspace Agent.

Idempotent. Does not print secrets. Leaves unrelated Agents untouched.
Requires Cherry Studio fully quit when writing agents.db.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = REPO_ROOT / "docs" / "prompts" / "cherry-agentcore-workspace-agent.md"
SKILLS_AUDIT = REPO_ROOT / "audits" / "CHERRY_STUDIO_SKILLS_AUDIT_2026-07-19.md"

CHERRY_ROOT = Path(os.environ.get("APPDATA", "")) / "CherryStudio"
AGENTS_DB = CHERRY_ROOT / "Data" / "agents.db"
AGENT_DIR = CHERRY_ROOT / "Data" / "Agents" / "agentcore-workspace"
SKILLS_SRC = CHERRY_ROOT / "Data" / "Agents" / "w-default" / ".agents" / "skills"
CONFIG_JSON = CHERRY_ROOT / "config.json"
LOCKFILE = CHERRY_ROOT / "lockfile"

AGENT_ID = "agentcore-workspace-agent"
AGENT_NAME = "AgentCore Workspace Agent"
CLIENT_KEY = "cherry-studio"
AGENT_KEY = "cherry-studio-assistant"

# Approved / hash-pinned skills from audits/CHERRY_STUDIO_SKILLS_AUDIT_2026-07-19.md
# find-skills is explicitly not catalog-admitted.
APPROVED_SKILLS = [
    "brainstorming",
    "diagnosing-bugs",
    "executing-plans",
    "playwright-skill",
    "requesting-code-review",
    "skill-creator",
    "systematic-debugging",
    "test-driven-development",
    "using-superpowers",
    "vercel-composition-patterns",
    "vercel-react-best-practices",
    "verification-before-completion",
    "writing-plans",
]


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


def sync_skills() -> list[str]:
    dest = AGENT_DIR / ".agents" / "skills"
    dest.mkdir(parents=True, exist_ok=True)
    mounted: list[str] = []
    search_roots = [
        SKILLS_SRC,
        CHERRY_ROOT / "Data" / "Agents" / "w-default" / ".claude" / "skills",
        CHERRY_ROOT / "Data" / "Agents" / "t-default" / ".claude" / "skills",
    ]
    for name in APPROVED_SKILLS:
        src = None
        for root in search_roots:
            candidate = root / name
            if candidate.is_dir():
                src = candidate
                break
        if src is None:
            print(f"WARN: approved skill missing at source: {name}")
            continue
        target = dest / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src, target)
        mounted.append(name)
    # Remove non-approved skills if previously copied
    for child in dest.iterdir():
        if child.is_dir() and child.name not in APPROVED_SKILLS:
            shutil.rmtree(child)
            print(f"removed_unapproved_skill={child.name}")
    lock = {
        "schema": "agentcore.cherry.skills.lock.v1",
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_audit": str(SKILLS_AUDIT.as_posix()),
        "mounted": mounted,
        "excluded": ["find-skills"],
    }
    (AGENT_DIR / "skills-lock.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")
    return mounted


def upsert_agent(prompt: str) -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    accessible = json.dumps([str(AGENT_DIR)])
    mcps = json.dumps(["agentcore-gateway"])
    configuration = json.dumps(
        {
            "avatar": "🧩",
            "permission_mode": "default",
            "max_turns": 50,
            "soul_enabled": False,
            "scheduler_enabled": False,
            "heartbeat_enabled": False,
            "env_vars": {},
            "agentcore": {
                "client_key": CLIENT_KEY,
                "agent_key": AGENT_KEY,
                "capability_profile": "builder",
            },
        }
    )
    # Preserve existing model if present; otherwise leave a conservative placeholder.
    con = sqlite3.connect(str(AGENTS_DB))
    try:
        row = con.execute("SELECT model FROM agents WHERE id = ?", (AGENT_ID,)).fetchone()
        model = row[0] if row and row[0] else "cherryin:agent/deepseek-v4-pro"
        if row:
            con.execute(
                """
                UPDATE agents SET
                  type = ?, name = ?, description = ?, accessible_paths = ?,
                  instructions = ?, model = ?, mcps = ?, allowed_tools = ?,
                  configuration = ?, updated_at = ?, deleted_at = NULL
                WHERE id = ?
                """,
                (
                    "claude-code",
                    AGENT_NAME,
                    "Governed non-Swarm AgentCore workspace agent (gateway-only MCP).",
                    accessible,
                    prompt,
                    model,
                    mcps,
                    None,
                    configuration,
                    now,
                    AGENT_ID,
                ),
            )
            print(f"agent_updated id={AGENT_ID}")
        else:
            # sort_order: place after built-ins (which use negative orders)
            max_sort = con.execute(
                "SELECT COALESCE(MAX(sort_order), 0) FROM agents WHERE deleted_at IS NULL"
            ).fetchone()[0]
            con.execute(
                """
                INSERT INTO agents (
                  id, type, name, description, accessible_paths, instructions,
                  model, plan_model, small_model, mcps, allowed_tools, configuration,
                  created_at, updated_at, sort_order, deleted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, NULL, ?, ?, ?, ?, NULL)
                """,
                (
                    AGENT_ID,
                    "claude-code",
                    AGENT_NAME,
                    "Governed non-Swarm AgentCore workspace agent (gateway-only MCP).",
                    accessible,
                    prompt,
                    model,
                    mcps,
                    configuration,
                    now,
                    now,
                    int(max_sort) + 1,
                ),
            )
            print(f"agent_created id={AGENT_ID}")
        con.commit()
    finally:
        con.close()


def ensure_developer_mode(desired: bool | None = None) -> dict:
    """Read/optionally set config.json enableDeveloperMode. Returns prior+current."""
    cfg = {}
    if CONFIG_JSON.is_file():
        cfg = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
    prior = bool(cfg.get("enableDeveloperMode", False))
    if desired is None:
        return {"prior": prior, "current": prior, "changed": False}
    cfg["enableDeveloperMode"] = bool(desired)
    CONFIG_JSON.write_text(json.dumps(cfg, indent="\t") + "\n", encoding="utf-8")
    return {"prior": prior, "current": bool(desired), "changed": prior != bool(desired)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--set-developer-mode", choices=["on", "off", "leave"], default="leave")
    args = parser.parse_args()

    if not AGENTS_DB.is_file():
        print("ERROR: agents.db not found")
        return 2
    if not PROMPT_PATH.is_file():
        print("ERROR: prompt missing", PROMPT_PATH)
        return 2
    prompt = PROMPT_PATH.read_text(encoding="utf-8").strip() + "\n"

    if not args.apply:
        print("DRY_RUN agent_id=", AGENT_ID, "prompt_chars=", len(prompt))
        print("approved_skills=", APPROVED_SKILLS)
        print("re-run with --apply after Cherry is quit")
        return 0

    if cherry_running():
        print("ERROR: Cherry Studio is running. Quit fully before configuring Agent.")
        return 3

    AGENT_DIR.mkdir(parents=True, exist_ok=True)
    (AGENT_DIR / "USER.md").write_text(
        "# AgentCore Workspace\n\nGoverned AgentCore client workspace. Canonical memory is AgentCore, not Cherry local memory.\n",
        encoding="utf-8",
    )
    mounted = sync_skills()
    upsert_agent(prompt)
    if args.set_developer_mode != "leave":
        result = ensure_developer_mode(args.set_developer_mode == "on")
        print("developer_mode", json.dumps(result))
    print(f"mounted_skills={mounted}")
    print("CONFIGURE_AGENT=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
