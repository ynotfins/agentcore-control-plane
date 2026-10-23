# Proposal: Workstation Parallel Subagent Infrastructure (Pi Swarm)

**Date:** 2026-10-22
**Status:** Applied under plan approval AUTH-2026-10-22-PI-SUBAGENT-PARALLEL-INFRASTRUCTURE
**Approval ID:** AUTH-2026-10-22-PI-SUBAGENT-PARALLEL-INFRASTRUCTURE
**Rollback:** .agentcore/rollback/20261023-214428-pi-parallel-subagent-infra/

## Intent

Formalize the workstation Pi coding-agent harness (@earendil-works/pi-coding-agent v1.4.0) as AgentCore-governed parallel subagent infrastructure: host-native companion for live IDE use, dormant Bifrost registry entry, policy delegation law, canonical subagent templates, and ops documentation. Distinct from the foreign Swarm ecosystem (SwarmClaw / SwarmVault).

## Architecture decision (Tier 1)

pi-agents stays an **approved host-native MCP companion** under AUTH-2026-09-05-UNIVERSAL-IDE-BIFROST-SKILLS-ALIGNMENT. It is **not** enabled as an active Bifrost upstream.

Rationale: Bifrost scheduled-task cwd is F:\\AgentCore\\runtime\\bifrost. The Pi MCP bridge defaults to cwd || process.cwd(). Active Bifrost exposure without trustworthy per-call project cwd would execute subagents under AgentCore hot runtime and violate drive isolation. Same pattern as dormant shared Depwire / Tentra / Context Fabric.

## Changes in this AUTH window

### Governed mutable

- contracts/global-agent-policy.yaml — companion exception + workstation-parallel-subagents rule + pi-agents task gate; policy_revision bump
- contracts/bifrost-upstream-mcp-registry.json — dormant pi-agents registry entry (nabled=false, empty profiles)
- docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md — catalog row + host-companion note
- DOC_AUTHORITY.md — index ops runbook
- CONTEXT_BLOCK.md — current-state posture note

### Normal workstream

- contracts/mcp-tool-output-schemas.json — pi-agents adapter entry
- global-subagents/{scout,planner,worker,reviewer,multimodal}.md — portable templates
- docs/operations/WORKSTATION_PARALLEL_SUBAGENT_INFRASTRUCTURE.md — workstation truth / runbook
- ide-profiles/*/GLOBAL_RULES.md — regenerated from policy

## Non-goals

- No .env files; OpenRouter uses Windows User $env:OPENROUTER_API_KEY only
- No SwarmVault / SwarmClaw bridge
- No hardcoding machine paths into portable product repos
- No enabling pi-agents in Bifrost capability profiles
- No direct PostgreSQL or rogue vector/memory stores for Pi subagents

## Acceptance

1. scripts/.venv/Scripts/python.exe scripts/bifrost/validate_contracts.py exit 0
2. scripts/.venv/Scripts/python.exe scripts/render_ide_rules.py --check exit 0
3. Secret scan clean; no raw DB credentials or API key literals
4. Drive/DB/memory boundaries stated in policy and ops doc
