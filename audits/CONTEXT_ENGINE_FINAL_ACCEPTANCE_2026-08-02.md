# Context Engine Final Acceptance — 2026-08-02

**Authority:** AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE  
**Status:** ACCEPTED with documented residuals (not an optimistic provisional claim)

## Repositories

| Repo | Branch | HEAD at certification | Remote |
|---|---|---|---|
| `D:\github\agentcore-control-plane` | `main` | pre-commit baseline `4698116` + this acceptance commit | origin present; push after commit |
| `D:\github\agentcore-context-engine` | `main` | pre-commit baseline `e123819` + this acceptance commit | no GitHub remote (operator-gated) |
| `D:\github\swarm-ecosystem-control` | `master` | `98576b9` (neutral Recall reclassification; **not** `e6f0c2c`) | origin present |
| `D:\github\vendor\swarm\swarmclaw` | (vendor) | base `f909a037` + wiring/tests commit | vendor remote |

Inherited Langfuse/M6 acceptance-summary WIP in control-plane was **not** staged.

## Gap reconciliation

| # | Conflict | Resolution evidence |
|---|---|---|
| 1 | Hosts not installed / CLI missing | Editable install of `agentcore-context-host-adapters` on Python 3.13; `agentcore-context` CLI available via Scripts; 105/105 pytest on system Python |
| 2 | Capability matrix overstated | Cursor → `live_validated_native_hooks_signed_gateway`; Claude/Codex/generic remain honest non-automatic |
| 3 | legacy_compat vs “every call signed” | Signed path proven under temporary `required` (unsigned + replay rejected). Kept `legacy_compat` because ordinary Bifrost MCP chat tools are still unsigned and would strand Cursor |
| 4 | 15 memory test failures | Fixed `db_available` signature preservation → **40 passed** |
| 5 | Stale LangGraph cert | Fresh RUN9: `run_db_id=368634f7-…`, `thread=f5a8f47b-…`, status=`completed`, judge=`proceed`, score=`1.0`, **13 PostgresSaver checkpoints**, `AGENTCORE_WORKER_MODE=deterministic` (live OpenRouter builders timed out in RUN5–RUN7) |
| 6 | Studio/CLI instructions wrong | Docs corrected: `cd …\scripts` then `python -m agentcore …`; Studio ≠ production checkpoints |
| 7 | M1 still CURRENT | MILESTONES.md updated to COMPLETE with residuals |
| 8 | SwarmClaw adapter unproven | Wired into `memory.ts` store/update + search supplement; **11/11** plugin+wiring tests pass |
| 9 | Swarm HEAD / storage matrix wrong | Control-plane HEAD `98576b9`; Recall is **neutral shared** physically on `H:\SwarmData` / `:3300`, not Swarm-exclusive F: |

## Live proofs (commands)

```powershell
# Memory tests
cd D:\github\agentcore-control-plane\scripts\agentcore_memory
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m pytest tests test_recovery.py -q

# Context Engine system install proof
agentcore-context capabilities

# Cursor hook smoke
# (sessionStart returned AGENTCORE_BOOTSTRAP_OK=1 for agentcore-context-engine)

# Device required-mode drill (restored legacy_compat afterward)
# signed_open ok; unsigned → device_assertion_required; replay → device_assertion_replay

# LangGraph production cert
cd D:\github\agentcore-control-plane\scripts
$env:AGENTCORE_WORKER_MODE = "deterministic"
python -m agentcore workflow start --project-key agentcore-context-engine --milestone M1 --risk-profile medium --provider gemini --model gemini-3.6-flash --json
# → audits/CONTEXT_ENGINE_LANGGRAPH_RUN9_DET_2026-08-02.json

# Production evidence inspection (NOT Studio)
python -m agentcore workflow status --run 368634f7-5e5b-4fb3-a830-d5a478629d5b --json
python -m agentcore workflow topology

# Studio (separate; dev checkpointer only)
python -m agentcore workflow studio --port 2024 --no-browser
```

## Drive / ownership matrix (logical vs physical)

| Plane | Logical ownership | Physical placement (this PC) |
|---|---|---|
| AgentCore PG18 evidence/checkpoints/leases | AgentCore | `F:\PostgreSQL18` / `127.0.0.1:55433` |
| AgentCore Bifrost runtime | AgentCore | `F:\AgentCore\runtime\bifrost` + `H:\AgentRuntime` launchers |
| Neutral SwarmRecall semantic plane | **Machine-level neutral** (not Swarm-exclusive, not AgentCore-exclusive) | Live API `127.0.0.1:3300`; hot data under `H:\SwarmData\recall` |
| SwarmClaw SQLite/tasks/transcripts | Swarm runtime | `H:\SwarmData\claw` |
| Source repos | Git | `D:\github\…` |

## Residuals / operator actions

1. Install Claude Code hooks when ready; then re-certify.
2. Do **not** set device enforcement to `required` until ordinary Bifrost MCP memory calls sign or are fail-closed by policy.
3. Live OpenRouter builder timeouts (`gemini:gemini-3.6-flash` / `deepseek/deepseek-v4-flash`) need operational follow-up; defaults already point at Gemini 3.6 Flash.
4. Create GitHub remote for `agentcore-context-engine` only when Tony approves.
5. Cursor IDE MCP gateway tool discovery was in error during this session even though Bifrost health returned auth-required 401 — investigate IDE MCP reconnect separately.

## Independent review

- Security review: no medium/high/critical findings in changed focus areas.
- Code review CRITICAL (`_compile_fallback` double-brace) fixed in `langfuse_integration.py`.
- SwarmClaw search array-shape + fire-and-forget projection warnings addressed; tests 11/11.
