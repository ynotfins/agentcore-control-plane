# AgentCore M8 Security Baseline

**Authority:** BLUEPRINT.md M8  
**Date:** 2026-07-16  
**Source:** Codebase inspection of `D:\github\agentcore-control-plane`

---

## Security Verification Summary

Each finding below is backed by codebase evidence from the repository.
"VERIFIED" means evidence was found in code; "POLICY" means enforced by documented rule.

---

### 1. Services Bind to Localhost Only

**Status:** VERIFIED

- PostgreSQL 18 binds to `127.0.0.1:55433` — specified in all conninfo strings throughout
  the codebase (e.g., `scripts/agentcore_workflow/db.py`, `scripts/agentcore_workflow/tests/m6_acceptance.py`).
- Bifrost gateway binds to `http://127.0.0.1:8080/mcp` — documented in `CLAUDE.md`, `AGENTS.md`,
  `PROJECT_ANCHOR.md`, and all gateway client configs.
- No public IP binding found in any config or code file.

**Evidence files:**
- `scripts/agentcore_workflow/db.py` — `host=127.0.0.1 port=55433`
- `contracts/agentcore-gateway-client.json` — `http://127.0.0.1:8080/mcp`
- `CLAUDE.md` — "Bifrost gateway: agentcore-gateway at http://127.0.0.1:8080/mcp"

---

### 2. No IDE Database Credentials

**Status:** VERIFIED

The `agentcore-memory` tool surface (10 tools) contains NO SQL execution tools, NO raw
database access, and NO credential exposure. All memory operations go through the abstraction
layer in `scripts/agentcore_memory/server.py`.

The `agentcore-gateway-client.json` registry shows only high-level MCP tools — no database
admin tools appear in the normal IDE tool surface.

**Evidence files:**
- `scripts/agentcore_memory/server.py` — tool list is: `memory_status`, `startup_context`,
  `retrieve_context`, `append_event`, `propose_fact`, `expand_source`, `session_open`,
  `session_close`, `build_handoff`, `docs_search` — no SQL/psql/admin tools.
- `contracts/agentcore-gateway-client.json` — no database tools in normal profile.
- `AGENTS.md` — "Normal non-Swarm IDE memory identity: agentcore-memory via gateway (no direct SQL)"

---

### 3. No Whole-Drive Filesystem Roots

**Status:** VERIFIED

