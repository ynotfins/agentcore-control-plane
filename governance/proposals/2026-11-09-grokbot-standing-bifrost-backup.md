# Proposal: Grok Bot standing Bifrost / control-plane backup (operator decision 1B)

Date: 2026-11-09  
Status: PROPOSED — apply bounded repo artifacts; AGENTS.md wording remains proposal-only until UNLOCK path  
AUTH id: `AUTH-2026-11-09-GROKBOT-STANDING-BIFROST-BACKUP`  
Capability: `authority_maintainer` (Cursor remains sole primary when available)

## Decision summary (1B)

| Role | When | Scope |
| --- | --- | --- |
| **Cursor** | Default; whenever the Cursor IDE is usable on ChaosCentral | Sole **primary** owner of the Bifrost MCP contract plane (unchanged 2026-09-08 baseline) |
| **Grok Bot (Grokbot)** | **Standing backup** when the operator declares Cursor unavailable **or** Cursor IDE is not usable for the needed Bifrost/control-plane work | Bounded edits and live ops listed below — not dual-primary |

Grokbot backup is **standing**, not temporary delegation only. Cursor resumes primary ownership when available. Grokbot must not treat backup as dual-primary promotion.

## Backup scope (when active)

Repositories (exact enrolled roots only):

- `D:\github\agentcore-control-plane` — `project_key`: `agentcore-control-plane`
- `D:\postgreSQL18-control-plane` — `project_key`: `postgresql18-control-plane`

In-scope: Bifrost contracts/renderers/validators/scripts in agentcore-control-plane; `ops/bifrost` apply/restart/acceptance via existing scripts or `Invoke-AgentCoreBifrostLifecycleForGrokbot.ps1`.

Out of scope: Stage B weakening; permanent operator/project-router on Grokbot VK profile; tunnel recreate or VK rotation; Grokbot automation ownership; enrolling `C:\Users\ynotf\.grokbot`.

## Activation triggers

1. Operator states Cursor unavailable for Bifrost/control-plane work, or
2. Cursor IDE not usable on ChaosCentral and operator or primary Bot directs Grokbot recovery.

Log trigger via `agentcore-memory`; reconcile with Cursor when healthy.

## MCP / profile constraints

Trust Class A, `BIFROST_MCP_VK_GROKBOT`, existing grokbot profile only. No permanent operator-router or project-router tools. Workstation lifecycle via repo ops scripts.

## Stage B

Cursor-only. No hook weakening. Morph/Code Mode allowed without disabling gates.

## Proposed AGENTS.md wording (protected — proposal only)

> **Bifrost MCP contract ownership (operator decisions 2026-09-08 primary, 2026-11-09 backup 1B):** Cursor is sole **primary** when available. When Cursor is unavailable, Grok Bot is **standing backup** for the bounded Bifrost MCP plane on enrolled `agentcore-control-plane` and `postgresql18-control-plane` roots — without dual-primary status, Stage B changes, or Grokbot MCP profile widening. Codex remains reviewer/challenge only.

## Applied artifacts

- `ide-profiles/grokbot/GLOBAL_RULES.md`
- `ide-profiles/grokbot/BIFROST_STANDING_BACKUP.md`
- `ops/bifrost/Invoke-AgentCoreBifrostLifecycleForGrokbot.ps1`
- `ide-profiles/grokbot/VALIDATION.md` (optional note)

## Enrollment evidence

`contracts/agentcore-project-enrollment.json`: `agentcore-control-plane` → `D:\github\agentcore-control-plane`; `postgresql18-control-plane` → `D:\postgreSQL18-control-plane`.

Cloud MCP unchanged: `https://agentcore-grokbot.4axe.com/mcp`, task `\AgentCore-Grokbot-Cloudflare-Tunnel` (Hidden).

## Non-goals

No tunnel recreate; DailyDriftCheck unchanged; Swarm startups unchanged.