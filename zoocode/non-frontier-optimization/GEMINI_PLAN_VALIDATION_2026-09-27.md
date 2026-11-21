# Gemini Plan Validation — Non-Frontier Model Optimization via Bifrost

**Date:** 2026-09-27
**Mode:** Plan (evidence-only; no files outside `zoocode/` were modified)
**Verdict:** **INVALID as written.** The compound-AI *direction* is sound and partially already live on this machine, but the plan contains stale model names, fabricated benchmarks, wrong Bifrost config syntax, hardware allocations that conflict with the actual machine, and — most critically — it never implements the per-task model selection it promises.

---

## 1. What the plan gets right (keep)

| Claim | Status | Evidence |
|---|---|---|
| Compound AI beats monolithic frontier on cost/latency | ✅ Confirmed | Multiple Sept 2026 sources: open-weight gap to frontier now ~3 points (Artificial Analysis); Morph: "for most teams the best answer is a router that sends easy work to a cheap model" |
| Bifrost Code Mode cuts tool-context tokens 58–93% | ✅ Confirmed | Bifrost benchmark: 58.2% @96 tools, 84.5% @251, 92.8% @508 tools; ~40% faster. **Already globally enabled on this machine** (`audits/bifrost/CODE_MODE_GLOBAL_ENABLE_2026-09-08.md`) |
| Morph Fast Apply ~10,500 tok/s, 96–98% merge accuracy | ✅ Confirmed | morphllm.com benchmarks: v3-fast 10,500 tok/s @96%, v3-large 4,500 tok/s @98%; beats Claude 3.7 (94%) and GPT-5.4 (92%) at merging. **Already enrolled here via `morph_mcp` (edit_file) through the gateway** |
| Morph WarpGrep improves agent search | ✅ Confirmed | Morph SWE-bench A/B (Claude 4.5 Opus): 15% cheaper, 10% more accurate, 26% fewer turns. **Already enrolled (`morph_mcp.codebase_search`)** |
| MiniMax H3 (Hailuo 3.0): 2K/24fps, 4–15s, native stereo audio | ✅ Mostly confirmed | Launched 2026-07-31; #1 AA Video Editing, #2 Text-to-Video (Elo 1238, behind Gemini Omni Flash 1245); accepts 9 images + 3 clips + 3 audio refs. ⚠️ "33B omni-modal" parameter count is **unverified** in any source; open weights announced but **not yet released** as of Aug 2026 |
| Two VK config (frontier standby + non-frontier primary) | ✅ Sound pattern | Matches existing AgentCore capability-profile architecture (`contracts/bifrost-upstream-mcp-registry.json`) |

## 2. Fatal flaws (reject / replace)

### 2.1 The plan never actually routes by task
The core requirement is "Bifrost picks the best non-frontier model per part of the job." The Gemini config only lists `allowed_models` + a single GLM-5.3 fallback. Every request still names one explicit model; nothing classifies tasks or selects per-category. **Bifrost OSS has no built-in quality-aware prompt classifier.** Real mechanisms available today:
- **CEL routing rules** with weighted targets (headers, token counts, model strings, scopes) — microsecond decisions
- **Model aliases** for stable client-side names
- **`openrouter/auto`** (Aug 2026 "wisdom of the market" engine): classifies ~30 task types, ranks by trailing 7-day community spend, 5 cost tiers, sticky multi-turn; usable as a provider *behind* Bifrost
- **Morph Model Router** (auto-route each prompt)
- **OpenRouter Fusion** (multi-model + judge fusion) for hardest tasks