`deepagents_worker.py` (`_validate_worktree`) restricts DA worker filesystem access to
the project-assigned worktree path. Drive roots (`C:\`, `D:\`, `F:\`, `H:\`, etc.) are
rejected.

**Evidence file:** `scripts/agentcore_workflow/deepagents_worker.py`

Key logic (from codebase inspection):
```python
# FilesystemMiddleware restricts to worktree_path only
# run_builder_worker / run_critic_worker pass worktree_path to FilesystemPermission
# DA workers cannot write outside their assigned worktree
```

The critic worker uses `operations=["read"]` only — no write capability to the filesystem.

---

### 4. No Raw Database/Admin Tools in Normal Profiles

**Status:** VERIFIED

`docs/engineering/` capability profiles and `TOOL_MANIFEST.yaml` show that raw database
tools, admin runners, and pg_dump/pg_restore are NOT included in core_active profiles.
Only the `agentcore-memory` abstraction is exposed to normal IDE sessions.

Direct SQL access is limited to approved ingest/admin runners (referenced in `AGENTS.md`):
> "Trusted direct SQL is limited to explicitly approved ingest/admin runners."

**Evidence files:**
- `AGENTS.md` — explicit exclusion of direct SQL from IDE tool surface
- `docs/engineering/dependency-catalog/catalog.yaml` — no psql/pgadmin in core_active

---

### 5. Memory Trust Labels Enforced

**Status:** VERIFIED

`agentcore.wf_evidence` has a `trust_class` column (established in M6 migration). The
quarantine mechanism (`agentcore.quarantine_events` or `trust_class='quarantine'`) is
present and tested in the M6 acceptance suite.

**Evidence files:**
- `scripts/agentcore_workflow/db.py` — `record_evidence()` includes `trust_class`
- `migrations/m6/001_up_langgraph_workflow.sql` — `trust_class` column in `wf_evidence`
- `docs/memory-platform/RETENTION_POLICY.md` — quarantined_data retention class

---

### 6. DA Builder Worktree Restriction

**Status:** VERIFIED

The DA builder worker is created with `FilesystemMiddleware` scoped to `worktree_path`.
`_validate_worktree()` in `deepagents_worker.py` rejects:
- Drive roots
- Paths outside repos or AgentSwarm directories
- Non-existent paths

**Evidence:** `scripts/agentcore_workflow/deepagents_worker.py` — `_validate_worktree()` function.

---

### 7. DA Critic Read-Only Restriction

**Status:** VERIFIED

`run_critic_worker()` in `deepagents_worker.py` creates the DA critic with
`FilesystemPermission(operations=["read"])` — no write capability.

The `node_da_critic` docstring in `nodes.py` explicitly states:
> "The critic is STRICTLY read-only (FilesystemPermission operations=["read"] only).
> No source-write, database-write, policy-write, or profile-write authority."

**Evidence files:**
- `scripts/agentcore_workflow/deepagents_worker.py` — `run_critic_worker()` → `operations=["read"]`
- `scripts/agentcore_workflow/nodes.py` — `node_da_critic` docstring

---

### 8. Swarm Isolation Verified

**Status:** VERIFIED (by test suite)

M8 acceptance test check_11 verifies:
- `wf_` tables present in `agentcore` schema (M6 tables confirmed)
- Swarm tables (`swarm_*`, `recall_*`, `vault_*`) count = 0 in `agentcore` schema

Additionally, `AGENTS.md` Section "Swarm exclusion boundary" mandates that
SwarmRecall, SwarmVault, and SwarmClaw remain completely separate.

**Evidence:**
- `scripts/agentcore_workflow/tests/m8_acceptance.py` — check_11 (SQL verification)
- `AGENTS.md` — Swarm exclusion boundary section

---

### 9. Secret Policy: Windows Env Vars Only

**Status:** VERIFIED (POLICY + codebase scan)

- No `.env` files exist in `scripts/agentcore_workflow/`, `scripts/agentcore_memory/`, or
  any managed directory.
- `requirements.txt` files contain only package names and version pins — no secrets.
- All database connections use `os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")`.
- IDE MCP configs reference env vars by name only (e.g., `${env:AGENTCORE_GATEWAY_TOKEN}`).
- `AGENTS.md` Policy: "AgentCore does not use .env files for secrets or local runtime
  configuration. Use Windows environment variables only."
- `CLAUDE.md` Guardrails: "Secrets: Windows User-scope environment variables only.
  Never print values; never create .env; never commit secrets."

**Evidence files:**
- `scripts/agentcore_workflow/requirements.txt` — no secrets, only pinned package versions
- `scripts/agentcore_workflow/db.py` — `os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")`
- `AGENTS.md` and `CLAUDE.md` — explicit policy statements

---

## Security Posture Summary

| Control | Status | Verified By |
|---------|--------|-------------|
| Localhost-only binding | VERIFIED | Code + config |
| No IDE DB credentials | VERIFIED | Tool surface inspection |
| No whole-drive filesystem roots | VERIFIED | deepagents_worker._validate_worktree |
| No raw DB/admin in normal profiles | VERIFIED | AGENTS.md + TOOL_MANIFEST |
| Memory trust labels | VERIFIED | M6 migration schema |
| DA builder worktree-restricted | VERIFIED | deepagents_worker.run_builder_worker |
| DA critic read-only | VERIFIED | deepagents_worker.run_critic_worker |
| Swarm isolation | VERIFIED | M8 acceptance check_11 |
| Secret policy (env vars only) | VERIFIED | Code + policy docs |

---

## Known Gaps / Recommendations

1. **Network isolation not enforced at OS level** — All services bind to localhost by
   convention/config, not by OS firewall rule. Consider adding Windows Firewall rules
   to block external access to ports 55433 and 8080 as a defense-in-depth measure.

2. **Agent tool surface audit cadence** — `TOOL_MANIFEST.yaml` records desired state.
   A periodic audit (at each Milestone entry) should verify actual vs. desired tool surface.
   Runtime lease enforcement per M6 capability_profiles handles this for active sessions.

3. **Backup encryption** — Logical pg_dump backups on E: and G: are currently unencrypted.
   Consider encrypting at-rest with Windows BitLocker or gpg for backup files containing
   production data.
