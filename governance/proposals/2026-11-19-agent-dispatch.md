# Proposal: agent-dispatch — local autonomous agents as gateway sub-agents

**Date:** 2026-11-19
**Status:** Proposed. Code and live loopback smoke tests are on branch `feat/agent-dispatch`. Not yet registered in Bifrost.
**Owner for apply:** Cursor (sole primary owner of the Bifrost MCP contract plane, per `AGENTS.md`). Codex reviews.
**Rollback:** set the registry entry `enabled=false`, re-render, run `ops/bifrost/Start-AgentCoreAgentDispatch.ps1 -Stop`. Nothing else on the PC changes.

## Why

Every gateway client (Grok Bot, Cursor, Codex, ZCode, VSCodium/Cline/Continue, OpenCode, Cherry Studio, LobeHub, ...) should be able to hand work to the local autonomous agents and run several in parallel, for very little context. The gateway's existing `pi-agents` upstream covers Pi only, and its shim on `:18091` is not running today.

## What was built (branch `feat/agent-dispatch`)

- `scripts/agent_dispatch/`: a loopback HTTP MCP server on `127.0.0.1:18092`, standard library only. It reuses `bifrost.session_identity` for default-deny project enrollment, the same way the Pi shim does.
- Six tools, with descriptions of 120 characters or fewer: `agents_list`, `agent_run`, `agents_parallel`, `job_status`, `job_result`, `job_cancel`.
- Backends:

  | Agent | How it runs | Model route |
  | --- | --- | --- |
  | `pi` | `pi -p --no-session` with a dispatch-owned agent dir (`I:\LocalApps\AgentDispatch\pi-agent`) | OmniRoute `deepseek-v4-pro` |
  | `openhands` | `openhands --headless --json --override-with-envs` | OmniRoute `deepseek-v4-pro` (set per run through env vars) |
  | `opencode` | `opencode run -m omniroute/deepseek-v4-pro --format json` | OmniRoute |
  | `codex` | `codex exec --sandbox workspace-write -m gpt-5.6-terra` (prompt passed on stdin) | Codex subscription |
  | `langgraph` | `python -m agentcore workflow start` (M6, PostgresSaver on PG18) | **Off by default**: M6 calls OpenRouter directly |
  | `paperclip/<agent>` | Creates and assigns a Paperclip issue over its REST API on `:3100`. Status, result and cancel read or patch that issue. | Only agents with no model, OmniRoute models, or `codex_local` can run |

- Per-job record in `I:\LocalApps\AgentDispatch\jobs\<id>\job.json`: agent, model, tokens and cost where the CLI reports them, workdir, files changed (git diff of dirty files, or an mtime scan in scratch dirs), exit status and duration. Full stdout and stderr logs sit next to it.
- Limits: at most 4 jobs run at once (`AGENTCORE_DISPATCH_MAX_PARALLEL`), at most 8 tasks per fan-out, and a per-agent wall-clock budget (Pi 10/30 min, OpenCode 20/60, OpenHands and Codex 30/90, M6 60/180). Workers run at below-normal priority with no window. When the budget runs out the whole process tree is killed.
- Workdir allowlist: enrolled project paths, `D:\agentcore-worktrees\<enrolled-key>\...`, or a per-job scratch dir under `I:\LocalApps\AgentDispatch\scratch` when no workdir is given. Refused: all of `C:`, `F:\AgentCore`, `F:\PostgreSQL18`, `H:`, `E:\Swarm`, `R:`, Swarm markers and roots, and any path containing "nfa" unless the task text names nfa. If the gateway's `x-agentcore-project` header names a different project than the workdir, the job is refused (`project_identity_mismatch`).
- Idle cost (measured): about 29 MB working set for the Python process, plus about 4 MB for the venv launcher stub and 10 MB for its console host. 0 ms CPU over 30 s and 3 threads. Nothing polls. Paperclip status is fetched only when a client asks.

## Design changes from the original brief, and why

1. **No new LangGraph graph for fan-out.** Fanning out subprocesses and collecting their summaries needs no graph. A bounded pool is simpler and costs no tokens. The existing, verified M6 LangGraph workflow (PostgresSaver on PG18, gates, critics, judge) is exposed as the `langgraph` backend for long governed runs instead of being duplicated.
2. **Built on the `pi-agents` pattern, intended to replace it.** One upstream covers Pi plus every other agent, so `pi-agents` can be retired. Both use the same enrollment and identity code.
3. **Through Bifrost Code Mode the six tools cost close to nothing up front.** Clients find them with `listToolFiles` / `readToolFile` instead of loading every schema.
4. **Summaries come from each agent's own final message, cut to 300 words.** No extra model call is spent on summarising.

