# AgentCore Engineering Constitution

**Authority:** `PROJECT_ANCHOR.md` → `BLUEPRINT.md` → this document.  
**Status:** Approved — operator-verified 2026-07-16.  
**Scope:** All managed projects on CHAOSCENTRAL using the AgentCore platform.  
**Machine:** CHAOSCENTRAL (Windows 11 Pro; see `docs/evidence/PC-Master-Hardware-Software-Specs.md`).

This document is concise by design. Each rule resolves a real ambiguity or prevents a
known failure. Do not expand with preferences that have not been validated against the
current official toolchain.

---

## 1. Immutable Boundaries

These decisions require explicit operator approval to change:

- PostgreSQL 18 is canonical. No second database authority.
- Secrets come from Windows User environment variables only. Never `.env` files.
- AgentCore memory is accessed through `agentcore-memory` behind `agentcore-gateway`.
- Swarm (SwarmRecall, SwarmVault, SwarmClaw) is independent. Do not couple to it.
- No Docker or WSL dependency for the core platform.
- Mem0 is not installed. Cognee is the semantic/graph subsystem.
- LangGraph owns durable workflow execution and checkpoints.

---

## 2. Python

### 2.1 Version and Environment

- **Minimum:** Python 3.12. Target Python 3.13 on CHAOSCENTRAL.
- **Packaging:** `pyproject.toml` with `[project]` metadata and pinned dev deps.
- **Lock:** Maintain a `requirements.txt` (or `uv.lock`) alongside `pyproject.toml`.
- **No venvs in repository roots.** Use `D:\test\<project>\.venv` or project-local paths.
- Dependencies must be in the governed catalog. Unapproved packages require a proposal.

### 2.2 Code Style

```python
from __future__ import annotations  # always first in every file
```

- Type-annotate every public function signature. Use `typing_extensions` for backports.
- `ruff` for linting and formatting (`line-length = 100`, `target-version = "py312"`).
- `mypy --strict` for type checking. Fix rather than silence.
- Docstrings on public classes and functions. No narrating comments.
- No `print()` in library code. Use structured logging (§7).

### 2.3 Sync/Async

- Choose sync or async consistently within a module. Do not mix arbitrarily.
- `asyncio.run()` is acceptable for CLI entry points. Never inside a running event loop.
- Psycopg: use `psycopg.connect()` (sync) or `psycopg.AsyncConnection` (async) — match the ambient loop.
- LangGraph: use `AsyncPostgresSaver` when the workflow node is async; `PostgresSaver` otherwise.

### 2.4 Error Handling

```python
# Specific, not bare:
try:
    ...
except psycopg.OperationalError as exc:
    _log(f"db_error: {exc.__class__.__name__}")
    raise  # re-raise; do not swallow unless deliberately degraded

# BLE001 exemption only at explicit recovery boundaries
```

- Never swallow exceptions silently in library code.
- Always log before re-raising in a recovery boundary.
- Use `contextlib.suppress` only when the suppressed exception is explicitly listed.

### 2.5 Security and Secrets

```python
# Correct: read from env
pg_pass = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
# Wrong: hardcoded, .env file, default non-empty string
```

- Scan all files with `detect-secrets` or `trufflesecurity/trufflehog` before commit.
- Never log secret values. Log only key names and redacted indicators.
- Validate: `assert pg_pass, "AGENT_CORE_POSTGRES_PASSWORD not set"` in startup.

---

## 3. TypeScript / Node.js

- **Minimum:** Node 20 LTS. Prefer Node 22.
- **Runtime:** Native Node.js (no Bun or Deno) unless operator-approved.
- **Types:** `strict: true` in `tsconfig.json`. No `any` without a comment.
- **Format:** `prettier` + `eslint`. Match project's existing config.
- **Modules:** ES Modules (`"type": "module"` in `package.json`) for new projects.
- Secrets: `process.env.KEY ?? (() => { throw new Error("KEY not set"); })()`.
- No `require()` in new code. No CommonJS in new projects.

