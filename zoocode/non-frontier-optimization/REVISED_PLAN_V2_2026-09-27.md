# REVISED PLAN v2 — Non-Frontier Model Optimization via Bifrost
**Date:** 2026-09-27 · **Supersedes:** `OPTIMIZED_PLAN_2026-09-27.md` (see `SELF_AUDIT_2026-09-27.md` for what changed and why)
**Status:** PLAN ONLY. Nothing applied. Gemini plan remains **INVALID** (reaffirmed — see Self-Audit Q7).
**Scope guard (corrected):** Two distinct planes must not be conflated:
- **MCP tool plane** — owned by `contracts/bifrost-upstream-mcp-registry.json` → `scripts/bifrost/render_bifrost_config.py` → `renderers/bifrost/*` → `ops/bifrost` (Cursor is sole primary owner per AUTH-2026-09-08).
- **Inference/provider/VK plane** — `contracts/openrouter-provider-contract.json`, `APPROVED_OPENROUTER_MODELS` in `scripts/agentcore/workflow_cli.py`, the renderer's hardcoded VK `provider_configs`/`semantic_cache` blocks, and Bifrost runtime governance objects (routing rules live in `config.db`, created via REST — never in the rendered config).

---

## 0. Verified live baseline (do not re-implement)

| Capability | Live evidence |
|---|---|
| Bifrost v2.0.0 gateway, MCP plane, 46+ tools, Code Mode global (`binding_level=tool`) | `audits/bifrost/BIFROST_V2_RUNTIME_ACCEPTANCE_2026-09-05.md`; `audits/bifrost/CODE_MODE_GLOBAL_ENABLE_2026-09-08.md` |
| Morph MCP (Fast Apply `edit_file`, WarpGrep `codebase_search`, `reflex_*`, GitHub search) — all 7 tools, builder-gated | `contracts/bifrost-upstream-mcp-registry.json` (morph-mcp, enabled, pinned @0.8.211) |
| Hash-mode semantic cache — `dimension: 1`, ttl 30m, Redis Stack backend `127.0.0.1:6381`, active | `renderers/bifrost/config.sanitized.json:1446-1455`; acceptance audit lines 34-37 |
| Inference auth enforced (`enforce_auth_on_inference: true`); builder VK provider_configs openai+openrouter `allowed_models:["*"]` | `renderers/bifrost/config.sanitized.json:741-840,966-978` |
| Approved OpenRouter models (workflow plane): `google/gemini-3.6-flash`, `minimax/minimax-m3`, `deepseek/deepseek-v4-pro`, `deepseek/deepseek-v4-flash`, `openai/gpt-5.6-sol`, `minimax/minimax-m2.7`, `tencent/hy3:free` | `scripts/agentcore/workflow_cli.py:1236-1244`; `contracts/openrouter-provider-contract.json` |
| **NOT live:** routing rules (`routing_rule_count = 0`), inference traffic (`logs_total_requests = 0`, `inference_traffic_observed = false`), model aliases, `vk-frontier`, semantic-mode cache, any kie/media upstream | Acceptance audit lines 151-156; rendered config (no `cel_expression`); registry (no kie entry) |

**Policy invariant (verified in three places):** `openrouter/auto`, `openrouter/auto-beta`, `openrouter/free` are **forbidden** (`contracts/openrouter-provider-contract.json:13-17,28`; hard-rejected by `workflow_cli.py:597-606`; rejected by `deepagents_worker.py:280-281`). Any use of auto-routing is a **deliberate operator policy reversal**, not a config tweak.

## 1. Model matrix (corrected for admission state)

Champions by category (Sept 2026 leaderboards — BenchLM/LiveBench/Vals, sources in `EVIDENCE_PACK_2026-09-27.md`):

