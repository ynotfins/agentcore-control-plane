# Post-Build Audit

Overall: **partial_with_external_devin_gates**

- open-interpreter-cli: gateway-only
- open-interpreter-desktop: gateway plus documented Codex-inherited transition exceptions
- opencode: gateway-only
- cursor: gateway-only
- zoo-code: gateway-only
- codex: documented transition exception
- devin: local coder path active; Outposts optional only
- openhands: Docker-first Agent Canvas at http://127.0.0.1:8003/canvas/

wslconfig 48/16/16
docker NCPU=32 Mem=67312361472
vhdx docker=97629765632 ext4=117440512
ports bifrost/pg18/recall tcp ok; recall http health 404
gpu NVIDIA GeForce RTX 4070 SUPER
openrouter_present=True foundry_cloud=True foundry_local=False devin_token=False
parked: D docker mcp/n8n/portainer
isolation: four-runtime confirmed
desktop_path=C:\Users\ynotf\OneDrive\Desktop
documents_path=C:\Users\ynotf\Documents

## Four-runtime model

- LangGraph: native on F:/PG18, workflow/checkpoint authority
- SwarmClaw: native on H:, Swarm execution authority
- Devin: local-first coder path with optional Docker Outposts
- OpenHands: Docker-first Agent Canvas on 127.0.0.1:8003, state on I:, projects on D:

## Workstation decisions

- Direct IDE-to-IDE communication is rejected. Use the hub-and-spoke control plane through agentcore-gateway, durable memory, and audit artifacts.
- Devin local execution is the default. No token is needed unless you intentionally use Outposts.
- Outposts remains optional for isolated long-running sessions.
- OneDrive-backed Desktop should not hold active project repositories, local databases, Docker bind roots, or runtime state.
- Codex and Devin direct helpers remain temporary exceptions until governed replacements exist behind the gateway.
- Non-trivial agent work should use planning, semantic code intelligence, dependency graph tools, and durable memory recovery so a vibe coder does not have to keep re-explaining context.

## MAF host follow-up

- import agent_framework 1.15.0 OK
- port 8080 refuse bind confirmed
- provider preference verified: Azure Foundry `deepseek-v4-pro` first, OpenRouter fallback second

## Remaining blockers

The MAF/OpenHands realignment is complete with nonblocking follow-ups, but the broader global Devin autonomous-execution objective is still **PARTIAL**. Current Devin package evidence is under `C:\Users\ynotf\Documents\Codex\2026-08-26\files-pasted-by-the-user-goal\outputs\global-devin-infra`.

Blocking external gates from that package:

- `DEVIN_ADMIN_API_KEY` is not visible to the current Codex/validator process, so admin key role separation and admin Outpost inventory remain blocked.
- Devin admin Outpost inventory remains blocked because the visible default key receives HTTP 403 from the Outpost inventory endpoint.
- Org-tier Devin Blueprint application is still approval/defer gated.
- Zoo Code active Gateway/profile/model/tool-call proof still requires UI proof or the documented IPC closeout path.
- Windows staging remains approval/elevation gated and was not pursued in the current pass.
- Devin still inherits `morph-mcp` from Claude/global MCP config. Codex may keep Morph as a documented transition exception, but Devin should receive shared capability through `agentcore-gateway` or through an explicitly approved cleanup of the Claude/global MCP baseline.

Nonblocking follow-ups for the MAF/OpenHands realignment remain: Foundry Local CLI install decision, optional Docker old-image cleanup, and future hot-swap acceptance gate for a live MAF/Recall adapter.

## Goal Completion Audit

| Requirement | Evidence | State |
|-------------|----------|-------|
| OpenHands startup assets synced | Repo-side assets exist under `scripts/maf_recall/openhands`; mirrored assets exist under `I:/LocalApps/OpenHands`; idempotent launcher verified `/ready` = 200 | complete |
| LangGraph execution layer verified | PG18 `:55433` TCP passed; AgentCore memory status reports LangGraph `m6_integrated` | complete |
| SwarmClaw execution layer verified | `:3456` TCP passed; no AgentCore write to `H:/SwarmData` | complete |
| Devin execution layer verified | Codex Devin report proves local + Docker Outpost path and corrected project-scoped filesystem policy; admin key visibility, Outpost inventory, org Blueprint, Zoo proof, Windows staging, and inherited Morph policy cleanup remain external gates | partial |
| OpenHands execution layer verified | `openhands-local-8003`, `127.0.0.1:8003->8000`, `/ready` 200, no `F:/` or `H:/` mounts | complete |
| MAF/Recall behind `:8080` | Guarded route plan in `maf_host/host.py`; Bifrost remains live; MAF chooses Azure Foundry before OpenRouter | planned/guarded, not hot-swapped |
| IDE MCP convergence | Gateway-only clients verified; Codex/OI Desktop/Devin transition exceptions documented; raw Recall/SQL still forbidden | complete with documented exceptions |
| Project enrollment clean | `repo_enrollment_status.md` records exact repo roots only; staging/runtime roots not blanket identities | complete |
| Final evidence without secrets | Audit JSON validates; targeted secret scan found no matches in realignment package/audit/handoff | complete |

MAF/OpenHands completion evidence is satisfied as of 2026-08-27: OpenHands host mirror exists, the stale created-only placeholder was removed, and the live runtime remains healthy. The full global Devin autonomous-execution objective is not complete until the Devin package aggregate is PASS and the external gates above are closed with non-secret evidence.
