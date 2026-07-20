# Gated AgentCore Rollout — Cross-Client Closeout

**Date:** 2026-07-19  
**Repo:** `D:\github\agentcore-control-plane`

## Status strings (claimed)

| String | Claimed? |
| -- | -- |
| `OPENROUTER MCP REGISTERED DORMANT — OAUTH NOT VALIDATED` | **YES** |
| `CHERRY STUDIO ENROLLED IN AGENTCORE — OPENROUTER PROVIDER LIVE` | **YES** (Gate C) |
| `DORMANT MCP CAPABILITY CATALOG READY` | **YES** (catalog doc + zero default exposure policy) |
| `OPENROUTER MCP AVAILABLE THROUGH AGENTCORE-GATEWAY` | **NO** |
| `OPENROUTER MODELS AVAILABLE AS IDE MODELS` | **NO** |

## Cross-client proofs

| Client | Gateway | Direct OpenRouter MCP | Notes |
| -- | -- | -- | -- |
| Cursor live `~\.cursor\mcp.json` | single `agentcore-gateway` → `http://127.0.0.1:8080/mcp` | absent | timeout 300 |
| Codex `~\.codex\config.toml` | `[mcp_servers.agentcore-gateway]` | absent (OpenRouter is **model_providers** only) | inherits gateway |
| Renderer `renderers/gateway-clients/minimax.json` | single gateway | absent | enrolled JSON client |
| Operator VK `tools/list` | 47 tools; **10** `agentcore_memory-*`; **0** openrouter tools | n/a | ten-tool invariant held |
| Memory `memory_status` | healthy 0.6.0; PG18 `:55433`; migrations through `m8.001` | n/a | |
| Project router | `agentcore-control-plane` active | n/a | |

## Validators run

- `python scripts/bifrost/validate_contracts.py` — OK
- `python scripts/engineering/admission_gate.py --validate-catalog` — re-run after provenance fix
- Extension security monitor — report-only; critical=0

## Gates A–E

| Gate | Result |
| -- | -- |
| A Power-loss | PASS (evidence under `artifacts/gated-agentcore-rollout-2026-07-19/`) |
| B Governance / dormant catalog | PASS |
| C Cherry Studio | PASS |
| D AO isolated | PASS (claude-code spawn; cursor binary missing non-blocking) |
| E Swarm / extensions / skills | PASS (no uninstalls; no Swarm mutation) |

## Residual risks (operator)

1. `BIFROST_ENCRYPTION_KEY` absent — OpenRouter OAuth blocked by design
2. Bifrost `config.db` broad ACL — durability check expected FAIL until hardened
3. Prior Cherry enrollment may have echoed keys to terminal — rotate recommended
4. AO not on PATH; Cursor harness binary not found for AO spawn
5. `find-skills` present on Cherry disk but not catalog-admitted (license unverified)

## MASTER_CONFIG_AND_PROMPT.md SHA-256

`1D330D17E1DC998386656C23AAAD690532A865CD74E8F148407F78BB818ECD0F`
