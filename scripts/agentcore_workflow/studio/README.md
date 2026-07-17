# LangGraph Studio — AgentCore Workflow (Dev / Debug Surface)

> **Studio is a development / debugging surface only.** It does NOT
> replace the production PostgresSaver. Production persistence is
> untouched by Studio.

| Aspect | Production | Studio |
| --- | --- | --- |
| Graph topology | `agentcore_workflow.workflow.build_graph` | `agentcore_workflow.workflow.build_studio_graph` (same topology) |
| Checkpointer | `PostgresSaver` → `public.checkpoints` at `127.0.0.1:55433` | Agent Server dev checkpointer (sqlite/in-memory) |
| Persistence | Canonical, durable, restart-safe | Ephemeral; for visualization only |
| LangSmith tracing | Disabled by policy | `LANGSMITH_TRACING=false` forced |
| Analytics | n/a | `LANGGRAPH_ANALYTICS=false` forced |
| Bind | 127.0.0.1 only | 127.0.0.1 only |
| Windows service | No | No — Studio is a foreground process |
| Operator use | `python -m agentcore workflow start` | `python -m agentcore workflow studio` |

## Topology fingerprint

The same topology fingerprint is computed by both runtimes and validated at
Studio launch:

```text
a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32
```

The fingerprint is a stable sha256 over (nodes, edges, conditional-edge
options). A topology change invalidates the fingerprint by design.

## Launch Studio

From the repository root (run from `scripts/`):

```powershell
cd D:\github\agentcore-control-plane\scripts
python -m agentcore workflow studio
```

Or specify port:

```powershell
python -m agentcore workflow studio --port 2024 --no-browser
```

The launcher:

1. Verifies Studio app directory + `langgraph.json` + `graph.py` exist.
2. Loads the topology fingerprint from the canonical workflow module and
   from `studio/graph.py`. Aborts if they differ.
3. Locates the LangGraph CLI (`python -m langgraph_cli`).
4. Sets `LANGSMITH_TRACING=false`, `LANGGRAPH_ANALYTICS=false`,
   `LANGGRAPH_HOST=127.0.0.1`.
5. Runs `langgraph dev --port <port> --no-browser` from the Studio app dir.
6. Reports the local API URL (e.g. `http://127.0.0.1:2024`) and a Studio
   connection hint.
7. Streams output to the operator terminal; Ctrl+C stops the server.

## Connect LangGraph Studio

Open LangGraph Studio and point it at:

```text
http://127.0.0.1:2024
```

(or whichever port the launcher reports).

You should see the complete graph topology with all expected nodes and
conditional edges. Select the **`agentcore_workflow`** graph.

## What to verify in Studio

- All expected nodes visible: `start`, `gate_check`, `deterministic_checks`,
  `risk_assess`, `critics_and_score`, `judge_node`, `micro_execute`,
  `da_builder`, `da_critic`, `ab_alternate`, `post_exec_judge`,
  `evidence_record`, `next_step`, `human_pause`, `workflow_fail`.
- Conditional edges from `start`, `gate_check`, `deterministic_checks`,
  `judge_node`, `human_pause`, `micro_execute`, `da_builder`,
  `da_critic`, `post_exec_judge`, `next_step` show the correct option sets.
- Create a thread, run the fixture, inspect node input/output state.
- Deterministic gate results visible per node.
- A human interrupt is visible on `human_pause`.
- After approving/resuming, the interrupted thread advances.
- Builder (DA) results and critic findings visible per run.
- `post_exec_judge` sees both candidate evidence sets (A vs B for high-risk).
- `block` route → `workflow_fail`; `proceed` → `evidence_record`.
- Checkpoint / time-travel inspection works (Studio dev checkpointer).

## What Studio is NOT

- NOT a second production Agent Server database.
- NOT a replacement for `python -m agentcore workflow start`.
- NOT a persistent Windows service.
- NOT a route to LangSmith Cloud — `LANGSMITH_TRACING=false` prevents
  AgentCore application data from being sent.

## Stopping Studio

Press Ctrl+C in the terminal running `langgraph dev`. The dev checkpointer
is ephemeral; nothing persists.

## Operational runbook

- **Start:** `python -m agentcore workflow studio` (from `scripts/`).
- **Status:** Studio prints the API URL on startup.
- **Stop:** Ctrl+C in the dev-server terminal.
- **Restart:** Re-run the start command.
- **Validation:** `python -m langgraph_cli validate -c scripts/agentcore_workflow/studio/langgraph.json`.
- **Topology parity:** automatic in the workflow CLI launcher; manual
  check via `python -m agentcore workflow topology --json`.

## Files

| File | Purpose |
| --- | --- |
| `scripts/agentcore_workflow/studio/langgraph.json` | LangGraph CLI config |
| `scripts/agentcore_workflow/studio/graph.py` | Graph factory (reuses canonical topology) |
| `scripts/agentcore/studio.py` | Studio launcher shim invoked by the workflow CLI |
| `scripts/agentcore_workflow/studio/README.md` | This document |
| `scripts/agentcore_workflow/requirements-studio.txt` | Pinned `langgraph-cli` dev dependency |
