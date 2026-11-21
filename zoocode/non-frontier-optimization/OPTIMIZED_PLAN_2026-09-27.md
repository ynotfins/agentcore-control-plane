# Optimized Plan — Better-Than-Frontier Performance with Non-Frontier Models via Bifrost

**Date:** 2026-09-27 · **Status:** PLAN ONLY (awaiting operator approval; no live config changes)
**Supersedes:** Gemini plan (see [GEMINI_PLAN_VALIDATION_2026-09-27.md](GEMINI_PLAN_VALIDATION_2026-09-27.md))
**Scope guard:** All changes flow through the existing governance chain: `contracts/bifrost-upstream-mcp-registry.json` → `scripts/bifrost/render_bifrost_config.py` → live apply via `ops/bifrost`. No direct IDE MCP entries. No second memory store. No Docker Postgres.

---

## 0. Core insight from current research

The open-weight gap to frontier is now ~3 points (Artificial Analysis, Sept 2026). No single non-frontier model beats Claude Opus 5.5 everywhere — but a **routing compound system** does, because:

1. **Per-task champions exist.** Kimi K3 (70.0% agentic), GLM-5.3 (95.4% SWE-bench Verified), DeepSeek V4 Pro (96.4% Verified), Qwen3.8 Max (71.8 open-weight #1) each beat frontier on their home category.
2. **The frontier's real advantage is long-horizon consistency, not any single step.** That is neutralized by Code Mode (92.8% token cut), Fast Apply (98% merges at 10,500 tok/s — frontier models get 82–94% at 80–90 tok/s), and WarpGrep (15% cheaper, 10% more accurate, 26% fewer turns — measured on Claude 4.5 Opus).
3. **Routing intelligence is now a commodity.** `openrouter/auto` classifies ~30 task types against trailing-7-day community spend; Bifrost CEL rules + weighted targets give deterministic per-scope control at µs cost; Morph Model Router and OpenRouter Fusion cover the remaining gaps.

## 1. Non-Frontier Model Matrix (current, sourced — replace Gemini's stale matrix)

| Category | Primary | Alternate / cheap tier | Why (Sept 2026 evidence) |
|---|---|---|---|
| Agentic coding lead | **Kimi K3** (Moonshot) | GLM-5.3 | #1 open-weight agentic (BenchLM 70.0%); LiveBench Coding 81.45; Fable-tier at ~100 tok/s |
| Deep SWE / bug fixing | **DeepSeek V4 Pro 0813** | DeepSeek V4.1 Flash | Vals AI SWE-bench Verified 96.4% — above every frontier except Opus 5 |
| Long engineering sessions | **GLM-5.3** | GLM-5.2 | 744B MoE, 1M ctx; 95.4% Verified; built for multi-hour agent sessions; security-strong |
| Math / proofs / algorithms | **Kimi K3** (AIME 96.1) | GLM-5.2 (AIME 99.2), Qwen3.8 Max | Competition-math parity with closed frontier |
| General reasoning / generalist | **Qwen3.8 Max** | Qwen3.8-27B | Open-weight leaderboard #1 (71.8); native vision; 1M ctx |
| Fast/cheap utility (classification, summaries, tool parsing, commit msgs) | **GLM-5.3 Flash** ($0.15/$0.50) | Qwen3.8-Flash-Next ($0.15/$0.47), DeepSeek V4.1 Flash ($0.15/$0.60 off-peak) | Flash tier now handles what mid models did a year ago |
| Vision / document & UI grounding | **Qwen3.8** (native vision) | GLM-4.5V, InternVL3-78B; free: `thinkingmachines/inkling:free` (1M ctx, text+image+audio) | Qwen2.5-VL-72B (Gemini's pick) is a stale generation |
| Long-context / enterprise corpus | **DeepSeek V4 Pro** / Nemotron 3 Ultra | GLM-5.3 (1M ctx) | DeepSeek + Nemotron dominate long-context per Baseten |
| Code merge (apply) | **Morph v3-large** (98%) / v3-fast (10,500 tok/s) | — | Beats Claude 3.7 (94%) and GPT-5.4 (92%) at merging |
| Codebase search | **Morph WarpGrep** | — | Sub-6s searches; 15% cheaper / 10% more accurate on SWE-bench |
| Trace classification / agent QA | **Morph Reflex** (<90ms) | Langfuse judge | New Sept 2026 tool; classifies agent traces for any behavior |
| Video (omni + native audio) | **MiniMax H3** (2K/24fps, stereo) | Kling 3.0 (4K, $0.11/s), Gemini Omni Flash (AA Elo 1245, #1 T2V), Veo 3.1 ($0.40/s) | H3 #1 AA Video Editing, #2 T2V; Hailuo 2.3 cheapest at $0.05/s |
| Video (long/budget) | **LTX 2.3** (4K, 20s, $0.05/s) | Wan 2.7, Seedance 2.0/2.5 | 20s clips at lowest price with native audio |
| Image | **Nano Banana 2 / Seedream 5.0 Pro / Flux 2** | GLM Image | Via kie.ai or fal.ai (985 endpoints, 50% image-API market share) |
| Frontier fallback (rare) | Claude Opus 5.5 / GPT-6 Astra / Gemini 3.1 Pro | — | vk-frontier standby only, per existing pattern |

**Local 4070 (12GB VRAM):** do NOT chase local LLM inference for quality — hosted Flash-tier beats any 7B local model at negligible cost. Use the GPU only for embeddings/rerankers if a semantic cache is enabled later. This reverses Gemini's "local Qwen2.5-Coder-7B auxiliary engine" — negative ROI.

## 2. Routing architecture (the part Gemini's plan never implemented)

Three complementary layers, all real and current:

### Layer A — Bifrost CEL routing rules + weighted targets (deterministic, µs)
Define scoped routing rules in Bifrost governance (real API: `cel_expression`, `priority`, `targets[{provider, model, weight}]`, `scope: global|team|virtual_key`):

- `x-task-class: swe-fix` → DeepSeek V4 Pro (0.7) / Kimi K3 (0.3)
- `x-task-class: agentic-loop` → Kimi K3 (0.6) / GLM-5.3 (0.4)
- `x-task-class: math-proof` → Kimi K3 (0.5) / Qwen3.8 Max (0.5)
- `x-task-class: utility` → GLM-5.3 Flash (0.6) / Qwen3.8-Flash-Next (0.4)
- token-count > 200k → GLM-5.3 / DeepSeek V4 Pro (1M ctx)
- default → `openrouter/auto` with `cost_tier: medium` (never `low` for quality-critical paths)

Clients that can't set headers (Cursor features) get **model aliases** instead: `nf-agentic` → Kimi K3, `nf-swe` → DeepSeek V4 Pro, `nf-cheap` → GLM-5.3 Flash, `nf-auto` → openrouter/auto.

### Layer B — `openrouter/auto` (learned router, always fresh)
The Aug 2026 "wisdom of the market" engine classifies ~30 task types and follows 7-day community spend — it auto-discovers new models within days of release. Use it as the *default* route behind Bifrost with `cost_tier: medium`/`high`; pin specific models (Layer A) only where measured quality demands it. This directly answers "Bifrost picks the best model for the job" with zero maintenance.

### Layer C — Fusion for the hardest 5%
For architecture-critical or high-risk decisions, route to **OpenRouter Fusion** (multi-model deliberation + judge fusion) or run the existing `.cursor/rules/self-verification-ab-judge.mdc` A/B judge flow (best-of-n-runner + code-reviewer in fresh context). This is where "better than frontier" is actually earned.

### What NOT to build
- No custom prompt-classifier microservice — `openrouter/auto` + CEL already cover it.
- No Valkey "SIMD semantic cache" — fabricated. Real Bifrost semantic cache (`semantic_cache` plugin, `dimension`, `threshold`, `vector_store`) is a valid later optimization; start with **hash mode (`dimension: 1`)** which needs no embedding provider, then A/B semantic mode.
- No second Postgres/RAG stack. Memory = existing `agentcore-gateway → agentcore-memory` (PG18 @ 55433) only.

## 3. Delivery pipeline (per coding job)

```
Client (Cursor/Zoo/Codex/…) → Bifrost :8080
  ├─ Code Mode (LIVE since 2026-09-08): 4 meta-tools, 58–93% token cut
  ├─ CEL rule / alias / openrouter:auto → per-task champion model
  ├─ WarpGrep (morph_mcp.codebase_search) for context discovery
  ├─ Champion model plans the edit
  ├─ Morph Fast Apply (morph_mcp.edit_file) merges at 10,500 tok/s / 98%
  ├─ Reflex (<90ms) or Langfuse judge classifies the trace → escalate to Fusion if flagged
  └─ Fallback chain: Kimi K3 → GLM-5.3 → DeepSeek V4 Pro → (rare) vk-frontier
```

## 4. Media pipeline (kie.ai — already-paid key)

Do **not** build the Gemini hand-rolled SSE TypeScript server. Instead:
1. Enroll one upstream `kie-media` in `contracts/bifrost-upstream-mcp-registry.json` (stdio or streamable-HTTP adapter wrapping kie.ai REST), with a named `permitted_tools` inventory — same pattern as existing entries.
2. Route by category: MiniMax H3 for omni/native-audio and editing; Kling 3.0 for 4K cinematic; Gemini Omni Flash for top T2V quality; LTX 2.3 for long/budget; Veo 3.1 only when 4K Google look is required. Images: Nano Banana 2 / Seedream 5.0 Pro / Flux 2.
3. Keep MiniMax direct API for H3 (kie.ai catalog coverage to be verified at implementation time; fal.ai is the fallback aggregator with 985 endpoints).

## 5. Phased implementation (each phase independently rollback-able)

**Phase 1 — Model matrix refresh (config-only, hours)**
- Add current OpenRouter model IDs to the gateway provider config / VK allowlists: Kimi K3, GLM-5.3, GLM-5.3 Flash, DeepSeek V4 Pro, DeepSeek V4.1 Flash, Qwen3.8 Max, Qwen3.8-Flash-Next, Qwen3.8-27B, MiniMax M3, `openrouter/auto`.
- Define model aliases (`nf-agentic`, `nf-swe`, `nf-cheap`, `nf-auto`).
- Validate with `scripts/bifrost/validate_contracts.py`; render; restart; smoke-test each alias.
- Rollback: restore previous rendered config (timestamped copy per policy).

**Phase 2 — Routing rules (governance API, hours)**
- Create the Layer A CEL rules with weighted targets; verify via Prometheus labels (`routing_rule_name`, `routing_engine_used`) that decisions land as intended.
- Set default route to `openrouter/auto` cost_tier medium for non-pinned traffic.

**Phase 3 — Baseline + eval harness (1 day)**
- Use **OpenRouter Ori Eval** against 20–30 real prompts from this repo's task history (memory `retrieve_context` can supply them) to measure per-model cost/speed/tool-calls/quality.
- Wire Bifrost OTel → existing Langfuse for traces; use Morph Reflex for fast trace classification.
- Produce the first real A/B table (replacing Gemini's invented numbers): pinned-champion routing vs `openrouter/auto` vs single-model baselines vs frontier control.

**Phase 4 — Media enrollment (half day)**
- Enroll `kie-media` upstream per §4; A/B H3 vs Kling 3.0 vs Omni Flash on 5 canonical prompts each.

**Phase 5 — Fusion escalation + cache (optional, after evidence)**
- Enable Fusion escalation for Reflex/Langfuse-flagged hard tasks.
- Enable Bifrost semantic cache in hash mode first; A/B semantic mode (real plugin config) only if hit-rate justifies an embedding provider.

**Phase 6 — Continuous freshness (zero maintenance)**
- `openrouter/auto` absorbs new releases via 7-day spend signal; re-run Ori Eval monthly; update pinned champions only when a new model beats the incumbent on the eval set.

## 6. Success criteria

- Per-task routing verified in Prometheus/Langfuse (routing_rule_name present on ≥95% requests).
- Ori Eval: compound system ≥ frontier control on quality, at ≤30% of frontier cost, ≤50% latency on agentic tasks.
- Code Mode token overhead stays <1.5k tokens (already proven live).
- Fast Apply merge success ≥96% first-pass.
- No new canonical stores, no direct IDE MCP entries, all changes through render pipeline + validators.

## 7. Risk register

| Risk | Mitigation |
|---|---|
| `openrouter/auto` picks a weak model for a niche task | Layer A pins override; Ori Eval monthly; Fusion for critical |
| Kimi K3 rate limits (new hot model) | Bifrost fallback chain + key pools already handle 429 rotation |
| MiniMax H3 weights/license shift | API access unaffected; kie.ai/fal.ai aggregation as alternate |
| Benchmark inflation (vendor-reported) | Only BenchLM "Supported" / Vals / LiveBench independent numbers used for pinning decisions |
| Policy violation (second memory store, direct MCP) | Plan explicitly routes through registry/render/validators; Phase gates include `validate_contracts.py` |
