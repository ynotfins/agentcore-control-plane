# Distill Pre-M3 Identification Record

**Status:** Identified, not integrated.  
**Milestone relevance:** M3 entry evidence; does not block M2.  
**Blueprint reference:** BLUEPRINT.md §3 (Distill reference patterns) and M3 exit criterion requiring an ADR if Distill behavior is native vs hidden sidecar.

## Candidate identified

- Repository URL: https://github.com/Siddhant-K-code/distill
- Site: https://distill.siddhantkhare.com/
- License: MIT (per repository/search metadata)
- Language/runtime: Go
- Current version/commit evidence: main branch; session-management commit referenced in search result: `a4b0724036e04c5e34af6400545c1404e090ce1b` ("feat: add session-based context window management")
- Windows compatibility: likely compatible because it is Go and provides CLI/MCP modes; must be verified on CHAOSCENTRAL during M3 entry before using code or sidecar behavior.

## API / MCP behavior (from public docs/search evidence)

- MCP command: `distill mcp --memory --session`
- Memory tools: `store_memory`, `recall_memory`, `forget_memory`, `memory_stats`
- Session tools: `create_session`, `push_session`, `session_context`, `delete_session`
- Behaviors matching BLUEPRINT.md requirements:
  - write-time deduplication
  - token-budgeted session windows
  - hierarchical decay/compression
  - importance-aware retention
  - recent preservation window
  - deterministic/no-LLM core path
  - advertised ~12 ms processing overhead

## M3 decision guidance

Do **not** adopt Distill as a second canonical memory store. PostgreSQL remains canonical. Distill is a reference implementation and benchmark source for M3 rolling-context behavior.

M3 must decide with an ADR:

1. Native AgentCore implementation of Distill-style behaviors, or
2. Hidden sidecar behind `agentcore-memory`.

Default recommendation until benchmarked: implement natively first because M2 now provides PostgreSQL identity/evidence/queue primitives and the core M3 requirements are tightly coupled to immutable source edges and generated STATE projections.
