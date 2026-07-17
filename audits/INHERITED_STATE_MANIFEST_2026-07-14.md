# Inherited State Manifest — 2026-07-14

Classification of every dirty/untracked path found at the start of the authority
reconciliation task on `task/authority-reconciliation` (HEAD `81e90eb`). Files marked
INCLUDE are captured in the checkpoint commit
`chore: checkpoint inherited AgentCore authority reconciliation state`.
Files marked EXCLUDE remain on disk, uncommitted, with the reason recorded.

Scans performed before staging: secret patterns (sk-/ghp_/AIza/Bearer/password),
junk/generated artifacts, oversized files (>1 MB), duplicate detection.

## Tracked modifications — INCLUDE (all)

Origin: completed Bifrost cutover follow-up and prior authority work
(2026-07-13/14 banner passes, registry status syncs, runtime repair evidence).

| File | Origin of change |
| -- | -- |
| `.agentcore/docs/DOCS_INDEX.md` | 2026-07-14 gateway-first docs index refresh |
| `CONTEXT_BLOCK.md` | Full rewrite into PG18/Cognee memory-platform target architecture |
| `DOC_AUTHORITY.md` | 2026-07-14 runtime-repair update; historical rows added |
| `contracts/bifrost-upstream-mcp-registry.json` | `status` field syncs (active → disabled) |
| `contracts/master-mcp-server-config.json` | Legacy-contract reconciliation notes |
| `database-plan.md` | Partial Bifrost-override banner (2026-07-14) |
| `docs/AGENTCORE_LOCAL_MEMORY_HANDOFF.md` | Bifrost-override banner |
| `docs/MCP_SERVER_CONFIGURATION_REFERENCE.md` | Bifrost reconciliation edits |
| `docs/SYSTEM_HANDOVER_BLUEPRINT.md` | Bifrost-override banner |
| `docs/bifrost/CAPABILITY_PROFILES.md` | Profile doc touch-ups |
| `docs/bifrost/MCP_CLASSIFICATION_MATRIX.md` | Classification sync |
| `docs/database_overview.md` | Bifrost-override banner |
| `docs/evidence/PC-Master-Hardware-Software-Specs.md` | Evidence refresh |
| `docs/handoffs/AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md` | 2026-07-14 runtime-repair addendum |
| `docs/prompts/*-cleanup-prompt.md` (8 files) | "Superseded for normal non-Swarm IDE setup" banners |
| `ops/AGENT_CORE_RESTART_CHECKLIST.md` | Restart-owner update after runtime repair |
| `renderers/antigravity.mcp_config.json`, `renderers/cursor-global.mcp.json`, `renderers/minimax.mcp.json`, `renderers/open-interpreter.config.fragment.json`, `renderers/openclaw.openclaw.fragment.json` | Legacy renderer deprecation headers |
| `rules/environment-and-secrets.md` | agentcore-gateway/agentcore-memory identity update |
| `rules/global-mcp-routing.md` | Partial routing updates (still stale; Phase 2 target) |
| `scripts/mcp_control_plane.py` | Legacy pipeline deprecation notes |
| `supervisor/servers.json`, `supervisor/servers.yaml` | Regenerated legacy server model |
| `validators/validate-control-plane.ps1` | Validator adjustments |

## Tracked deletion — INCLUDE

| File | Verdict |
| -- | -- |
| `swarm.zip` (132,003 bytes) | Intentional. Added in Swarm-era commit `7042f84`; removal of a Swarm binary snapshot from the non-Swarm control plane is consistent with the reconciliation. Recoverable at `7042f84:swarm.zip`. |

## Untracked — INCLUDE

| Path | Origin / role |
| -- | -- |
| `MILESTONES.md` | Operator-authored locked memory-platform Milestones M0–M8 (operator evidence; source for `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`) |
| `Global-memory-and-context-system-revised-2.md` | Research input that fed the rewritten CONTEXT_BLOCK.md (receives a do-not-execute historical banner in Phase 2) |
| `Set-AgentCoreSwarmBaseline.ps1` | Swarm-era baseline script (receives a Swarm-only label in Phase 2) |
| `docs/SERENA_CONFIGURATION.md` | Serena configuration documentation from prior work |
| `reports/*.md` (10 files) | Memory-architecture research reports (system inventory, memory stack audit, IDE integration matrix, architecture options, final recommendation, implementation sequence) |
| `reports/_ps/*.ps1` (11 files) | Inventory scripts that generated the reports; secret-scanned clean |

## Untracked — EXCLUDE (left on disk, not committed)

| Path | Reason |
| -- | -- |
| `reports/_raw/` | **SECRET-BEARING.** `peek_configs.txt` line 1231 contains a live `Bearer sk-or-v1-…` OpenRouter API key captured from a live config dump; `openclaw_configs.txt` is 15.3 MB and `peek_configs2.txt` is 2.8 MB of raw live-config dumps (oversized, generated, unreviewed secret surface). Never commit. Ignore rule added in follow-up hygiene commit. |
| `.minimax/` | 344 files / 19.1 MB of vendored MiniMax/OpenClaw skill payloads — third-party skill content, not control-plane policy. Ignore rule added in follow-up hygiene commit. |
| `docs/PC-Master-Hardware-Software-Specs.md` | Duplicate of tracked `docs/evidence/PC-Master-Hardware-Software-Specs.md` with diverged content (hashes differ). Single evidence copy policy: reconcile in Phase 2; not committed as a second copy. Contains a `[REDACTED]` marker (already sanitized). |

## Operator notice

`reports/_raw/peek_configs.txt` holds a live OpenRouter API key copied from
`C:\Users\ynotf\...` config during a prior inventory run. It was never committed to
Git. Recommend rotating that key and deleting `reports/_raw/` after review.
