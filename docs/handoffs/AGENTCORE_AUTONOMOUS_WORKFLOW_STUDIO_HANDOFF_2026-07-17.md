# Autonomous Workflow & LangGraph Studio Productization — Handoff 2026-07-17

**Status:** READY — production launcher + LangGraph Studio adapter + E2E recovery suite + canonical runbook.

## Scope
Productize the existing M6/M8 AgentCore autonomous LangGraph workflow so a new operator can launch, observe, pause, approve, resume, cancel, recover, and complete a workflow against any registered project without writing custom Python, and visualize the same graph in LangGraph Studio.

## What changed
- `python -m agentcore workflow {init,start,status,pause,approve,reject,resume,cancel,logs,evidence,topology,studio}` — 12 subcommands (`scripts/agentcore/workflow_cli.py`).
- Workflow topology refactor: shared `build_topology()` + `topology_fingerprint()` + `build_graph()` + `build_studio_graph()` (`scripts/agentcore_workflow/workflow.py`).
- LangGraph Studio adapter: `langgraph.json` + `graph.py` + `requirements-studio.txt` + `pyproject.toml` + `README.md` (`scripts/agentcore_workflow/studio/`).
- Studio runner: `scripts/agentcore/studio.py`.
- Studio acceptance: `scripts/agentcore/studio_accept.py` → `audits/M6/studio-acceptance.json`.
- Fixture project: `D:\agentcore-fixture\fixture-project` + `D:\agentcore-fixture\fixture-remote.git`.
- E2E recovery suite: `scripts/agentcore_workflow/tests/fixture_e2e.py` → 17/17 PASS → `audits/M6/fixture-e2e-summary.json`.
- Canonical runbook: `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`.
- CLI help updated in `scripts/agentcore/__main__.py` and `scripts/agentcore/workflow_cli.py`.

## Verification
- Production launch: 17/17 E2E PASS (`fixture-e2e-summary.json`)
- Studio acceptance: graph loaded, thread created, state/history inspected, topology parity proven (`studio-acceptance.json`)
- Bifrost gateway unchanged (E2E scenario 19)
- 10-tool `agentcore-memory` surface unchanged (E2E scenario 19)
- Swarm ecosystem untouched

## Untouched
- `agentcore-memory` (10-tool surface)
- Bifrost gateway contracts and renderers
- Memory database / schema
- Swarm ecosystem (SwarmRecall, SwarmVault, SwarmClaw)
- Open Interpreter
- Workflow definition (nodes, edges, route functions, critic/scorer/judge, A/B, capability leases, Deep Agents)

## Authority
- `BLUEPRINT.md` M6 (locked architecture)
- `MEMORY_PLATFORM_EXECUTION_PLAN.md` M6
- `PROJECT_ANCHOR.md` §0, §3, §10
- `AGENTS.md` (Git policy, no .env, no printed secrets)
- `CLAUDE.md` (gateway baseline)

## Operator next steps
- Read `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`.
- Use `python -m agentcore workflow init --project-key <key> --target <path>` to register a real project (do not run destructive tests against real projects).
- Use the disposable fixture at `D:\agentcore-fixture\fixture-project` for any destructive acceptance.
- Studio: `python -m agentcore workflow studio --port 8124 --no-browser`.

## Evidence locations
- `audits/M6/fixture-e2e-summary.json` — 17/17 PASS
- `audits/M6/studio-acceptance.json` — Studio acceptance
- `audits/M6/M6-EXIT-EVIDENCE.md` — M6 acceptance
- `audits/M6/m6-acceptance-summary.json` — M6 summary

## Git policy compliance
- All changes committed via narrow staged commits.
- Push after each completed task per `docs/GIT_PUSH_ONLY_POLICY.md`.
- No pull / fetch / merge / rebase.