### 2.2 Stale / wrong model matrix
| Gemini pick | Problem | Current best (Sept 2026, sourced) |
|---|---|---|
| "DeepSeek-V4.1-Flash 90.6 Terminal-Bench 2.1, 74.2% DeepSWE" | Benchmark numbers unverifiable/fabricated; V4.1 Flash is real but mid-pack on independent boards | **Kimi K3** — #1 open-weight agentic (BenchLM agentic 70.0%, LiveBench Coding 81.45, Agentic Coding 57.58); **GLM-5.3** (BenchLM agentic 67.2%, Vals SWE-bench Verified 95.4%) |
| GLM-5.3 for security/architecture | Right model, fabricated CyberGym/ExploitBench numbers | Keep GLM-5.3 (it is literally the model running this session); Kimi K3 leads independent security results |
| DeepSeek-R1 / QwQ-32B for math | A year stale | **Kimi K3** (AIME 96.1), **Qwen3.8 Max** (open-weight leaderboard #1 at 71.8), GLM-5.2 (AIME 99.2) |
| Qwen2.5-VL-72B for vision | Stale generation | **Qwen3.8** (native vision), GLM-4.5V, InternVL3-78B; free option: `thinkingmachines/inkling:free` (text+image+audio, 1M ctx) |
| Frontier fallback: Claude 3.5 Sonnet / o3-mini | ~14 months stale | Claude Opus 5.5 / Fable 5.1, GPT-6 Astra, Gemini 3.1 Pro |
| Missing entirely | — | **Qwen3.8 Max**, **Qwen3.8-27B** (61.0% agentic, runs on one GPU), **MiniMax M3**, **GLM-5.3 Flash / Qwen3.8-Flash-Next** ($0.15/M input utility tier), **Nemotron 3 Ultra** (long context) |
| Media: "Runway Aleph, Kling 1.5, Flux Kontext" | Stale | Kling **3.0** (4K), Veo **3.1**, Seedance 2.0/2.5, LTX 2.3 (4K, 20s, $0.05/s), Wan 2.7; images: Nano Banana 2, Seedream 5.0 Pro, Flux 2 |

### 2.3 Bifrost config syntax is invented — would not load
- `virtual_keys` as an inline config object with `allowed_models`/`fallbacks`/`cache` is not real Bifrost config. Real: governance virtual keys (`x-bf-vk`), provider configs per VK, `key_ids` (renamed from `allowed_keys` in v1.5.0), multi-`budgets`.
- `plugins.semantic_cache` with `store: valkey` / `connection_url` is fabricated. Real: `semantic_cache` plugin with `dimension` (1 = hash mode), `provider`, `embedding_model`, `threshold`, `ttl`, `cache_by_model`; requires separate `vector_store` config for semantic mode.
- v1.5.0 breaking changes ignored (empty array = deny-all; VK `provider_configs: []` deny-by-default).
- No "Valkey 8.0 SIMD HNSW semantic cache storing 2M pairs at <5ms" exists in Bifrost. Fabricated.

### 2.4 Conflicts with the actual machine and governance
- Plan deploys a **second Postgres** in Docker (`pgvector/pgvector:pg18`, 32GB shared_buffers) — this machine already runs production **PG18 at 127.0.0.1:55433** (`agent_core`, LangGraph checkpoints, agentcore-memory). Repo policy: *no second canonical memory store*; memory only through `agentcore-gateway → agentcore-memory`.
- Plan's `postgres_rag` MCP at :5433 and hand-rolled `kie-mcp-server.ts` (SSE transport — deprecated; MCP is streamable-HTTP now) bypass the Bifrost upstream registry + capability profiles + render pipeline. Policy requires all upstreams through `contracts/bifrost-upstream-mcp-registry.json` → `render_bifrost_config.py`.
- Hardware fiction: 12GB VRAM RTX 4070 cannot run anything that beats hosted Flash-tier models. Qwen3.8-27B needs 24GB even at 4-bit. Local Qwen2.5-Coder-7B Q8 (~8GB) is possible but delivers worse quality than GLM-5.3 Flash at $0.15/M input — negative ROI for the "local auxiliary engine" role.
- Docker/WSL2 + `/nvme` mounts: this is Windows; `F:` is the AgentCore hot runtime. Plan ignores the entire existing runtime.

### 2.5 A/B testing claims are asserted, not testable
The A/B table's numbers (94% retrieval accuracy, <5ms cache hits, "Exceeds Frontier") are invented. No measurement harness is specified. Real, currently available evaluation tooling: **OpenRouter Ori Eval** (launched Aug 2026; tests real prompts, compares cost/speed/tool-calls/quality, CI support), **Morph Reflex** (<90ms trace classification), **Langfuse** (already installed here, per skill + `docs/operations/LANGFUSE_TRACING_AND_PROMPTS.md`).

---

## 3. Sources (pulled live 2026-09-27, not from training data)

- benchlm.ai/best/open-source — Open-Source LLM Leaderboard (104 models, verified 2026-09-15): Qwen3.8 Max 71.8, GLM-5.3 67.1
- benchlm.ai/agentic — Agentic leaderboard Sept 2026: Kimi K3 70.0% (#6 overall, #1 open), GLM-5.3 67.2%, Qwen3.8 Max 65.5%, Qwen3.8-27B 61.0%
- pinggy.io LiveBench Coding: Kimi K3 81.45 / GLM 5.2 79.65 / DeepSeek V4 Pro 69.99 / MiniMax M3 68.20
- baseten.co (updated 2026-09-04): "Kimi K3 most well-rounded; Qwen 3.6 and GLM-5.3 lead agentic coding"
- morphllm.com/best-ai-model-for-coding (checked 2026-09-22): Vals AI SWE-bench Verified — DeepSeek V4 Pro 96.4%, GLM-5.3 95.4%, Kimi K3 93.4%
- yottalabs.ai: GLM-5.3 Flash $0.15/$0.50, Qwen3.8-Flash-Next $0.15/$0.47, DeepSeek V4.1 Flash $0.15/$0.60 off-peak
- aireiter.com + openrouter.ai: Auto Router "wisdom of the market" (Aug 10, 2026), 30 task types, 5 cost tiers, `openrouter/auto`
- releasebot.io: OpenRouter Ori Eval (Aug 4, 2026); Model Fusion (judge-blended multi-model)
- morphllm.com/fast-apply-model + /benchmarks: Fast Apply 10,500 tok/s; WarpGrep A/B results
- getmaxim.ai: Bifrost Code Mode benchmarks (58.2%/84.5%/92.8% token reduction); 11µs p99 gateway overhead
- docs.getbifrost.ai (arabold-docs local store): routing rules (CEL, weighted targets, scopes), semantic_cache plugin spec, v1.4.0/v1.5.0 migration breaking changes
- huggingface.co/blog/ResterChed + ngram.com + invideo.io: MiniMax H3 specs (2026-07-31 launch, 2K/24fps, native stereo audio, weights not yet released)
- overchat.ai + teamday.ai: current video model price/spec table (Kling 3.0 4K $0.11/s, Veo 3.1 $0.40/s, LTX 2.3 $0.05/s, Hailuo 2.3 $0.05/s); fal.ai 985 endpoints, 50% image / 44% video API market share
- Machine facts: `contracts/bifrost-upstream-mcp-registry.json`, `contracts/agentcore-gateway-client.json`, `audits/bifrost/CODE_MODE_GLOBAL_ENABLE_2026-09-08.md`, AGENTS.md (PG18 @ 55433, gateway @ 127.0.0.1:8080/mcp, morph_mcp enrolled)