## Requested changes (locked; need Cursor apply + Codex review)

### P1. Register the upstream in `contracts/bifrost-upstream-mcp-registry.json`

```json
"agent-dispatch": {
  "canonical_id": "agent-dispatch",
  "display_name": "AgentCore Agent Dispatch",
  "purpose": "Async sub-agent jobs (Pi, OpenHands, OpenCode, Codex, M6 LangGraph, Paperclip) behind six tools.",
  "owner": "agentcore",
  "pinned_version": "0.1.0",
  "connection_type": "http",
  "executable_or_url": "http://127.0.0.1:18092/mcp",
  "arguments": [],
  "env_var_names": [],
  "timeout_seconds": 60,
  "health_check_type": "mcp_ping",
  "project_scope": "project",
  "write_classification": "write_capable",
  "permitted_tools": ["agents_list", "agent_run", "agents_parallel", "job_status", "job_result", "job_cancel"],
  "denied_tools": [],
  "capability_profiles": ["builder", "ide", "grokbot"],
  "logging_policy": {"log_invocations": true, "log_content": false, "redact_secrets": true},
  "retry_policy": {"max_attempts": 1, "backoff_seconds": 2, "retry_on": ["spawn_failure"]},
  "rollback_route": "Set enabled=false; re-render; Start-AgentCoreAgentDispatch.ps1 -Stop.",
  "enabled": true,
  "bifrost_client_name": "agent_dispatch",
  "status": "active",
  "is_code_mode_client": true,
  "allowed_extra_headers": ["x-agentcore-project", "x-bf-session-id", "x-session-id"]
}
```

Also add `agent-dispatch` to `allowed_server_ids` for `builder`, `ide` and `grokbot`. Then re-render with `scripts/bifrost/render_bifrost_config.py`, run `scripts/bifrost/validate_contracts.py`, and restart and accept Bifrost.

### P2. Retire `pi-agents`

After P1 has been accepted live: set `pi-agents` to `enabled=false`, remove it from `builder` and `grokbot`, and stop launching `:18091` from `Start-AgentCoreBifrostGateway.ps1`. Pi stays reachable as `agent_run(agent="pi")`.

Docs to update in the same P1/P2 apply commit (all locked; docs-guardian 2026-11-19, verdict CLEAR for this PR): `CONTEXT_BLOCK.md` (the Pi parallel subagents row, `pi-agents` on `:18091`), `contracts/global-agent-policy.yaml`, `docs/operations/WORKSTATION_PARALLEL_SUBAGENT_INFRASTRUCTURE.md`, `docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md`, `docs/operations/BIFROST_CONTEXT_AND_OMNIROUTE_DEFAULT.md`.

### P3. Start with the gateway

In `ops/bifrost/Start-AgentCoreBifrostGateway.ps1`, call `Start-AgentCoreAgentDispatch.ps1` the same way it calls the Pi shim today. This adds no scheduled task and no service.

### P4. PC Performance Bot watchdog

Please add to the watchdog list:

