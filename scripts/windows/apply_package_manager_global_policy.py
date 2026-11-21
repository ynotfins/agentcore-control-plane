#!/usr/bin/env python3
"""Apply workstation package-manager policy into AgentCore global rules.

Operator approval: AUTH-2026-09-22-WORKSTATION-PACKAGE-MANAGERS
Canonical edit: contracts/global-agent-policy.yaml → render_ide_rules.py
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(r"D:\github\agentcore-control-plane")
POLICY = REPO / "contracts" / "global-agent-policy.yaml"
ROLLBACK_DIR = REPO / ".agentcore" / "rollback" / "20260922-193000-workstation-package-managers"
APPROVAL = "AUTH-2026-09-22-WORKSTATION-PACKAGE-MANAGERS"
NEW_REVISION = "2026-09-22-workstation-package-managers-v1"

NEW_RULE = {
    "id": "workstation-package-managers",
    "title": "Workstation package managers (Windows dual-support)",
    "rule": (
        "This Windows workstation uses dual package-manager support, not a forced monolith. "
        "Corepack stays DISABLED: do not run corepack enable, and never put "
        "%LOCALAPPDATA%\\Corepack\\shims on PATH while Node's Corepack package is incomplete "
        "(Node 26.x on this PC). Lockfile wins: package-lock.json only → npm; pnpm-lock.yaml → pnpm "
        "(via npm-global pnpm under %AppData%\\npm); yarn.lock → yarn if installed globally. "
        "If both npm and pnpm lockfiles exist, stop and ask. RGDS "
        "(D:\\github\\r3lentless-grind-design-system) and AgentCore design pins "
        "(docs/design/m3/package-pins.json) use npm workspaces / npm install --save-exact only — "
        "do not migrate them to pnpm mid-release. Preserve PNPM_HOME "
        "(%LOCALAPPDATA%\\pnpm), the H:\\DevCache\\pnpm store, and Bifrost MCP launchers that pin "
        "%LOCALAPPDATA%\\pnpm\\bin\\node.EXE. packageManager fields are documentation/CI hints on "
        "this PC and do not auto-switch versions without Corepack. Publish @r3lentless/* with npm; "
        "keep registry tokens in user npmrc / Windows User env — never Git. Authority: "
        "docs/operations/WORKSTATION_PACKAGE_MANAGERS.md; repair script: "
        "scripts/windows/Repair-WorkstationPackageManagers.ps1."
    ),
}

FORBIDDEN_ADDITIONS = [
    "corepack enable / Corepack shims on PATH while Node Corepack package is incomplete",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unlock(path: Path) -> None:
    if not path.exists():
        return
    try:
        import ctypes

        FILE_ATTRIBUTE_NORMAL = 0x80
        ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_NORMAL)
    except Exception:
        pass
    try:
        path.chmod(path.stat().st_mode | 0o222)
    except OSError:
        pass


def relock(path: Path) -> None:
    if not path.exists():
        return
    try:
        import ctypes

        FILE_ATTRIBUTE_READONLY = 0x01
        ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_READONLY)
    except Exception:
        try:
            path.chmod(path.stat().st_mode & ~0o222)
        except OSError:
            pass


def patch_policy(text: str) -> str:
    text = re.sub(
        r'^policy_revision:\s*".*?"',
        f'policy_revision: "{NEW_REVISION}"',
        text,
        count=1,
        flags=re.M,
    )
    if "id: workstation-package-managers" in text:
        print("policy already contains workstation-package-managers rule")
    else:
        anchor = "  - id: cursor-prompt-path-format"
        if anchor not in text:
            raise SystemExit("anchor cursor-prompt-path-format not found")
        block = (
            "  - id: workstation-package-managers\n"
            "    title: Workstation package managers (Windows dual-support)\n"
            "    rule: >-\n"
            "      This Windows workstation uses dual package-manager support, not a forced monolith. "
            "Corepack stays DISABLED: do not run corepack enable, and never put "
            "%LOCALAPPDATA%\\Corepack\\shims on PATH while Node's Corepack package is incomplete "
            "(Node 26.x on this PC). Lockfile wins: package-lock.json only → npm; pnpm-lock.yaml → pnpm "
            "(via npm-global pnpm under %AppData%\\npm); yarn.lock → yarn if installed globally. "
            "If both npm and pnpm lockfiles exist, stop and ask. RGDS "
            "(D:\\github\\r3lentless-grind-design-system) and AgentCore design pins "
            "(docs/design/m3/package-pins.json) use npm workspaces / npm install --save-exact only — "
            "do not migrate them to pnpm mid-release. Preserve PNPM_HOME "
            "(%LOCALAPPDATA%\\pnpm), the H:\\DevCache\\pnpm store, and Bifrost MCP launchers that pin "
            "%LOCALAPPDATA%\\pnpm\\bin\\node.EXE. packageManager fields are documentation/CI hints on "
            "this PC and do not auto-switch versions without Corepack. Publish @r3lentless/* with npm; "
            "keep registry tokens in user npmrc / Windows User env — never Git. Authority: "
            "docs/operations/WORKSTATION_PACKAGE_MANAGERS.md; repair script: "
            "scripts/windows/Repair-WorkstationPackageManagers.ps1.\n\n"
        )
        text = text.replace(anchor, block + anchor, 1)

    # Forbidden-route placement is handled by fix_forbidden_route_placement().

    ref_line = (
        "  workstation_package_managers: docs/operations/WORKSTATION_PACKAGE_MANAGERS.md\n"
    )
    if "workstation_package_managers:" not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += ref_line
    return text


def update_agents_md() -> None:
    path = REPO / "AGENTS.md"
    text = path.read_text(encoding="utf-8")
    bullet = (
        "- **Workstation package managers (2026-09-22):** Corepack DISABLED on this PC. "
        "Dual-support: lockfile wins (npm vs pnpm vs yarn). RGDS and AgentCore "
        "`docs/design/m3/package-pins.json` use npm exact installs. pnpm via "
        "`npm install -g pnpm` → `%AppData%\\npm`. Authority: "
        "`docs/operations/WORKSTATION_PACKAGE_MANAGERS.md`.\n"
    )
    if "Workstation package managers (2026-09-22)" in text:
        return
    marker = "## Learned Workspace Facts"
    if marker not in text:
        # Append under Learned User Preferences if needed
        if "## Learned User Preferences" in text:
            # insert before end of file after preferences section - find Learned Workspace Facts alternate
            text = text.rstrip() + "\n\n## Learned Workspace Facts\n\n" + bullet
        else:
            text = text.rstrip() + "\n\n" + bullet
    else:
        # Insert as first fact after heading
        text = text.replace(marker + "\n", marker + "\n" + bullet, 1)
    path.write_text(text, encoding="utf-8")


def update_cursorrules() -> None:
    path = REPO / ".cursorrules"
    text = path.read_text(encoding="utf-8")
    old = (
        "2. Install **exact** versions from `docs/design/m3/package-pins.json` using package managers "
        "(`npm install --save-exact …`). Allowed tools: npm/pnpm/yarn/pip only for listed pins — never random latest."
    )
    new = (
        "2. Install **exact** versions from `docs/design/m3/package-pins.json` with "
        "`npm install --save-exact …` (RGDS / AgentCore design pins are npm-only). "
        "For other repos, lockfile wins (npm / pnpm / yarn) per "
        "`docs/operations/WORKSTATION_PACKAGE_MANAGERS.md`. Corepack stays disabled on this PC. "
        "Never unpinned `latest`."
    )
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
    elif "WORKSTATION_PACKAGE_MANAGERS.md" not in text:
        # soft append under bootstrap section if phrasing drifted
        path.write_text(text.rstrip() + "\n\n## Workstation package managers\n\n" + new + "\n", encoding="utf-8")


def update_design_system_mdc() -> None:
    path = REPO / ".cursor" / "rules" / "design-system-m3.mdc"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    old = (
        "7. **Bootstrap deps.** New UI projects install **pinned** packages from "
        "`docs/design/m3/package-pins.json` via `npm install --save-exact …` (or equivalent). "
        "Do **not** run unpinned `npx`/`npm install` “latest”. Do **not** invent alternate design kits."
    )
    new = (
        "7. **Bootstrap deps.** New UI projects install **pinned** packages from "
        "`docs/design/m3/package-pins.json` via `npm install --save-exact …` only (npm, not pnpm/Corepack). "
        "Do **not** run unpinned `npx`/`npm install` “latest”. Do **not** invent alternate design kits. "
        "Workstation package-manager policy: `docs/operations/WORKSTATION_PACKAGE_MANAGERS.md`."
    )
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_canonical_global_rules(policy: dict) -> None:
    path = REPO / "rules" / "canonical" / "GLOBAL_AGENT_RULES.md"
    lines = [
        "# Canonical Global Agent Rules",
        "",
        f"**Source of truth:** `contracts/global-agent-policy.yaml` (policy_revision {policy['policy_revision']}).",
        "This file is the human-readable rendering. Per-IDE renderings live under `ide-profiles/<ide>/GLOBAL_RULES.md` and must not contradict it.",
        "",
        "## Mandatory rules",
        "",
    ]
    for i, rule in enumerate(policy["mandatory_rules"], start=1):
        lines.append(f"{i}. **{rule['title']}.** {rule['rule']}")
    lines.append("")
    lines.append("## Forbidden routes")
    lines.append("")
    lines.append(" · ".join(f"`{x}`" for x in policy["forbidden_routes"]))
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def install_cursor_foundation() -> None:
    rendered = (REPO / "ide-profiles" / "cursor" / "GLOBAL_RULES.md").read_text(encoding="utf-8")
    body = (
        "---\n"
        "description: Current AgentCore foundation policy for Cursor.\n"
        'globs: ["**/*"]\n'
        "alwaysApply: true\n"
        "---\n\n"
        + rendered
    )
    staging = REPO / "ide-profiles" / "cursor" / "staging" / "agentcore-foundation.mdc"
    staging.parent.mkdir(parents=True, exist_ok=True)
    staging.write_text(body, encoding="utf-8")

    live = Path(r"C:\Users\ynotf\.cursor\rules\agentcore-foundation.mdc")
    if live.is_file():
        backup = live.with_suffix(
            f".mdc.bak-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        )
        shutil.copy2(live, backup)
        print(f"foundation backup: {backup}")
    live.parent.mkdir(parents=True, exist_ok=True)
    live.write_text(body, encoding="utf-8")
    print(f"foundation installed: {live}")


def update_external_ops_status() -> None:
    path = REPO / "audits" / "rgds" / "EXTERNAL_OPS_STATUS.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    old = (
        "**Keep npm + package-lock.json** for RGDS (see `docs/PACKAGE_MANAGER.md`). "
        "Workstation Corepack/pnpm is broken/incomplete; not a reason to migrate mid-1.0.0."
    )
    new = (
        "**Keep npm + package-lock.json** for RGDS (see repo `docs/PACKAGE_MANAGER.md` and "
        "AgentCore `docs/operations/WORKSTATION_PACKAGE_MANAGERS.md`). Workstation Corepack is "
        "**disabled by policy**; pnpm remains available via npm-global for pnpm-lock repos — "
        "not a reason to migrate RGDS mid-1.0.0."
    )
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")


def fix_forbidden_route_placement(text: str) -> str:
    """Ensure the Corepack forbidden entry is under forbidden_routes, not task_class_gates."""
    item = FORBIDDEN_ADDITIONS[0]
    # Remove any misplaced list entry immediately before references:
    text = text.replace(f'  - "{item}"\nreferences:', "references:", 1)
    text = text.replace(f"  - {item}\nreferences:", "references:", 1)
    forbidden_block = text.split("forbidden_routes:", 1)[1].split("task_class_gates:", 1)[0]
    if item not in forbidden_block:
        needle = (
            "  - port 65432 as a direct AgentCore or IDE route; the neutral Recall service "
            "may own that backend only behind agentcore-memory\n"
        )
        if needle not in text:
            raise SystemExit("forbidden_routes port 65432 anchor missing")
        text = text.replace(needle, needle + f"  - {item}\n", 1)
    return text


def main() -> int:
    print(f"approval={APPROVAL}")
    ROLLBACK_DIR.mkdir(parents=True, exist_ok=True)
    if not (ROLLBACK_DIR / "contracts__global-agent-policy.yaml").is_file():
        before = sha256(POLICY)
        shutil.copy2(POLICY, ROLLBACK_DIR / "contracts__global-agent-policy.yaml")
        (ROLLBACK_DIR / "BEFORE_SHA256.txt").write_text(before + "\n", encoding="utf-8")
        print(f"rollback before sha256={before}")
    else:
        print("rollback already present; skipping copy")

    unlock(POLICY)
    original = POLICY.read_text(encoding="utf-8")
    if "id: workstation-package-managers" not in original:
        patched = patch_policy(original)
    else:
        patched = original
    patched = fix_forbidden_route_placement(patched)
    POLICY.write_text(patched, encoding="utf-8", newline="\n")
    after = sha256(POLICY)
    (ROLLBACK_DIR / "AFTER_SHA256.txt").write_text(after + "\n", encoding="utf-8")
    print(f"policy after sha256={after}")

    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    assert policy["policy_revision"] == NEW_REVISION
    assert any(r["id"] == "workstation-package-managers" for r in policy["mandatory_rules"])
    assert all(isinstance(g, dict) for g in policy["task_class_gates"])
    assert any("corepack enable" in x for x in policy["forbidden_routes"])

    # Render all IDE GLOBAL_RULES / INSTALL / VALIDATION
    render = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "render_ide_rules.py")],
        cwd=str(REPO),
        check=False,
    )
    if render.returncode != 0:
        print("render_ide_rules.py failed", render.returncode)
        return render.returncode

    check = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "render_ide_rules.py"), "--check"],
        cwd=str(REPO),
        check=False,
    )
    print(f"render --check exit={check.returncode}")

    update_canonical_global_rules(policy)
    update_agents_md()
    update_cursorrules()
    update_design_system_mdc()
    update_external_ops_status()
    install_cursor_foundation()

    # Expand WORKSTATION doc pointer to policy revision
    ops = REPO / "docs" / "operations" / "WORKSTATION_PACKAGE_MANAGERS.md"
    if ops.is_file():
        ops_text = ops.read_text(encoding="utf-8")
        note = (
            f"\n## Global rule propagation\n\n"
            f"Canonical mandatory rule id `workstation-package-managers` lives in "
            f"`contracts/global-agent-policy.yaml` (policy_revision `{NEW_REVISION}`), "
            f"approval `{APPROVAL}`. All `ide-profiles/*/GLOBAL_RULES.md` and the Cursor "
            f"foundation rule are derived renderings.\n"
        )
        if "Global rule propagation" not in ops_text:
            ops.write_text(ops_text.rstrip() + "\n" + note, encoding="utf-8")

    relock(POLICY)
    print("policy re-locked read-only")

    # Spot-check one rendered file
    cursor_rules = (REPO / "ide-profiles" / "cursor" / "GLOBAL_RULES.md").read_text(encoding="utf-8")
    if "Workstation package managers" not in cursor_rules:
        print("FAIL: cursor GLOBAL_RULES missing new rule title")
        return 2
    print("PASS: cursor GLOBAL_RULES contains Workstation package managers")
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