---

## 4. PowerShell

- **Minimum:** PowerShell 5.1. Prefer 7.x for new scripts.
- Always start scripts with `Set-StrictMode -Version Latest` and appropriate `$ErrorActionPreference`.
- Use `[CmdletBinding()]` for scripts that accept parameters.
- Prefer named parameters. No positional parameters in shared scripts.
- Secrets: `$env:KEY` only. Never hardcode.
- Return structured objects (`[PSCustomObject]`) not free text.
- Exit codes: `exit 0` for success, `exit 1` for failure. Test in CI.

---

## 5. PostgreSQL and Migrations

### 5.1 Migration Policy

- Every schema change requires an UP migration and a DOWN rollback migration.
- Migration files: `migrations/<milestone>/NNN_up_<description>.sql` and `_down_`.
- All UP migrations are wrapped in `BEGIN; ... COMMIT;`.
- Use `IF NOT EXISTS` / `ON CONFLICT DO NOTHING` for idempotent creates.
- Record every applied migration in `agentcore.schema_migrations`.
- **Destructive migrations** (DROP TABLE, TRUNCATE, ALTER with data loss) require explicit operator approval and a verified backup before execution.

### 5.2 Schema Design

- Every table: `id uuid PRIMARY KEY DEFAULT gen_random_uuid()` and `created_at timestamptz NOT NULL DEFAULT now()`.
- Use `agentcore` schema for all platform tables. Use `wf_` prefix for M6 workflow tables.
- All FK references use `ON DELETE RESTRICT` unless a cascade is explicitly justified.
- Use `SECURITY DEFINER` functions for cross-schema writes. Never give normal roles direct table writes across security boundaries.
- Row-Level Security (`ENABLE ROW LEVEL SECURITY`) for tables shared across projects.
- Project isolation: every shared table carries `project_id uuid` and the `assert_project_scope()` function guards writes.

### 5.3 Roles

```
agentcore_read     — SELECT only
agentcore_ingest   — INSERT on event tables
agentcore_worker   — INSERT/UPDATE on job/context tables
agentcore_admin    — ALL (maintenance only)
agentcore_backup   — SELECT + COPY for backup runners
agentcore_cognee   — Cognee-owned tables in cognee_core
```

No IDE agent receives database credentials or the `agentcore_admin` role.

### 5.4 pgvector

- Index strategy: exact search for small datasets; HNSW only when benchmarked benefit is proven.
- IVFFlat, pgvectorscale, and DiskANN require benchmark evidence before adoption.
- Always maintain a PostgreSQL FTS/trigram fallback when vector retrieval is unavailable.

---

## 6. MCP Servers

### 6.1 Stdio (Bifrost-compatible)

- Protocol: newline-delimited JSON-RPC (NDJSON). Bifrost current version: `2025-06-18`.
- Accept and echo the negotiated protocol version.
- Never expose credentials, raw database access, or admin tools in the tool surface.
- Tool surface: exactly the declared list — no wildcard expansion in production.
- Error responses must include `{"error": {"code": -32000, "message": "..."}}` in JSON-RPC format.
- Use `sys.stderr` for logging (not stdout, which is the JSON-RPC channel).

```python
# Reference: scripts/agentcore_memory/server.py
```

### 6.2 Streamable HTTP

- Use `mcp` Python SDK `>=1.28.1,<2` for Streamable HTTP servers.
- Bind to `127.0.0.1` only unless operator approves external binding.
- Authentication: Bearer token from env var. Never hardcode.
- Health endpoint at `/health` returning `{"ok": true}`.

### 6.3 Tool Design

- Tool names: snake_case, descriptive verbs (`append_event`, not `add` or `event_add`).
- Input schemas: `additionalProperties: false` always.
- Required fields listed explicitly. Optional fields have meaningful defaults.
- One purpose per tool. Do not combine read and write into one tool.
- Tools are idempotent where possible. Document when they are not.

---

## 7. LangGraph Workflows

### 7.1 Graph Design