| Field | Value |
| --- | --- |
| Name | `AgentCore-AgentDispatch` |
| Process | `D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe -u ...\scripts\agent_dispatch\server.py --port 18092` (pid in `I:\LocalApps\AgentDispatch\agent-dispatch.pid`) |
| Port | `127.0.0.1:18092` (loopback only) |
| Health | `GET http://127.0.0.1:18092/health` returns `{"status":"healthy"}` |
| Restart | `powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\bifrost\Start-AgentCoreAgentDispatch.ps1` |
| Expected idle | about 45 MB total, 0% CPU |
| Logs | `I:\LocalApps\AgentDispatch\logs\` |
| Never disturb | NFA `:3000` / `NFA-Platform-API-LAN`, `:8080`, `:18082`, `:20128`, `:3100`, `:55433` |

### P5. Model-routing fixes found during inventory (not changed here)

- **OmniRoute `default` combo resolves to `deepseek/deepseek-v4.1-flash-1017`, not v4-pro.** OpenHands (`~/.openhands/config.toml`) and OpenCode (`omniroute/default`) defaults therefore are not deepseek-v4-pro. agent-dispatch pins `deepseek-v4-pro` explicitly. Decide whether the combo should change.
- **Paperclip agents bypass OmniRoute.** CEO, Code Reviewer, Drift Review QA, Release Engineer, Lead Engineer and Builder use `openrouter/deepseek/deepseek-v4-pro`. Docs uses `openrouter/deepseek/deepseek-chat`, and Grok Builder uses the Grok CLI subscription. Switching their adapter model to `omniroute/deepseek-v4-pro` would make them dispatchable. agent-dispatch refuses them until then (`routing_not_omniroute`).
- **The M6 LangGraph workflow calls OpenRouter directly** (`agentcore_workflow/deepagents_worker.py`, `nodes.py`). It needs an OmniRoute provider path before `langgraph` is enabled by default. The interim opt-in is the User env var `AGENTCORE_DISPATCH_ALLOW_DIRECT_OPENROUTER=1`, which also unlocks the Paperclip agents above.
- **The Codex default model `gpt-6.1-terra` is rejected on the ChatGPT subscription** (`model_not_found`), as are `gpt-6.2-sol` and `gpt-6-sol`. `gpt-5.6-terra` works and is what agent-dispatch uses. Codex `exec` also loads all user MCPs, hooks and skills (about 30k tokens for a one-word reply), and its `:18810` MCP and `UserPromptSubmit` hook fail. Trimming that would make Codex jobs cheaper.
- **Pi's global config talks to OpenRouter directly.** agent-dispatch avoids this with its own `PI_CODING_AGENT_DIR`, leaving the operator's `~/.pi/agent` untouched.

### P6. Paperclip items (no changes made)

- Paused agents, listed only and left alone: **AI CEO** (cursor), **Fixer** (cursor), **Hermes Utility** (hermes_local).
- `Scratch Writer` (`process` adapter) runs, but it cannot close its issue. Paperclip moves the issue to `blocked` ("no live execution path"). A fully completed Paperclip issue through `agent_run` therefore needs at least one OmniRoute-routed, model-backed agent (see P5).

## Evidence (2026-11-19, live on loopback, branch build)

- Unit tests: `scripts/agent_dispatch/test_agent_dispatch.py`, 18 passed.
- `agent_run` single jobs: pi succeeded in 7.3 s, openhands in 36.3 s, opencode in 28.1 s (92,479 tokens), codex in 49.8 s. Each wrote `hello.txt` in its scratch dir.
- `agents_parallel` 3-way run (pi + opencode + openhands): succeeded in about 28 s of wall time, with all three files written.
- `job_cancel` on a running Pi job: cancelled, and no orphaned worker processes remained.
- Paperclip: `agent_run(paperclip/scratch-writer)` created **VAL-12**, assigned to Scratch Writer. Status moved to `blocked` (see P6). `job_cancel` set it to `cancelled`, confirmed through the Paperclip API.
- Not tested: access through agentcore-gateway from Grok Bot, Codex or an IDE. That is blocked on P1.

## Dropped candidates (with reason)

- Hermes: works, but it is hard-wired to OpenRouter in `~/.hermes/config.yaml`, it overlaps the gateway research tools and Pi, and it is paused in Paperclip.
- Open Interpreter 0.0.40: a fork of the Codex CLI, so it duplicates `codex`.
- Claude Code: Anthropic subscription and was not requested. It could be added later the same way Codex was.
- OpenClaw 2026.9.5: a messaging-assistant gateway, and its gateway is not running. Could be added later via `openclaw agent --local`.
- ClawTeam: its own autonomous runtime with a Board, overlapping Paperclip. No CLI on PATH.
- DeepAgents: approved only inside M6 LangGraph nodes (`AGENTS.md`), so it is covered by `langgraph`.
- Stale or not runtimes, with no changes in 60+ days or just docs and backups: `D:\github\swarms`, `D:\github\agent-swarm`, `D:\AgentSwarm`, `D:\MAF`, `D:\Auto-AI-Router`, `D:\AgentOps`, `D:\github\autonomous-agent-team`, `D:\github\advanced-agent-team`, `D:\github\minimax-agent-team`, `D:\Codex-Parallel-Agents`, `D:\NFA-OpenHands-Control`, `D:\hermes_agent`. `D:\Autonomy` holds research and backups only. `D:\github\agentcore-context-engine` is a library, not an agent.
