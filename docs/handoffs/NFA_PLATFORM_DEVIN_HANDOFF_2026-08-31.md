# nfa-platform / Devin — Handoff
**Date:** 2026-08-31 | **Repo:** D:\github\nfa-platform | **Branch:** release-pass/ci-e2e-manifest

## Purpose
This handoff is for a Cursor chat focused on the nfa-platform project and Devin setup. Keep this separate from agentcore-control-plane infrastructure work.

---

## 1. Project snapshot

**What it is:** Flutter multi-app platform (apps/chaser + apps/supe) with a Fastify/PostgreSQL backend.

```
Backend API     : Fastify at 127.0.0.1:3000 (env NFA_API_HOST/NFA_API_PORT)
Database        : PostgreSQL 18 at 127.0.0.1:55433
  - nfa_devin_dev     : main app database
  - nfa_ingest_capture: real-time alert ingest (capture.raw_alerts, 3,571 alerts as of Aug 31 3:23 PM)
Phone ingest    : 127.0.0.1:8787 (Tailscale: https://chaoscentral.tailb71e7e.ts.net/v1/ingest/alerts)
Flutter apps    : apps/chaser (first responder), apps/supe (supervisor)
Firebase        : NOT USED — fully migrated to PostgreSQL
EMU Alerts IDs  : com.emualerts / App ID 841200945180 — CONFIRMED NOT IN THIS PROJECT
```

---

## 2. Devin setup — current state

### Global Devin MCP config (`C:\Users\ynotf\AppData\Roaming\devin\mcp_config.json`)
| Server | Status |
|---|---|
| agentcore-gateway | ✅ Connected — `http://127.0.0.1:8080/mcp` |
| devin/github-mcp-server | ❌ Auth required (GitHub Copilot OAuth) — optional |
| devin/mcp-playwright | ✅ Connected |
| devin/vercel | ❌ Auth required (Vercel OAuth) — optional |
| vercel | ✅ Connected (separate from devin/vercel) |

agentcore-gateway provides 46 tools: arabold-docs, context7, agentcore-memory, sequential-thinking, playwright, morph-mcp, skills-hub, mcp-prompt-optimizer, cursor-agent-mcp, agentcore-project-router.

### Project MCP config (`D:\github\nfa-platform\.devin\mcp.json`) — gitignored, contains resolved secrets
| Server | Status |
|---|---|
| filesystem | ✅ `npx @modelcontextprotocol/server-filesystem D:\github\nfa-platform` |
| depwire | ✅ `C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd mcp` — call `connect_repo` with project path first |
| tentra | ✅ `npx tentra-mcp@1.3.3 --local`, data at `F:\AgentCore\runtime\tentra\data` |
| serena | ⚠️ Configured but NOT yet initialized — needs `serena init` first |

### Serena initialization (one-time, do after reboot)
```powershell
cd D:\github\nfa-platform
& "C:\Users\ynotf\AppData\Roaming\uv\tools\serena-agent\Scripts\serena.exe" init
```
After init, serena will create `.serena/project.yml` and activate in Devin sessions.

### Outpost
- `my-outpost` (Windows) is configured — use this for nfa-platform sessions to get local DB + MCP access
- Default Ubuntu cloud cannot reach 127.0.0.1 services

### Model
- SWE-1.7 Medium (272K context) — stable session persistence
- Tip: `/megaplan` at session start compresses context; use before approaching 200K

---

## 3. Devin session protocol

When starting a new nfa-platform Devin session, send:
```
Read .devin/SESSION_STARTUP.md and follow the session start protocol before doing anything else.
```

SESSION_STARTUP.md tells Devin:
1. Call agentcore_memory startup_context
2. Call depwire connect_repo
3. Read RESTART_RECOVERY.md and .devin/handoffs/
4. Report current milestone, last task, next step

---

## 4. Architecture Critic playbook

Created in Devin org settings:
- Name: `Architecture Critic — Macro Strategic Review`
- Trigger: `!arch-critic`
- Purpose: system-level strategic review (not bugs/code style)
- Instructions: `.devin/CREATE_ARCH_CRITIC_PLAYBOOK.md`

Trigger at Milestone exit for strategic review of overall project design.

---

## 5. Graphify knowledge graph

Generated 2026-08-30, committed to nfa-platform:
- Location: `D:\github\nfa-platform\graphify-out\GRAPH_REPORT.md`
- 4,438 nodes, 5,773 edges, 373 communities
- Key communities: API Response Models, Backend API Logic, Authentication State Management, Chat Business Logic, Realtime WebSocket Client, Incident Data Models, Push Notification Management
- Built from commit `af57a913` — run `graphify update .` after major code changes
- Query: `graphify query . "your question"` before diving into code

---

## 6. Devin settings to optimize (web UI: app.devin.ai)

| Setting | Current | Action |
|---|---|---|
| DeepWiki effort | Low | Change to High |
| Pre-approve testing | Off | Turn On |
| Build snapshot (Windows) | Not built | Click Build snapshot on Windows tab |
| Auto-approve child sessions | On ✅ | Keep |
| Auto-approve workflows | On ✅ | Keep |

---

## 7. Pending items

| Priority | Task |
|---|---|
| HIGH | Run `serena init` in nfa-platform after reboot |
| HIGH | Continue Milestone hardening (was in-progress when context hit 522K) |
| MEDIUM | Verify alert ingest pipeline is still live (last alert 3:23 PM Aug 31 — check after reboot) |
| LOW | Build Windows snapshot in Devin environment settings |
| LOW | Authenticate devin/github-mcp-server (GitHub Copilot OAuth) |

---

## 8. Not wired predictably

- **Devin context overflow (Aug 30)**: session hit 522K/200K tokens mid-Milestone. Root cause: old model subscription expired, dropped to smaller-context model. Fixed: SWE-1.7 Medium now selected.
- **Permission denied error on Aug 30**: caused by non-standard `_note` keys in .devin/mcp.json. Fixed: clean JSON only.
- **.devin/mcp.json is gitignored** — contains resolved secrets. Regenerate from `ide-profiles/devin/MCP_CONFIG_TEMPLATE.json` if lost. Keys needed: BIFROST_MCP_VIRTUAL_KEY (Windows User env, 80 chars), GITHUB_TOKEN (Windows User env, 40 chars).

---

## 9. Cursor continuation prompt

```
@D:\github\nfa-platform\.devin\SESSION_STARTUP.md
@D:\github\agentcore-control-plane\docs\handoffs\NFA_PLATFORM_DEVIN_HANDOFF_2026-08-31.md
@D:\github\nfa-platform\AGENTS.md

Read the handoff doc. Repo: D:\github\nfa-platform, branch: release-pass/ci-e2e-manifest.
Priority 1: Run serena init. Priority 2: Resume Milestone hardening from where Devin left off.
Read .devin/SESSION_STARTUP.md for the full tool inventory and session protocol.
```