- State: `TypedDict` with reducers for list fields (`Annotated[list, operator.add]`).
- Nodes: pure functions `(state: State) -> dict`. No side effects that aren't through approved DB helpers.
- Edges: conditional where needed; `route(state) -> str` returns the next node name from `state.next_action`.
- Always set `interrupt_before=["human_pause"]` in `compile()`.

### 7.2 Checkpoints

- Use `langgraph-checkpoint-postgres==3.1.0` with `PostgresSaver`.
- Call `saver.setup()` once at startup to create checkpoint tables.
- Thread IDs: UUID strings. Always project-scoped (`f"project_{project_id}_{uuid}"` form recommended).
- Do not use raw `thread_id` strings without UUID structure — they must stay under 255 chars.

```python
with PostgresSaver.from_conn_string(conninfo) as saver:
    saver.setup()
    graph = builder.compile(checkpointer=saver, interrupt_before=["human_pause"])
```

### 7.3 Human Review

- Pause: `interrupt({"question": "...", "pause_db_id": "..."})` in the `human_pause` node.
- Resume: `graph.invoke(Command(resume=decision), config=config)`.
- Record every pause/resume in `agentcore.wf_human_pauses`.
- Timeout all pauses. Default: 24 hours. Set `timeout_at` in the DB row.

### 7.4 Gates and Critics

- All 7 gates run deterministically BEFORE any LLM critic call.
- Critics are selected by risk class: none for `low`; more for `high`/`critical`.
- Score formula: `0.60 * det_checks + 0.25 * gates + 0.15 * critics`.
- Judge is independent: `proceed ≥ 0.85`; `needs_operator ≥ 0.60`; `block` otherwise.
- A/B: enabled only when `risk_class ∈ {high, critical}` AND `uncertainty ≥ 0.5`.

---

## 8. Typing and Validation

- `pydantic>=2.0` for runtime data validation. Use `model_validator` not custom `__init__`.
- Never use `dict` when a `TypedDict` or Pydantic model is appropriate.
- Use `Literal["value1", "value2"]` for constrained string fields.
- PostgreSQL enums → Python `enum.Enum` subclasses. Keep them in sync.
- Validate at system boundaries (API input, DB output, file read). Do not validate internal function calls.

---

## 9. Structured Logging and Diagnostics

```python
import json, sys
def _log(level: str, msg: str, **ctx) -> None:
    sys.stderr.write(json.dumps({"ts": _now(), "level": level, "msg": msg, **ctx}) + "\n")
    sys.stderr.flush()
```

- Log to stderr. Never stdout (reserved for JSON-RPC / tool output).
- Structured JSON always. No freeform log strings in library code.
- Required fields: `ts` (ISO-8601 UTC), `level` (debug/info/warn/error), `msg`.
- Never log secret values. Log key names only: `{"secret_key": "AGENT_CORE_POSTGRES_PASSWORD"}`.
- Log at boundaries: startup, shutdown, every external call, every error.

---

## 10. Security and Secret Handling

- Source: Windows User-scope environment variables. No `.env` files for AgentCore.
- Validation at startup: fail fast if required env vars are absent.
- Secret scan on every commit: `trufflehog` or `detect-secrets` in pre-commit.
- No secret values in: documentation, contracts, IDE configs, logs, evidence, Git, or OpenMemory.
- Services bind to `127.0.0.1` by default. Approval required for external binding.
- MCP tools never expose raw database credentials or admin operations.
- AgentCore write boundary: only the assigned project/worktree. `assert_project_scope()` enforces.

---

## 11. Tests and Acceptance Evidence

- **Test framework:** `pytest` with `pytest-cov`.
- Every test file: `tests/test_<module>.py`.
- Unit tests: fast, no external dependencies, mock DB with `pytest-mock`.
- Integration tests: isolated temporary database or `agentcore_<test>_<ts>` database. Clean up after.
- Acceptance tests: deterministic first, LLM critic optional.
- **Coverage target:** ≥80% for library code.
- No test may modify shared production state.
- Tests must pass before marking a Milestone complete.

