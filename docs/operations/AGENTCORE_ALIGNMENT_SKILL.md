# AgentCore Alignment Skill

**Canonical source:** `skills/agentcore-project-lifecycle/`  
**Host manifest:** `contracts/agentcore-alignment-skill-hosts.json`  
**Authority:** `PROJECT_ANCHOR.md` → `DOC_AUTHORITY.md` → locked `BLUEPRINT.md` → `CONTEXT_BLOCK.md`

## Purpose

The lifecycle skill gives every AgentCore-capable agent the same task classification, memory lifecycle, generated-STATE rules, progressive tool routing, validation, and completion contract. It does not create a new runtime, database, gateway, or memory authority.

The skill is deliberately conditional. It requires the correct tool for the task class; it does not load Serena, Depwire, Tentra, Context Fabric, or every MCP server on every turn.

## Delivery model

- Cursor, Codex, Claude Code, and the empirically supported MiniMax data root receive hash-matched native skill copies.
- Claude Desktop, Antigravity, Open Interpreter, Cherry Studio, and MiniMax Classic use their governed generated-rule or prompt adapter until native skill discovery is proven.
- LangGraph receives the hash-pinned skill capsule through `contracts/context-engine-execution-catalog.json`.
- SwarmClaw receives no AgentCore skill install. Its equivalent adapter belongs to `D:\github\swarm-ecosystem-control` and must preserve Swarm authority.

This is one semantic contract with host-specific adapters, not multiple competing copies of architecture authority.

## Verify source and adapters

```powershell
& D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe D:\github\agentcore-control-plane\scripts\validate_agentcore_alignment_skill.py
& D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe D:\github\agentcore-control-plane\scripts\install_agentcore_alignment_skill.py --json
```

The second command is read-only. It reports host status and hash drift.

## Install supported native copies

```powershell
& D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe D:\github\agentcore-control-plane\scripts\install_agentcore_alignment_skill.py --apply --json
```

The installer backs up every existing target it replaces under `E:\AgentCore-Backups\agentcore-alignment-skill\<UTC timestamp>\`.

Installation is staged beside the exact allowlisted skill leaf, hash-verified, and swapped into place. If staging or verification fails, the installer restores the prior directory automatically. It refuses any manifest target that is not the exact `agentcore-project-lifecycle` leaf under the approved host skill root.

To restore a replaced prior copy manually, use the backup path reported by the installer. Validate the exact target before moving it, then restore only that skill leaf. Example for Cursor:

```powershell
$Target = 'C:\Users\ynotf\.cursor\skills\agentcore-project-lifecycle'
$Backup = 'E:\AgentCore-Backups\agentcore-alignment-skill\<UTC timestamp>\cursor'
if ((Split-Path -Leaf $Target) -ne 'agentcore-project-lifecycle') { throw 'unsafe target' }
if (-not (Test-Path -LiteralPath $Backup)) { throw 'backup missing' }
$Quarantine = "$Target.failed-restore-$(Get-Date -Format yyyyMMddHHmmss)"
if (Test-Path -LiteralPath $Target) { Move-Item -LiteralPath $Target -Destination $Quarantine }
Copy-Item -LiteralPath $Backup -Destination $Target -Recurse
```

The quarantine is intentionally retained until the restored hash and host behavior are verified.

File installation yields `installed_unverified`, not `live_validated`. Open a fresh task in each host and prove skill discovery, correct project classification, gateway-only routing, signed memory lifecycle, generated-STATE behavior, and the applicable task-class tool gate.

## Hardening boundary

Do not harden or force full synchronous claims until:

1. **Passed:** Context Engine v0.2.4 is installed and live-validated at exact artifact commit `789b42a12e55a98e71327a8ce6c49f30320f2143`.
2. **Passed:** LangGraph production run `cdb3a8ae-346e-4798-9477-fcee962280f6` completed the hash-pinned capsule canary with a system-verified 3-byte/SHA-256 artifact manifest, strict-schema critic pass, and 13 checkpoints.
3. **Pending:** SwarmClaw independently validates its Swarm-owned adapter and native stores.
4. **Pending per host:** each IDE advances from `installed_unverified` or adapter-only status only after fresh-task discovery proof.
5. **Continuous invariant:** no direct Recall, SQL, duplicate MCP, shared implicit-project tool, or cross-runtime state route exists.

`BLUEPRINT.md` remains unchanged and authoritative throughout this polish phase.
