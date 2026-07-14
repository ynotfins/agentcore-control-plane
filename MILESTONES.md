Rock-solid milestones

These Milestones should be locked. Cursor may freely optimize, add, remove, reorder, or split the Macro and Micro steps inside them based on repository and machine evidence.

Cursor may not change:

Milestone purpose
Milestone exit criteria
Milestone ordering
Core architecture
Storage authority
Cognee decision
Bifrost identity
Lossless guarantees

without explicit operator approval.

M0 — Authority and Execution Foundation

Outcome: Every agent sees one accurate architecture and execution policy.

Exit criteria:

One authoritative read order.
Stale Swarm-first and old database instructions neutralized.
Current machine authority referenced.
Per-IDE global-rule profiles created.
New Project, Milestone, Macro/Micro, checklist, Context Fabric, Arabold, and tool-audit policies established.
This exact memory-platform Milestone plan is the execution authority.
No live memory/database implementation begins in M0.
M1 — PostgreSQL 18 Safety Foundation

Outcome: A recoverable PostgreSQL 18 + pgvector platform exists beside the preserved old cluster.

Exit criteria:

Existing cluster inventory completed.
Logical and physical backups created.
At least one restore test passes.
PostgreSQL 18 and compatible pgvector run on F:.
Required databases and least-privilege service roles exist.
Old PostgreSQL installation remains recoverable.
Rollback is proven.
M2 — Canonical Identity and Immutable Evidence

Outcome: Every durable operation has an identity and every accepted event is preserved.

Exit criteria:

Machine, user, project, repo, worktree, IDE/client, agent, session, run, and LangGraph thread identities are separate.
Append-only evidence ledger works.
Idempotent event writes work.
Large payloads are externalized by content hash.
Project A cannot write Project B.
Normal IDE agents have no database credentials.
Raw evidence cannot be updated or deleted by normal service roles.
M3 — Lossless Context and STATE Projections

Outcome: Long sessions compact without losing recoverability.

Exit criteria:

L0 recent raw context.
L1 event-span summaries.
L2 session summaries.
L3 project chronology.
Exact source links from all summaries.
Original long prompts preserved verbatim.
Exact expansion works after compaction.
Exact expansion works after archival to E:.
GLOBAL_STATE.md and project STATE.md regenerate deterministically.
Process interruption during compaction causes no loss or corruption.
M4 — AgentCore Memory Gateway

Outcome: All non-Swarm IDEs use the completed memory system through the existing Bifrost connection.

Required compact tool surface:

memory_status
startup_context
retrieve_context
append_event
propose_fact
expand_source
session_open
session_close
build_handoff
docs_search

Exit criteria:

Existing agentcore-memory Bifrost identity is preserved.
No IDE configuration change is required.
Multiple IDEs can use separate sessions safely.
Append → retrieve → compact → expand works end to end.
Degraded components are reported clearly.
No raw database/admin tools are exposed.
M5 — Hybrid Retrieval and Curated Cognee Memory

Outcome: Relevant facts and knowledge are retrieved efficiently without creating a second source of truth.

Exit criteria:

PostgreSQL full-text search and trigram search work.
Selective pgvector search works.
Official documents live on E: and indexes live on F:.
Cognee runs natively behind KnowledgeMemoryPort.
Cognee uses its own cognee_core database on the PostgreSQL 18 service.
Only promoted knowledge enters Cognee.
Raw transcripts and entire repositories do not enter Cognee.
Cognee failure does not break evidence, summaries, exact expansion, or STATE generation.
Mem0 is not installed.
M6 — Durable LangGraph Autonomous Workflow

Outcome: The autonomous developer workflow resumes safely and verifies its work.

Exit criteria:

PostgreSQL-backed LangGraph checkpoints.
Resume after process restart.
Milestone state and checklist state persist.
Requirement/scope/architecture drift gates.
Critic, deterministic scorer, and independent judge.
A/B implementation only when risk justifies it.
Human pause/resume for genuine operator decisions.
Progressive tool disclosure and JIT leases backed by PostgreSQL.
Concurrent projects cannot change each other’s tools or state.
M7 — Engineering Knowledge and Templates

Outcome: Agents have trusted examples and predictable implementation standards.

Exit criteria:

Engineering Constitution.
Approved dependency catalog.
Recipes and focused reference implementations.
Official-source provenance.
First two Copier templates pass admission:
mcp-server-python
agent-langgraph-postgres-checkpointer
No random codebase dump.
No whole-repository embedding requirement.
M8 — Operations, Recovery, Performance, and Cutover

Outcome: The platform operates reliably without expert intervention.

Exit criteria:

Native Windows lifecycle ownership.
Backup to E: and second copy to G:.
Restore tests pass.
PostgreSQL, memory service, Bifrost, Cognee, and LangGraph restart tests pass.
Resource limits prevent workstation exhaustion.
Context assembly and retrieval latency measured.
Security and secret scans pass.
Old PostgreSQL remains preserved for rollback.
Complete acceptance suite passes.
Swarm remains untouched.