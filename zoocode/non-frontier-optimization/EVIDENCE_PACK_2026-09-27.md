# Research Evidence Pack — Non-Frontier Optimization via Bifrost
**Collected:** 2026-09-27 (live web via Tavily through gateway; Bifrost docs via arabold-docs local store; machine facts via repo contracts). No training-data claims.

## A. Model landscape (September 2026)

### BenchLM Open-Source Leaderboard (verified 2026-09-15, 104 models)
- Qwen3.8 Max — 71.8 (open-weight #1)
- GLM-5.3 — 67.1 · GLM-5.2 — 66.8
- DeepSeek V3.2 — 56.9 · Qwen3.8-Flash-Next — 57
- Top open-weight tier: DeepSeek, Zhipu (GLM), Moonshot (Kimi), Alibaba (Qwen), MiniMax

### BenchLM Agentic Leaderboard (Sept 2026)
1. Claude Opus 5.5 (87.9) … 5. GPT-6 Astra (70.6)
6. **Kimi K3 — 70.0% (#1 open weight)**
9. **GLM-5.3 — 67.2%** · 10. **Qwen3.8 Max — 65.5%**
14. **Qwen3.8-27B — 61.0%** · 23. Qwen3.8-Flash-Next — 57%
- Radar Sep 21–27: MiniMax M3.1 Flash Preview released

### LiveBench Coding (pinggy.io, current rotation)
- Kimi K3 — Coding 81.45, Agentic Coding 57.58 (open #1)
- GLM 5.2 — 79.65 / 51.92 · DeepSeek V4 Pro — 69.99 / 42.63 · MiniMax M3 — 68.20 / 40.66 · Qwen 3.6 27B — 71.78 / 39.29
- Frontier leader Claude Fable 5 = 60 on AA index; best open weights within ~3 points

### Vals AI SWE-bench Verified (archived board, via morphllm.com checked 2026-09-22)
- DeepSeek V4 Pro 0813 — 96.4% · GLM-5.3 — 95.4% · Kimi K3 — 93.4%
- (Frontier: Claude Opus 5 archived top 97.0%)

### Other key specs (yottalabs.ai, thundercompute, baseten 2026-09-04)
- Kimi K3: 2.8T (~50B active), 1M ctx, AIME 96.1, GPQA 93.5, HLE 43.5; "Fable-tier, 100 tok/s, #1 Design Arena"
- GLM-5.3: 744B MoE, 1M ctx, "Opus-tier", built for multi-hour agent sessions; GLM-5.3 Flash $0.15 in / $0.50 out
- Qwen3.8 Max: 2.4T, native vision, 1M ctx; Qwen3.8-27B runs on 24GB card @4-bit
- DeepSeek V4.1 Flash: $0.15/$0.60 off-peak; V4-Flash weights MIT on HF (166.9GB, 2×H200)
- Baseten: "Kimi K3 most well-rounded; Qwen 3.6 and GLM-5.3 lead agentic coding; DeepSeek and Nemotron dominate long-context"
- GLM-5.2: AIME 99.2, GPQA 91.2, no image understanding

## B. Routing technology (current)

### Bifrost (docs.getbifrost.ai — local arabold-docs store)
- Routing rules API: `cel_expression`, `priority`, `targets[{provider, model, weight (must sum to 1), key_id}]`, `scope: global|team|customer|virtual_key`; Prometheus labels `routing_rule_id/name`, `routing_engine_used` (governance, routing-rule, loadbalancing, model-catalog, core)
- Request flow: VK validation/budget → CEL routing rules → adaptive health scoring → semantic cache → provider; fallback chains + key rotation on 429/401/402; 11µs p99 overhead
- Semantic cache plugin (real config): `dimension` (1 = hash mode, no embedding provider), `provider`, `embedding_model`, `threshold` (default 0.8), `ttl`, `cache_by_model/provider`, `conversation_history_threshold`; semantic mode requires separate `vector_store`
- v1.5.0 breaking changes: empty array = deny-all; `allowed_keys`→`key_ids`; VK `provider_configs: []` deny-by-default; multi-`budgets`; Direct Key Bypass removed
- Code Mode: 58.2% input-token cut @96 tools, 84.5% @251, 92.8% @508 (cost −92.2%, ~40% faster, 100% pass); Starlark sandbox; 4 meta-tools (listToolFiles/readToolFile/getToolDocs/executeToolCode)
- Cursor integration: VK as OpenAI API key; per-feature model assignment (Chat/Agent/Inline/Tab)

### OpenRouter (openrouter.ai, aireiter.com, releasebot.io)
- `openrouter/auto` — Aug 10, 2026 "wisdom of the market" engine: classifies ~30 task types, ranks by trailing 7-day community spend (55T+ weekly tokens), 5 cost tiers (low/medium/high/xhigh/max), sticky multi-turn, respects guardrails/ZDR; replaced NotDiamond engine; response `model` field is auditable
- **Ori Eval** (Aug 4, 2026): agentic eval tool — real prompts, writes eval files, compares cost/speed/tool-calls/quality, CI support
- **Model Fusion** (OpenRouter Labs): runs prompt through multiple models + judge model fuses best aspects — for hardest tasks
- Free tier includes: nemotron-3-ultra-550b (1M ctx), thinkingmachines/inkling (1M, text+image+audio), z-ai/glm-5.2:free

### Morph (morphllm.com — current)
- Fast Apply: v3-fast 10,500 tok/s @96%; v3-large 4,500 tok/s @98%; vs Claude 3.7 (94%), GPT-5.4 (92%), Claude 3.5 Sonnet (91%); 100% merge success paired with frontier planners vs 84–96% for search-replace; $0.80/1M input; MCP integration available
- WarpGrep: sub-6s searches; SWE-bench A/B on Claude 4.5 Opus — 15% cheaper, 10% more accurate, 26% fewer turns, 16% fewer prompt tokens
- **Reflex**: classify agent traces for any behavior <90ms
- **Model Router**: auto-route each prompt to best model
- Morph's own current model page lists: Kimi K3, GLM-5.3, Qwen (27B), MiniMax (230B MoE agentic), DeepSeek

## C. Media (September 2026)

### Video models (overchat.ai comparison + ngram + invideo + HF blog)
| Model | Max res | Length | Native audio | $/s |
|---|---|---|---|---|
| MiniMax H3 (Hailuo 3.0) | 2K (1440px short edge) | 4–15s @24fps | ✅ stereo, same pass | ~$0.30 tier (2K) |
| Kling 3.0 | 4K | 3–15s | ✅ | 0.11 |
| Gemini Omni Flash | 720p | 10s | ✅ | 0.10 |
| Veo 3.1 | 4K | 8s | ✅ | 0.40 |
| Seedance 2.0 / 2.5 | 1080p | 4–12s | ✅ | 0.30 |
| Wan 2.7 | 1080p | 2–15s | ✅ | 0.10 |
| LTX 2.3 | 4K | 20s | ✅ | 0.05 |
| Hailuo 2.3 | 1080p | 6–10s | ❌ | 0.05 |
- MiniMax H3: launched 2026-07-31; AA Elo 1238 (#2 T2V, #1 Video Editing, #3 I2V behind Gemini Omni Flash 1245); 9 image + 3 video + 3 audio refs; cuts + localized editing in one generation; open weights announced (MiniMax Community License, <$20M rev) but NOT released as of Aug 2026; "33B" parameter claim unverified
- Images: Nano Banana 2, Seedream 5.0 Pro, Flux 2, Qwen Image 3, GPT Image 2.5
- Aggregators: fal.ai — 985 endpoints (406 image / 450 video / 59 audio / 35 3D), 50% image & 44% video API market share; Magnific (ex-Freepik) bundles Kling 3.0/Veo 3.1/Gen-4.5/Seedance/Wan 3.0/MiniMax; Runway Gen-4.5 + Aleph 2.0

## D. Machine facts (repo contracts, verified this session)
- Gateway: single `agentcore-gateway` @ `http://127.0.0.1:8080/mcp`, bearer `env:BIFROST_MCP_VIRTUAL_KEY` (`contracts/agentcore-gateway-client.json`)
- Registry: `contracts/bifrost-upstream-mcp-registry.json` — capability profiles (builder/reviewer/operator/…), named permitted_tools, no wildcards; morph_mcp enrolled (codebase_search, edit_file, github_codebase_search, reflex_*)
- Code Mode globally enabled since 2026-09-08 (`audits/bifrost/CODE_MODE_GLOBAL_ENABLE_2026-09-08.md`); live tools confirmed this session: listToolFiles → readToolFile → executeToolCode (Starlark)
- Production PG18 @ 127.0.0.1:55433 (`agent_core`); memory only via agentcore-memory through gateway; no second store permitted
- OpenRouter MCP behind Bifrost, dormant by default, M6 lease + JIT VK bridge for exact `openrouter-*` tool groups (`docs/operations/OPENROUTER_MCP.md`)
- Langfuse installed (`docs/operations/LANGFUSE_TRACING_AND_PROMPTS.md`, langfuse skill); A/B judge rule `.cursor/rules/self-verification-ab-judge.mdc`
- Hardware: 128GB RAM, RTX 4070 12GB VRAM, NVMe; F: = AgentCore hot runtime

## E. Gemini plan claims vs. reality (summary table)
| Gemini claim | Reality |
|---|---|
| "Valkey 8.0 SIMD HNSW semantic cache, 2M pairs, <5ms" | Not a Bifrost feature. Real semantic cache: plugin + vector_store; hash mode `dimension:1` |
| `virtual_keys` inline config with `allowed_models`/`fallbacks`/`cache` | Fabricated schema; real VKs are governance objects (key_ids, provider_configs, budgets) |
| DeepSeek-V4.1-Flash "90.6 Terminal-Bench 2.1, 74.2% DeepSWE" | Unverifiable/fabricated; V4.1 Flash mid-pack on independent boards |
| GLM-5.3 "CyberGym 84.5%, ExploitBench 54.4%" | Unverifiable; GLM-5.3 is real and strong, numbers invented |
| MiniMax-H3 "33B omni-modal" | Size unverified anywhere; weights not released |
| Qwen2.5-VL-72B, DeepSeek-R1, QwQ-32B, Claude 3.5 Sonnet, o3-mini, Kling 1.5, Runway Aleph, Flux Kontext | All stale generations (2025-era) |
| Docker pgvector:pg18 second Postgres + postgres_rag MCP :5433 | Conflicts with production PG18 @55433 and repo policy (no second memory store, no direct MCP entries) |
| Local Qwen2.5-Coder-7B Q8 as auxiliary engine | 12GB VRAM can host it, but hosted Flash tier ($0.15/M) is better quality — negative ROI |
| A/B table numbers (94% retrieval, <5ms, "Exceeds Frontier") | Invented; no harness specified. Real harness: Ori Eval + Langfuse + Reflex |
| Kie MCP via SSE TypeScript server | SSE transport deprecated; must go through registry/render pipeline as governed upstream |
