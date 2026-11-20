# Workstation Parallel Subagent Infrastructure (Pi)

**Status:** Governed Bifrost HTTP MCP `agent-dispatch` (AUTH-2026-11-20-AGENT-DISPATCH-LIVE); the Pi-only `pi-agents` shim (AUTH-2026-10-23-PI-BIFROST-HTTP-SHIM) is retired and rollback-only; host-native fallback remains
**Engine:** @earendil-works/pi-coding-agent v1.4.0
**Machine spec:** C:\Users\ynotf\.pi\agent\SWARM_CAPABILITIES.md (not committed; workstation-local)
**Bifrost registry:** `agent-dispatch` is `active` HTTP on `http://127.0.0.1:18092/mcp` (builder/ide/grokbot profiles, Code Mode) and fronts Pi plus OpenHands, OpenCode, Codex, M6 LangGraph and Paperclip. The Pi-only `pi-agents` shim on `http://127.0.0.1:18091/mcp` is retired (`enabled=false`) as of AUTH-2026-11-20-AGENT-DISPATCH-LIVE and is no longer started by the gateway start script.

## Naming boundary

"Pi subagent swarm" means this local parallel executor only. It is **not** the foreign Swarm
ecosystem (SwarmClaw, SwarmVault, SwarmRecall execution). Do not bridge Pi into Swarm roots on H:.

## Why the HTTP shim (not sticky STDIO)

Bifrost runs as scheduled task `\AgentCore\AgentCore-Bifrost-Gateway` with cwd under
`F:\AgentCore\runtime\bifrost`. The Pi MCP bridge defaults subagent cwd to `cwd or process.cwd()`.
Sticky Bifrost STDIO would execute under F:\AgentCore\runtime\bifrost. The `agent-dispatch` MCP on 18092 injects the enrolled project cwd and isolates children per project. Phase 3b siblings stay dormant until they have their own shims.

## Access paths

1. Governed path: `agentcore-gateway` > `agent-dispatch` HTTP MCP (`Start-AgentCoreAgentDispatch.ps1`, Direct-launch only, no scheduled task; silent watchdog `AgentCore-AgentDispatch-Watchdog`) exposing:
   `agents_list`, `agent_run`, `agents_parallel`, `job_status`, `job_result`, `job_cancel`. Pi is reached as `agent_run(agent="pi")`; OpenHands, OpenCode, Codex, M6 LangGraph and Paperclip share the same six tools.
2. Fallback CLI: `pi.cmd` on User PATH (engine home `C:\Users\ynotf\.pi\agent\`)

## Roles and models

| Role | Model | Access |
| --- | --- | --- |
| scout | openrouter/deepseek/deepseek-v4-pro-0813 | read-oriented recon |
| planner | openrouter/deepseek/deepseek-v4-pro-0813 | read-only planning |
| worker | openrouter/deepseek/deepseek-v4-pro-0813 | write-capable implementation |
| reviewer | openrouter/deepseek/deepseek-v4-pro-0813 | read-only audit |
| multimodal | openrouter/minimax/minimax-m3 | vision/UI |

Credentials: Windows User-scope `OPENROUTER_API_KEY` only. No `.env` files.

## Delegation law

See `contracts/global-agent-policy.yaml` rule `workstation-parallel-subagents` and tool gate `agent-dispatch`.
Always pass an explicit enrolled project cwd on D:. Canonical portable templates live in `global-subagents/`.

## Storage and database boundaries

- No raw SQL to PostgreSQL 18 (`127.0.0.1:55433`)
- No rogue vector/memory databases
- Durable memory: `agentcore-gateway` to `agentcore-memory` only
- Denied write roots: `F:\PostgreSQL18\data`, `F:\AgentCore`, `H:`, `E:` backup/archive

## Portability

Do not hardcode machine-local Windows paths into portable product repositories. Control-plane
contracts may record workstation paths for this PC; product repos use relative/portable guidance.

## Rollback

- Set registry `agent-dispatch.enabled=false`, re-render, and stop 18092 (`Start-AgentCoreAgentDispatch.ps1 -Stop`)
- To restore Pi-only access: set `pi-agents.enabled=true`, re-add it to builder/ide/grokbot, restore the gateway start call, start 18091
- Restore contracts from `audits/rollback/AUTH-2026-11-20-AGENT-DISPATCH-LIVE/` (this change) or `.agentcore/rollback/20261023-214428-pi-parallel-subagent-infra/` (the original Pi shim change)
