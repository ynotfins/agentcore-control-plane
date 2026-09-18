# Bifrost Full Feature Optimization Audit (2026-09-14)

Branch: `setup/zoo-code-qdrant-nfa-20260820`
Authority: Cursor sole Bifrost MCP owner
Evidence commit (Phase A): `b24b34d`

## 1. Inventory matrix

| Feature | Status | Live evidence | Gap | Priority |
|---|---|---|---|---|
| Code Mode (binding=tool) | Configured | Eager tools/list **29** (was 53); VFS includes serena, nia, cursor_agent_mcp, skills_hub, morph, playwright, research; live `--mode check` drift_count=0 | Apply path now PUTs `is_code_mode_client` after render/restart | P0 done |
| Eager hot path | Configured | memory, sequential-thinking, Code Mode meta-tools, capability-catalog, arabold-docs, context7 remain eager | Arabold 10 eager schemas kept (`keep_full_eager`; o200k 1009) | P1#2 done |
| Tool filtering / VK MCP | Configured | `mcp_disable_auto_tool_inject=true`; builder VK profile allowlists | None urgent | - |
| Gateway auth | Configured | headers mode for IDE VKs on `:8080`; Trust Class A `:18082` | Do not flip oauth-only | Rejected change |
| Keys / load balance | Configured | Weighted keys via governance render | Continue model allowlists | P2 |
| Retries / fallbacks | Partial | Provider configs present (openai, openrouter) | Explicit fallback chains not audited this pass | P2 |
| Compat plugin | Unused | Not required for current IDE surface | Admit only for LiteLLM drop-in need | Rejected now |
| Drop-in replacement | Partial | `/v1/chat/completions` works with builder VK | Document inference vs MCP plane separation | P1 |
| Prompt caching (provider) | Configured | openai_direct + openrouter_openai both `pass=true`; second call `cached_tokens`/`cached_read_tokens`=1408, `hash_cache_hit`=false (`audits/bifrost/BIFROST_PROVIDER_PROMPT_CACHE_PROOF_2026-09-14.json`) | None; `agentcore_meta.provider_prompt_cache_policy` recorded, providers stay keys-only | P1 done |
| Semantic / hash cache | Configured | dimension=1 hash mode; Redis `:6381` up; plugin `active`; probe miss then hit (`cache_debug.cache_hit` false then true) | Treat as proven hash cache, not stub | P0 done |
| Content logging | Configured | `disable_content_logging: true` | Keep forever unless operator changes AUTH | Protect |
| OTEL | Unused | Not enabled | Optional GenAI spans later; no content export | P2 |
| Async inference / webhooks | Unused | No AgentCore consumer | Admit only with consumer + ADR | Rejected now |
| Tool hosting (Go SDK) | Rejected | Gateway must not take SDK-only hosting | N/A | Rejected |
| Watchdog self-heal TTLs | Configured | `-StopRequestedMarkerTtlSeconds 120`, `-StartRequestedMarkerTtlSeconds 180`; Test PASSED | None | P0 done |
| Serena Code Mode | Configured | HTTP shim `:18090`; VFS `servers/serena/`; missing `serena-*` is discovery failure | executeToolCode still needs project identity headers for writes | P1 |
| nfa identity | Partial | Enrollment correct; signed GatewayClient works; unsigned MCP fails `device_assertion_required`; **no Stage B hooks in nfa** | Do not weaken assertions; nfa needs its own signed client path | Identity stop |

## 2. Ranked backlog

### P0 (implement now / already landed)
1. **Eager surface shrink** — move `nia`, `cursor-agent-mcp`, `skills-hub` to Code Mode; measure; live admin PUT to sync config.db. **DONE** (53 to 29 eager; ~7910 o200k compact tokens).
2. **Watchdog TTL pin** — elevated install; Test PASS. **DONE**.
3. **Hash-cache proof** — Redis 6381 + dimension 1 + miss/hit. **DONE** (`audits/bifrost/BIFROST_HASH_CACHE_PROOF_2026-09-14.json`).
4. **Vibe-prompt guard** — handoff over huge pastes; keep content logging off. **DONE** (`.cursor/rules/vibe-prompt-protection.mdc`).
5. **Ops gap close** — apply path must PUT `is_code_mode_client` on live clients after render/restart so config.json and config.db cannot diverge. **DONE** (`scripts/bifrost/sync_code_mode_live_clients.py --mode check|apply`; Install if healthy; Start after readiness; Test `--check`; proof `audits/bifrost/BIFROST_CODE_MODE_LIVE_SYNC_PROOF_2026-09-14.json`).

### P1 (next bounded tasks)
1. **Provider prompt-cache enablement** — openai/openrouter stable system/tool prefixes; cache-read tokens proven. **DONE** (commits `b85fa98`, `cbe681e`; `audits/bifrost/BIFROST_PROVIDER_PROMPT_CACHE_PROOF_2026-09-14.json`; 19/19 unit tests).
2. **Arabold eager-token measurement** — docs-first hot path stays eager. **DONE** (`keep_full_eager`; 10 tools; compact o200k 1009; Code Mode save 1008 and bounded-subset save 370 rejected; `audits/bifrost/ARABOLD_EAGER_TOKEN_MEASUREMENT_2026-09-16.md`; unit tests `scripts/bifrost/test_arabold_eager_tokens.py` 3/3).
3. Serena executeToolCode project-identity injection for enrolled roots (without sticky STDIO).
4. Strengthen Test to assert Code Mode clients are absent from tools/list (not only registry flag).

### P2 / later
- OTEL metrics-only profile (no content)
- Explicit retry/fallback matrix for inference
- Compat/drop-in only with a named consumer

## 3. Explicit non-goals
- Swarm MCP paste into IDE baselines
- Shared Bifrost Tentra/Depwire enablement without ADR
- oauth-only `/mcp`
- Weakening nfa/device_assertion / Stage B for convenience
- Treating `dimension: 1` as a stub

## 4. Exit criteria status
| Criterion | Status |
|---|---|
| Measured eager-token reduction | PASS (53 to 29; compact chars 64234 to 34764; o200k 7910) |
| Watchdog self-heal pinned | PASS |
| Cache proofs | PASS (hash miss then hit; content logging off) |
| Live Code Mode apply path | PASS (19 enabled clients matched; drift_count=0; no recycle) |
| No secret leakage | PASS (proof JSON has no tokens/bodies) |

## 5. Recommended next operator action
P0 is accepted. P1#1 provider prompt-cache and P1#2 Arabold (`keep_full_eager`) are done. Next pending P1 is Serena executeToolCode project-identity injection.
