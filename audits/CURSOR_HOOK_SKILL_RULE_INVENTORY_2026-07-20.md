# Cursor Hook / Skill / Rule / Agent Inventory (2026-07-20)

Sanitized inventory of active surfaces that can affect Cursor or Cherry under AgentCore governance. Hashes are SHA-256 of file contents at audit time.

## Classification legend

| Action | Meaning |
| --- | --- |
| retain | Compatible with AgentCore; keep |
| adapt | Useful behavior; must route through AgentCore before re-enable |
| disable | Auto-trigger off; originals preserved |
| quarantine | Do not use for non-Swarm AgentCore work |
| remove-after-approval | Candidate for deletion only with operator approval |

## Continual-learning (critical)

| Name | Path / scope | Trigger | Memory / writes | Alignment | Action |
| --- | --- | --- | --- | --- | --- |
| continual-learning plugin | Cursor plugin cache `continual-learning@3fe2823…` | `stop` → followup_message | Transcripts → AGENTS.md | Parallel memory; user-role injection | **disable** |
| agents-memory-updater | plugin `agents/` | via skill | AGENTS.md | Same | **disable** (auto) |
| continual-learning-index.json | `.cursor/hooks/state/` | updater | Index only | evidence_only metadata | retain (state) |
| update-continual-learning-index.ps1 | `.cursor/hooks/` | manual | Index rebuild | OK as helper | retain |

See `audits/CONTINUAL_LEARNING_AUTOMATION_2026-07-20.md`.

## Project (`D:\github\agentcore-control-plane`)

| Name | Scope | Trigger | Action |
| --- | --- | --- | --- |
| `AGENTS.md` / `CLAUDE.md` | project contracts | always read | retain |
| `.cursor/rules/agentcore-env-policy.mdc` | project rule | always/globs | retain |
| `.cursor/hooks/CONTINUAL_LEARNING_AUTO_TRIGGER_DISABLED.md` | marker | n/a | retain |
| No project `hooks.json` | — | — | n/a |

## Cursor global rules (`C:\Users\ynotf\.cursor\rules`)

Includes: evidence-first, MCP router, arabold-docs, memory-usage, multi-agent, secrets/env, managed configs, drive boundaries, code quality, task completion, background agents, agent-skills, yolo, agentcore-memory, artiforge, autonomous-rule-creation, coding-standards, context-fabric, cursor-rules-meta.

**Action:** retain. None inject user-role prompts. Memory rules must continue to prefer `agentcore-memory` via gateway (not Swarm).

## D-drive / GitHub shared rules

| Path | Notes | Action |
| --- | --- | --- |
| `D:\.cursor\rules\10-autonomous-mcp-routing.mdc` | MCP routing | retain |
| `D:\.cursor\rules\11-depwire-foundation.mdc` | DepWire mandate | retain |
| `D:\.cursor\rules\openmemory.mdc` | OpenMemory phases | **adapt** — must not become parallel durable store vs AgentCore; treat as IDE aid only |
| `D:\github\.cursor\rules\*.mdc` | autopilot / quality helpers | retain / review openmemory overlap |

## Cursor plugins (`~\.cursor\plugins\cache\cursor-public`)

| Plugin | Notes | Action |
| --- | --- | --- |
| continual-learning | stop followup injection | **disable** |
| superpowers | skills + hooks (using-superpowers) | retain (no AGENTS auto-edit observed) |
| context7-plugin | docs | retain |
| cloudflare / firebase / vercel / twilio / cursor-team-kit | domain kits | retain when task-relevant |

## Skills (high level)

| Location | Action |
| --- | --- |
| `~\.cursor\skills-cursor\*` | retain (Cursor product skills) |
| `~\.agents\skills\*` | retain; do not auto-write AgentCore projections |
| `~\.codex\skills\*` | retain for Codex; out of Cherry scope |
| Cherry AgentCore Workspace skills | approved hash-pinned set per `audits/CHERRY_STUDIO_SKILLS_AUDIT_2026-07-19.md` | retain |

## Cherry-specific

| Item | Action |
| --- | --- |
| Agent prompt `docs/prompts/cherry-agentcore-workspace-agent.md` | retain |
| MCP: only `agentcore-gateway` | retain |
| Global Memory OFF | retain |
| Built-in memory MCP | unused | retain unused |
| Unrelated Agents (Cherry Assistant / Claw) | preserve; not AgentCore path | quarantine for AgentCore work |

## AgentCore policy / contracts

| Item | Action |
| --- | --- |
| `contracts/agentcore-gateway-client.json` | retain |
| `contracts/bifrost-upstream-mcp-registry.json` | retain |
| `contracts/global-agent-policy.yaml` | retain |
| `docs/bifrost/CAPABILITY_PROFILES.md` | retain |

## Violations checked (none retained if true)

- Swarm as non-Swarm memory — not in IDE baseline
- Bypass Bifrost for Cherry MCP — not present
- Direct PostgreSQL from IDE — not present
- Auto-edit generated STATE/GLOBAL_STATE — continual-learning targeted AGENTS.md only (now disabled)
- Silent user-role prompt injection — **found and disabled** (continual-learning stop hook)
- Whole-drive filesystem MCP for Cherry — not enrolled
- Secrets in source renderers — validator PASS

## Notes

- Unrelated Studio-interrupt WIP left untouched.
- Plugin cache edits are machine-local; reinstalling the plugin may restore the original stop hook — re-apply disable or uninstall plugin if that happens.