| Category | Champion | Admission state today |
|---|---|---|
| Deep SWE / bug fixing | DeepSeek V4 Pro (96.4% Verified) | ✅ **already approved** |
| Agentic coding lead | Kimi K3 (70.0% agentic, #1 open) | ❌ needs admission |
| Long engineering sessions / security | GLM-5.3 (95.4% Verified, 1M ctx) | ❌ needs admission |
| General reasoning + vision | Qwen3.8 Max (open #1, 71.8) | ❌ needs admission |
| Fast/cheap utility | GLM-5.3 Flash / Qwen3.8-Flash-Next ($0.15/M in) | ❌ needs admission |
| Agentic MoE alternate | MiniMax M3 | ✅ already approved |
| Fast coding | DeepSeek V4 Flash | ✅ already approved |
| Frontier fallback (rare) | Claude Opus 5.5 / GPT-5.6 Sol / Gemini 3.1 Pro | GPT-5.6 Sol ✅ approved; others need admission |

**Admission procedure for any new ID (gate, not step):** (1) verify live catalog existence via `python -m agentcore workflow models --provider openrouter` (checks live index, `workflow_cli.py:1296+`); (2) confirm cost tier; (3) explicit operator approval; (4) update `contracts/openrouter-provider-contract.json` `models` **and** `APPROVED_OPENROUTER_MODELS` together; (5) record the accepted selection through agentcore-memory (contract `memory.record_accepted_provider_model_selection_through_agentcore`). The VK `allowed_models:["*"]` is NOT the lever — the contract and allowlist are.

## 2. Phases (revised)

### Phase 0 — Inference-traffic prerequisite (NEW; nothing else is measurable without it)
The acceptance audit proves no IDE inference currently traverses Bifrost. Before any routing work:
1. Operator picks one pilot client (recommended: Cursor custom OpenAI-compatible base URL → `http://127.0.0.1:8080/v1` with the builder inference VK; Bifrost docs confirm VK-as-API-key for Cursor).
2. Cursor (plane owner) renders/validates the client change through `renderers/gateway-clients/` + `contracts/agentcore-gateway-client.json` — no direct IDE config pasting.
3. Acceptance: `Get-AgentCoreBifrostFeatureAdoption.ps1` shows `inference_traffic_observed = true` and `logs_total_requests > 0`.
**Gate:** no later phase starts until this passes. All §5 metrics depend on it.

### Phase 1 — Model admission (contract + allowlist, operator-approved)
- Frame the admission proposal for: Kimi K3, GLM-5.3, Qwen3.8 Max, GLM-5.3 Flash (minimum set; Qwen3.8-Flash-Next optional).
- Verify each against the live catalog; confirm cost tiers; operator approves; contract + `APPROVED_OPENROUTER_MODELS` updated in one change; validators run.
- Ownership: provider contract + workflow allowlist are non-Bifrost inference policy (Codex framing authority); renderer untouched (VK is already wildcard).

### Phase 2 — Deterministic routing (runtime governance, Cursor-owned apply)
- Create CEL routing rules via the Bifrost governance REST API (they live in `config.db`; the rendered config never contains them): task-class header rules with weighted targets over the **admitted** model set, plus token-count rules for 1M-ctx models.
- Optionally add model aliases (`nf-swe` → deepseek/deepseek-v4-pro, etc.) so header-incapable clients get stable names.
- No `vk-frontier` exists today; if the operator wants the frontier-standby pattern, it is a **new VK** created through the same governance surface (or simply a named alias to an approved frontier model) — decide at this gate, don't assume.
- Acceptance: `routing_rule_count > 0` in the adoption reporter; Prometheus/Langfuse shows `routing_rule_name` on pilot traffic.
- **Operator decision point (explicit, not assumed):** whether to reverse the `openrouter/auto` prohibition. Default recommendation: **do not reverse** — keep explicit-model policy; the CEL rules already provide the per-task selection, and admission of the champion set removes the need for a meta-router. If the operator later wants auto-routing, it requires a coordinated contract + CLI + worker change with its own rollback, and it must never be the *default* while `forbidden_model_ids` stands.

### Phase 3 — Baseline + eval harness (only now honest)
- Build a 20–30 prompt eval set from this repo's real task history (agentcore-memory `retrieve_context`).
- Run pinned-champion routing vs single-model baselines (DeepSeek V4 Pro, MiniMax M3) vs one frontier control, through the pilot client so traffic is observable.
- Wire Bifrost OTel → Langfuse; use Morph Reflex (`reflex_*`, already live) for trace classification.
- Produce the first real A/B table. OpenRouter Ori Eval is optional tooling here, used only with admitted models.

### Phase 4 — Semantic-mode cache (optional, evidence-gated)
- Hash mode is already live. Semantic mode (embedding provider + vector store) is proposed **only if** Phase 3 shows meaningful repeated-prompt volume that hash mode misses. Real plugin config only; no Valkey fiction.

### Deferred appendix (NOT in critical path; separate operator approvals)
- **kie-media / MiniMax H3 / video-image generation**: separate product expansion; existing `openrouter-media-generation` group already defines the `billable_approval` JIT pattern to follow. Not required to prove better non-frontier coding.
- **OpenRouter Fusion**: billable multi-model meta-route; conflicts with explicit-model posture until the operator decides otherwise; only after a measured baseline.
- **`openrouter/auto` reversal**: see Phase 2 decision point.

## 3. Success criteria (all now measurable, all gated on Phase 0)

| Criterion | Measurement |
|---|---|
| Pilot inference traffic observed through Bifrost | adoption reporter `inference_traffic_observed = true`, `logs_total_requests > 0` |
| Routing rules live and matching | `routing_rule_count > 0`; `routing_rule_name` label present on routed requests |
| Champion routing ≥ single-model baselines on eval set; ≥ frontier control on quality at ≤30% cost | Phase 3 eval table (Langfuse-traced) |
| Fast Apply first-pass merge ≥96% | Morph Reflex/Langfuse trace stats |
| Code Mode overhead <1.5k tokens | already proven live; re-verify on pilot traffic |
| Zero policy violations | `validate_contracts.py` + `test_contracts.py` green; no forbidden model IDs anywhere; no direct IDE MCP entries; no second memory store |

## 4. Ownership routing (added; was missing)

- Registry / renderer / `renderers/bifrost/*` / `ops/bifrost` live apply → **Cursor sole primary owner** (AUTH-2026-09-08).
- `contracts/openrouter-provider-contract.json` + `APPROVED_OPENROUTER_MODELS` + eval framing → **Codex framing authority** (non-Bifrost inference policy).
- This plan is produced in Zoo/Plan mode: evidence + proposal only; implementation is delegated per the above.

## 5. Operator decision recommendation

**APPROVE WITH GATES.** The compound-AI direction is sound and partially live; the Gemini plan stays rejected. Approval of this plan means authorizing, in order:

1. **Gate A (Phase 0):** approve one pilot client routing inference through Bifrost (recommend Cursor). Without it, nothing downstream is measurable.
2. **Gate B (Phase 1):** approve admission of Kimi K3, GLM-5.3, Qwen3.8 Max, GLM-5.3 Flash (after live-catalog verification) into the provider contract + workflow allowlist.
3. **Gate C (Phase 2):** approve creation of CEL routing rules + aliases over the admitted set; decide the `vk-frontier` question; decide (recommend: no) the `openrouter/auto` reversal.
4. **Gate D (Phase 3):** approve the eval spend bound for the baseline/A-B harness.
5. Media, Fusion, and semantic-mode cache remain **deferred** behind their own future approvals.

Reject conditions (any one): operator declines the pilot client; operator declines new-model admission (then the plan reduces to already-approved DeepSeek V4 Pro / MiniMax M3 / DeepSeek V4 Flash routing only); or operator insists on `openrouter/auto` as default without a contract-policy change — that would need a different plan.
