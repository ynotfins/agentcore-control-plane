# Workstation Parallel Subagent Infrastructure (Pi)

**Status:** Governed Bifrost HTTP session shim (AUTH-2026-10-23-PI-BIFROST-HTTP-SHIM); host-native fallback remains
**Engine:** @earendil-works/pi-coding-agent v1.4.0
**Machine spec:** C:\Users\ynotf\.pi\agent\SWARM_CAPABILITIES.md (not committed; workstation-local)
**Bifrost registry:** `pi-agents` is `active` HTTP on `http://127.0.0.1:18091/mcp` (builder profile, Code Mode)

## Naming boundary

"Pi subagent swarm" means this local parallel executor only. It is **not** the foreign Swarm
ecosystem (SwarmClaw, SwarmVault, SwarmRecall execution). Do not bridge Pi into Swarm roots on H:.

## Why the HTTP shim (not sticky STDIO)

Bifrost runs as scheduled task `\AgentCore\AgentCore-Bifrost-Gateway` with cwd under
`F:\AgentCore\runtime\bifrost`. The Pi MCP bridge defaults subagent cwd to `cwd or process.cwd()`.
Sticky Bifrost STDIO would execute under F:\AgentCore\runtime\bifrost. The HTTP shim on 18091 injects the enrolled project cwd and isolates children per project. Phase 3b siblings stay dormant until they have their own shims.

## Access paths

1. Governed path: `agentcore-gateway` > `pi-agents` HTTP shim (`Start-AgentCorePiSessionShim.ps1`, Direct-launch only, no scheduled task) exposing:
   `pi_list_agents`, `pi_run_agent`, `pi_parallel_agents`, `pi_chain_workflow`
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

See `contracts/global-agent-policy.yaml` rule `workstation-parallel-subagents` and task gate `pi-agents`.
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

- Remove host `pi-agents` MCP entries from IDE configs
- Set registry `enabled=false`, remove `pi-agents` from builder.allowed_server_ids, stop 18091
- Restore contracts from `.agentcore/rollback/20261023-214428-pi-parallel-subagent-infra/`