---

## 12. Observability

- Health endpoint: `/health` or `memory_status` returning `{"ok": true/false}`.
- Component degradation: report clearly, do not hide. Cognee failure → PostgreSQL-only mode.
- Structured diagnostic bundle: one command to collect logs, version info, config (no secrets).
- Metric collection via PostgreSQL queries where practical. No additional telemetry daemon required.

---

## 13. Dependency Policy

- All runtime dependencies must be in the governed catalog (`docs/engineering/dependency-catalog/catalog.yaml`).
- Catalog entry required fields: package, ecosystem, version_policy, source, license, provenance.
- Unapproved packages → submit a proposal with evidence. Agent must wait for approval.
- Do not use `pip install <package>` without a catalog entry or active proposal.
- `requirements.txt` or `pyproject.toml` must pin major+minor versions (`==1.2.5` or `>=1.2,<2`).
- "Latest" is never automatically approved. Test against the pinned version.

---

## 14. Release and Rollback

- Every schema-level release requires a DOWN migration.
- Every service change requires a rollback runbook (single command or sequence).
- Tag releases in Git. Format: `vN.N.N` for platform releases, `mN` for Milestone gates.
- Backup before any destructive change. Restore test before marking the backup as accepted.
- Rollback proof is part of every Milestone exit criterion.

---

## 15. Git and Worktree Safety

- Push after every completed task: `git push origin <branch>`.
- Do not `pull`, `fetch`, `merge`, or `rebase` unless the operator asks.
- Never force-push without explicit operator approval.
- Source-controlled files only: no runtime state, secrets, credentials, generated binaries, or DB dumps.
- `.gitignore` must cover: `.depwire/`, `*.pyc`, `__pycache__/`, `.venv/`, `*.egg-info/`, `node_modules/`, `dist/`, `build/`.
- Worktree isolation: each feature branch gets an isolated worktree in `D:\github\` or approved path.
- The canonical source repository is `D:\github\agentcore-control-plane`.

---

## 16. AgentCore Memory and STATE Usage

- Normal agents: use `agentcore-memory` tools (`append_event`, `retrieve_context`, etc.).
- Never issue raw SQL from normal IDE agents.
- Durable project history is effectively unbounded by model-token limits. Context profiles bound
  one active request or retrieval page only; 4096 is acceptance/legacy-only and one million is
  not a storage ceiling.
- Compaction is non-destructive. Original evidence and exact source edges remain canonical;
  incorrect summaries are superseded and rebuilt, never overwritten.
- Before asking the operator to repeat missing history, use paginated `retrieve_context`,
  `expand_source`, and `build_handoff` to recover from PostgreSQL plus retained H:/E: artifacts.
- Project `STATE.md` is generated. Agents contribute through `agentcore-memory`, never by editing STATE directly.
- `startup_context` returns the current capability profile (M6). Use it to discover available tools.
- Long-term curated knowledge → `propose_fact` → operator promotion → Cognee.
- Session lifecycle: open with `session_open`, close with `session_close`. Never leave sessions open indefinitely.
- Compaction is automatic. Never manually delete evidence rows.

---

## 17. Copier Templates

- Use Copier `>=9.0` for project templates.
- Template root: `templates/<name>/copier.yml` + `{{project_slug}}/` subdirectory.
- Approved Copier templates must use an explicit template suffix, normally `.jinja`, for files containing Jinja. An empty suffix is allowed only when the template intentionally renders every eligible file and repository validators prove that parser-sensitive template sources do not create invalid workspace artifacts.
- Every approved template must pass the admission gate before entering the catalog.
- Templates generate a project foundation. They do not contain business logic or reference implementations.
- Approved templates: `mcp-server-python`, `agent-langgraph-postgres-checkpointer`.
- Template updates: `copier update` from within the generated project directory.

---

*Last reviewed: 2026-07-16. Review trigger: any change to official toolchain versions, new Milestone, or operator instruction.*
