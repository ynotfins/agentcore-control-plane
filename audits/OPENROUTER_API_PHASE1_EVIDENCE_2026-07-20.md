# OpenRouter API Phase 1 Evidence (2026-07-20)

**Starting commit (task baseline):** `f347015`  
**Repo HEAD at evidence write:** see git after push  
**Prior overstated commit (not accepted as completion):** `69f9ac6`

## Live verified OpenRouter model IDs

Queried `GET https://openrouter.ai/api/v1/models` with User-scope `OPENROUTER_API_KEY` (value not logged).

| Model ID | Live |
| -- | -- |
| `minimax/minimax-m3` | yes |
| `deepseek/deepseek-v4-pro` | yes |
| `openai/gpt-5.6-sol` | yes |
| `minimax/minimax-m2.7` | yes |
| `deepseek/deepseek-v4-flash` | yes |
| `tencent/hy3:free` | yes (free smoke `OI-OR-OK`) |
| `openrouter/auto` | listed but **forbidden by policy** |
| `google/gemma-4-31b-it:free` | listed but **404** under account privacy/guardrails |

Forbidden routers for AgentCore selection: `openrouter/auto`, `openrouter/auto-beta`, `openrouter/free`.

## Open Interpreter

| Check | Result |
| -- | -- |
| Config path | `%APPDATA%\interpreter\codex-home\config.toml` |
| Default provider/model | `openrouter` / `minimax/minimax-m3` |
| `default_profile_id` | `autonomous-os` |
| Profiles | `autonomous-os`, `autonomous-gpt-sol`, `autonomous-deepseek-pro`, `autonomous-minimax-m27`, `autonomous-free` (`tencent/hy3:free`), … |
| Env-backed key | yes (`OPENROUTER_API_KEY`) |
| `fallbacks: []` on default/approved profiles | yes |
| `openrouter/auto` | absent |
| MCP | only `agentcore-gateway` in OI codex-home |
| Free smoke | `tencent/hy3:free` → `OI-OR-OK` |
| Memory lifecycle | session_open + startup_context OK; append/retrieve flaked (gateway timeouts) — **incomplete** |
| `~/.codex/config.toml` | Codex Desktop default remains `gpt-5.5`; **12 literal `sk-or-v1-*` scrubbed to `${env:OPENROUTER_API_KEY}`** (rotation still required) |

## LangGraph production

| Check | Result |
| -- | -- |
| Command | `python -m agentcore workflow start --project <path> --goal-file <goal> --provider openrouter --model <id>` |
| Models list | `python -m agentcore workflow models --provider openrouter` (live catalog) |
| Default unchanged | proven empty provider/model on fixture stream |
| Checkpoint + metadata | `PROOF_OK True` — provider/model survived new graph load; `wf_runs.metadata.model_selection` persisted |
| Full fixture completion | **not** claimed — long `workflow start` hung on LLM nodes; persistence proven separately |

Fixture repo: `D:\github\openrouter-wf-fixture-20260720` (disposable).

## LangGraph Studio

| Check | Result |
| -- | -- |
| Topology parity | fingerprint `a86e40e8…ae32` matches production |
| `langgraph validate` | valid |
| Dev server | `http://127.0.0.1:2025` returned 200; `langsmith:false` |
| Selection method | thread input `{"provider":"openrouter","model":"<explicit-id>"}` (documented in studio README) |
| Full Studio interrupt/judge OR path | **not** fully exercised in UI this run |

## Cherry Studio

| Check | Result |
| -- | -- |
| Gateway | exactly one `agentcore-gateway` |
| Direct OpenRouter MCP | false |
| Global Memory | false |
| OpenRouter provider | one; host `https://openrouter.ai/api/v1` |
| Models | includes sol, deepseek-v4-pro, m3, m2.7; **no** `openrouter/auto` |
| App default preserved | `cherryai` / `qwen` (not OpenRouter) |

## Agent Orchestrator

| Check | Result |
| -- | -- |
| CLI | `C:\Program Files\agent-orchestrator\resources\daemon\ao.exe` |
| Version | app `0.10.3`; `ao version` → `dev` |
| PATH | **PASS** (`ao doctor`: ao-binary in PATH) |
| Provider mechanism | child harness `codex` → Open Interpreter OpenRouter profiles (AO has no DB / no native OR provider) |
| Fixture spawn | `openrouter-wf-fixture-20260720-1` worktree created; killed; cleaned |
| Cursor harness | **needs install** — `agent "cursor" needs install` |

## Bifrost / OpenRouter MCP (Phase 2 gate)

| Check | Result |
| -- | -- |
| `BIFROST_ENCRYPTION_KEY` | present, User scope only |
| `config.db` ACL | PASS — only `ynotf`, Administrators, SYSTEM |
| Backup | `E:\AgentCore-Backups\bifrost-pre-oauth-20260720-000116` (+ SHA256 manifest) |
| OAuth | **blocked** — logs: `oauth2 config not found`; `BIFROST_ADMIN_KEY` absent so authorize_url cannot be re-issued from here |
| Claim `OPENROUTER MCP AVAILABLE THROUGH AGENTCORE-GATEWAY` | **NO** |

## Paid call / cost

| Call | Cost |
| -- | -- |
| Free chat smokes (`tencent/hy3:free`, earlier `openrouter/free` probe) | $0 |
| Paid MCP calls | 0 |
| Full paid M3/Sol workflow runs | not authorized / not completed |

## Invariants

- No `.env` files created
- Other IDE defaults unchanged (Cursor/Codex Desktop model unchanged; Codex Desktop remains `gpt-5.5`)
- No direct OpenRouter MCP IDE entries added
- Ten-tool memory surface unchanged (operator VK tools/list earlier sessions)
- Swarm / `D:\github\agent-swarm` untouched
