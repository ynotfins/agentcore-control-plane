# LangGraph Topology Canary — 2026-08-09 19:51 EDT

## Scope

This is the M5 runtime canary required before final restore-point evidence. It verifies the AgentCore LangGraph production runtime/topology without starting a real production project.

Real production project execution requires an operator-supplied goal and acceptance criteria via:

```powershell
.\.venv\Scripts\python.exe -m agentcore workflow start --goal '<goal>' --acceptance-file '<file>' --autonomous
```

## Command

Run from:

`@D:\github\agentcore-control-plane\scripts`

```powershell
.\.venv\Scripts\python.exe -m agentcore workflow topology --json
```

## Result

```json
{
  "timestamp": "2026-08-09T23:51:01.965751+00:00",
  "topology_fingerprint_sha256": "a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32",
  "node_count": 15,
  "interrupt_before": [
    "human_pause"
  ],
  "checkpointer_production": "agentcore_workflow.workflow.build_graph -> PostgresSaver",
  "checkpointer_studio": "agentcore_workflow.workflow.build_studio_graph -> Agent Server dev checkpointer",
  "note": "Production and Studio share the same topology. Topology fingerprint is stable for the current graph; do NOT edit without explicit operator approval."
}
```

## Acceptance

PASS.

Evidence:

- Expected topology fingerprint is present.
- Expected node count is 15.
- Production checkpointer is PostgresSaver.
- Studio remains dev checkpointer only.
- No workflow was started and no project artifacts were mutated.
