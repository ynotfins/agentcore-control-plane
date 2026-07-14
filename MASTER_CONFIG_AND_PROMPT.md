# MASTER_CONFIG_AND_PROMPT.md

**Updated:** 2026-07-12 — Bifrost MCP Gateway rebuild
**Authority:** `PROJECT_ANCHOR.md` §0 Bifrost Gateway Override
**Contracts:** `contracts/agentcore-gateway-client.json`, `contracts/bifrost-upstream-mcp-registry.json`

Reusable root-level master setup guide for AgentCore after the Bifrost cutover. Normal non-Swarm IDE architecture is a **single** `agentcore-gateway` entry. Upstream MCP servers live behind Bifrost — not pasted into each IDE.

```text
IDE -> agentcore-gateway (127.0.0.1:8080/mcp)
    -> Bifrost native Gateway (H:\AgentRuntime\bifrost)
    -> upstream MCP registry (contracts)
```

Secrets live only in Windows User-scope environment variables. No `.env` files.

---

## 1. Authority

| Role | Path |
|------|------|
| Source / config authority | `D:\github\agentcore-control-plane` |
| Bifrost runtime | `H:\AgentRuntime\bifrost` |
| Compatibility / live-ops evidence only | `D:\MCP-Control-Plane` |

Constitution: `PROJECT_ANCHOR.md`
Document hierarchy: `DOC_AUTHORITY.md`
Agent contract: `AGENTS.md`
Handoff: `docs/handoffs/AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md`

**Operator approval:** Bifrost cutover task (2026-07-12) authorized this rebuild. The Go SDK smoke under `experiments/bifrost-go-sdk-smoke/` is **not** the MCP gateway.

Drive map:

```text
C: OS/apps/live IDE configs
D: source repos / config authority
E: docs archive / cold backups / exports
F: PostgreSQL / hot indexes / hot DB+search runtime
G: backup target
H: Bifrost runtime / models / caches / AgentRuntime
I: disposable scratch
J: portable
```

Forbidden: `:65432`, whole-drive filesystem MCP roots, Postgres credentials in IDE configs, requiring Swarm MCP in non-Swarm IDEs.

---

## 2. Machine evidence pointer

Canonical machine facts live in ChaosCentral / AgentCore evidence docs — not in ad-hoc chat memory:

- `docs/evidence/PC-Master-Hardware-Software-Specs.md` — hardware/software baseline (facts)
- `DOC_AUTHORITY.md` — what is authoritative vs historical
- `PROJECT_ANCHOR.md` — constitution endpoints and drive roles
- `.agentcore/docs/DOCS_INDEX.md` — arabold-docs library index (includes Bifrost)

Treat `D:\MCP-Control-Plane` as evidence only.

---

## 3. Bifrost gateway architecture

```text
Non-Swarm IDE
  -> HTTP MCP agentcore-gateway
     url:  http://127.0.0.1:8080/mcp
     auth: Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}
  -> bifrost-http.exe (v2.0.0-prerelease1) at H:\AgentRuntime\bifrost
     config.json + sqlite config/logs stores
     mcp_server_auth_mode: headers
     content logging disabled; metadata logs bounded
  -> upstream stdio/http/router MCP clients from registry
```

Ops scripts: `ops/bifrost/` (Install/Start/Stop/Test/Backup/Restore/IdeGatewayCutover).
Render: `scripts/bifrost/render_bifrost_config.py` → `H:\AgentRuntime\bifrost\config.json` + sanitized `renderers/bifrost/`.
No Docker for the Gateway runtime. Bind localhost only.

ADRs:

- `docs/adr/ADR-2026-07-12-bifrost-mcp-gateway.md`
- `docs/adr/ADR-2026-07-12-configuration-source-of-truth.md`

---

## 4. Canonical upstream registry

**File:** `contracts/bifrost-upstream-mcp-registry.json`
**Schema:** `contracts/schemas/bifrost-upstream-mcp-registry.schema.json`

Validate:

```powershell
python D:\github\agentcore-control-plane\scripts\bifrost\validate_contracts.py
```

Implemented registry posture (as of docs update; re-run validator for live truth):

- **14 enabled** upstream clients rendered into Bifrost
- **2 deferred/disabled:** `depwire-cloud`, `github-mcp`
- Bifrost client names use underscores; AgentCore IDs keep hyphens
- Swarm IDs listed under `swarm_exclusion` must not appear in non-Swarm IDE baselines

Classification matrix: `docs/bifrost/MCP_CLASSIFICATION_MATRIX.md`

---

## 5. Stable agentcore-memory identity

**Canonical id:** `agentcore-memory` (Bifrost name `agentcore_memory`)
**Implementation (current):** `scripts/agentcore_memory/server.py`
**Tools (current minimal):** `memory_health`, `memory_status`
**Note:** May report **degraded** until the fuller memory platform lands. Keep the server id stable; expand tools behind it later.

Non-Swarm path:

```text
IDE -> agentcore-gateway -> agentcore-memory
```

Never put `AGENT_CORE_PG*` credentials in IDE configs. Trusted SQL remains ops/admin only (`AGENT_DATABASE_BOOTSTRAP.md`, `contracts/global-memory-database-contract.json`).

---

## 6. Project router

**Canonical id:** `agentcore-project-router`
**Implementation:** `scripts/project_router/server.py`
**State file:** `H:\AgentRuntime\bifrost\state\active-project.json`
**Tools:** `project_list`, `project_activate`, `project_status`, `project_clear`

Project-scoped upstreams launch via wrappers:

```text
scripts/project_router/wrappers/
  serena.cmd
  depwire.cmd
  tentra.cmd
  context-fabric.cmd
  filesystem.cmd
```

Allowed roots: registered `D:\github\...` git worktrees. Reject Swarm / `F:\AgentCore\agentmemory` markers.

---

## 7. Capability profiles

See `docs/bifrost/CAPABILITY_PROFILES.md` and registry `capability_profiles`:

| Profile | Primary use | VK env (name only) |
|---------|-------------|--------------------|
| builder | Full coding/planning | `BIFROST_MCP_VIRTUAL_KEY` |
| reviewer | Read-focused review | `BIFROST_MCP_VK_REVIEWER` |
| database-validator | Memory/DB health without creds | `BIFROST_MCP_VK_DATABASE_VALIDATOR` |
| docs-knowledge | Docs + notes | `BIFROST_MCP_VK_DOCS_KNOWLEDGE` |
| operator | Ops + routing | `BIFROST_MCP_VK_OPERATOR` |

Do not invent profiles outside the registry. Never commit resolved VK values.

---

## 8. Canonical single IDE gateway connection

**Contract:** `contracts/agentcore-gateway-client.json`

Cursor's canonical global MCP file is:

```text
C:\Users\ynotf\.cursor\mcp.json
```

The normal Cursor baseline must contain exactly one AgentCore non-Swarm gateway entry named
`agentcore-gateway` at `http://127.0.0.1:8080/mcp`. Project-level `.cursor\mcp.json` or
`.mcp.json` gateway duplicates are not normal; project-specific behavior is selected through
`agentcore-project-router`, not by adding duplicate gateway entries under individual repos.

Sanitized canonical entry (env form — never resolve secrets in Git):

### JSON-style clients (Cursor / MiniMax / Mavis / Claude / Antigravity / Open Interpreter)

```json
{
  "mcpServers": {
    "agentcore-gateway": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "Authorization": "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
      },
      "timeout": 300
    }
  }
}
```

### Codex TOML

```toml
[mcp_servers.agentcore-gateway]
url = "http://127.0.0.1:8080/mcp"
http_headers = { "Authorization" = "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}" }
enabled = true
```

If a client cannot expand `${env:...}` in headers, materialize from Windows User env into the **live** config only during cutover — never commit the live secret-bearing file.

---

## 9. Client-specific renderers

Sanitized renderers (source-controlled):

| Client | Renderer |
|--------|----------|
| cursor | `renderers/gateway-clients/cursor.json` |
| codex | `renderers/gateway-clients/codex.json` |
| claude-code | `renderers/gateway-clients/claude-code.json` |
| claude-desktop | `renderers/gateway-clients/claude-desktop.json` |
| minimax | `renderers/gateway-clients/minimax.json` |
| mavis | `renderers/gateway-clients/mavis.json` |
| antigravity | `renderers/gateway-clients/antigravity.json` |
| open-interpreter | `renderers/gateway-clients/open-interpreter.json` |

Live paths are listed in `contracts/agentcore-gateway-client.json` → `client_render_hints`.
Cutover automation: `ops/bifrost/Invoke-AgentCoreIdeGatewayCutover.ps1`.
**Out of scope:** OpenClaw / ClawX.

---

## 10. Global IDE setup prompt path

Use this reusable prompt for any supported IDE:

```text
D:\github\agentcore-control-plane\docs\prompts\install-agentcore-gateway-in-ide.md
```

It encodes the operator’s 15 steps: read authority → identify config/schema → backup → preserve non-MCP settings → remove old direct baseline → add only agentcore-gateway → canonical endpoint → VK without printing → schema-correct render → validate syntax → reload → gateway discovery → verify profile/project → report unsupported capabilities → preserve rollback.

---

## 11. Server-specific operating rules

General:

1. Prefer tools via `agentcore-gateway` after cutover.
2. Activate a project before Serena / Depwire / Tentra / Context Fabric / filesystem.
3. Stop policy: do not silently downgrade Bifrost, arabold-docs, artiforge, sequential-thinking, or required Depwire verification.
4. No Context7, raw Mem0, direct Composio, or Hostinger as baseline routes.

Root Agent Rules Template (seed `AGENTS.md` / `CLAUDE.md` on new repos):

```markdown
# AgentCore Gateway Operating Rules

D:\github\agentcore-control-plane is source authority.
H:\AgentRuntime\bifrost is Bifrost runtime (not design authority).
D:\MCP-Control-Plane is compatibility/live-ops evidence only.

On every new project/repo, create AGENTS.md and CLAUDE.md at the project root if missing
(seed from MASTER_CONFIG_AND_PROMPT.md), read/verify both at session start, and keep them updated.

Non-Swarm IDE MCP baseline is a single agentcore-gateway entry
(http://127.0.0.1:8080/mcp + Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}).
Do not paste the full upstream registry into each IDE.
Do not require SwarmRecall/SwarmVault/SwarmClaw for non-Swarm IDE work.

Use agentcore-memory (stable id; may be degraded) via the gateway for memory health/status.
Use agentcore-project-router before project-scoped tools.
Use arabold-docs for exact version docs; keep .agentcore/docs/DOCS_INDEX.md current.
Use Serena (via project router) before broad code edits.
Use sequential-thinking before architecture/migration/refactor decisions.
Use Depwire via gateway for structural impact; local Depwire CLI is diagnostic fallback.
Use Tentra local mode only (H:\AgentRuntime\tentra\data).
Use context-fabric only on approved Git workspaces via project router.
Use mcp-debugger for runtime/test failures instead of guessing.
Use Artiforge for complex multi-file strategy only.
Use Obsidian for human-readable notes/handoffs.

Never put Postgres credentials or whole-drive filesystem roots in IDE configs.
Never use :65432. Never create .env files. Never print secrets.
Push after every completed task per docs/GIT_PUSH_ONLY_POLICY.md.
```

---

## 12. Depwire

- **Primary:** through `agentcore-gateway` → `depwire` (project-router wrapper).
- **Cloud:** registry `depwire-cloud` deferred/`enabled=false` until healthy; auth `Bearer env.DEPWIRE_API_KEY` when enabled.
- **Local diagnostic:** `depwire-cli` / `depwire mcp` still OK offline — see `DEPWIRE.md` and `docs/bifrost/DEPWIRE_RECONCILIATION.md`.
- Do not set `DEPWIRE_NO_TELEMETRY` unless operator requests.
- Ignore `.depwire/` and `depwire-output.json`.

---

## 13. Tentra

Local mode only (`tentra-mcp@1.3.3 --local`). Data: `H:\AgentRuntime\tentra\data`.
Details: `docs/bifrost/TENTRA_LOCAL_MODE.md`.

---

## 14. Arabold Docs

Primary docs MCP for libraries/SDKs/APIs (replaces Context7).
Index Bifrost docs as library `bifrost` version `2.0.0-prerelease1` from https://docs.getbifrost.ai — see `.agentcore/docs/DOCS_INDEX.md`.
Keep project manifests under `.agentcore/docs/` when indexing project-relevant libraries.

---

## 15. Serena

Pinned launcher via project-router wrapper (`serena.exe start-mcp-server ...`).
Always activate the target `D:\github\...` project first. Do not emit git-based `uvx` launch commands as the governed path.

---

## 16. Context Fabric

Project-scoped only via router wrapper. Approved Git-managed workspaces only.
Do not initialize under `F:\AgentCore\agentmemory` or Swarm roots.

---

## 17. Artiforge

HTTP upstream; connection string is `env.ARTIFORGE_MCP_URL` (compose PAT locally into User env — never commit). High-leverage scans/refactor strategy only.

---

## 18. Obsidian

Long-form human notes, decisions, runbooks. Launcher uses Windows env names (`OBSIDIAN_API_KEY`, `OBSIDIAN_BASE_URL`, etc.). REST default host `https://127.0.0.1:27124`. Never embed key values in Git.

---

## 19. Security

- Windows User-scope env vars only; no `.env` files.
- Never print or commit secrets, resolved VKs, PATs, DB passwords, or live secret-bearing IDE configs.
- Bifrost: headers VK auth; content logging disabled.
- Localhost bind only for gateway.
- No whole-drive filesystem roots; filesystem MCP is project-worktree scoped.
- No direct Postgres credentials in IDE MCP configs.
- See `SECURITY.md`.

---

## 20. Validation

Minimum deterministic checks:

```powershell
python D:\github\agentcore-control-plane\scripts\bifrost\validate_contracts.py
# Optional ops smoke (record actual results; do not fabricate):
# ops\bifrost\Test-AgentCoreBifrostGateway.ps1
```

Also: secret/junk scan before commit; IDE JSON/TOML parse after cutover; confirm single gateway entry per migrated client.

**Docs update note:** Contract schema validation was run successfully during this authority-doc update (14 enabled / 2 deferred). Full live gateway/IDE acceptance remains evidenced only where ops tests and cutover evidence files exist — do not invent pass/fail beyond that.

---

## 21. Backup and rollback

- Backup root example: `E:\AgentCore-Backups\bifrost-gateway-cutover-20260712-223149`
- Hash manifest: `artifacts/bifrost-gateway-cutover-2026-07-12/BACKUP_MANIFEST.md`
- Runbooks: `docs/bifrost/MIGRATION_RUNBOOK.md`, `docs/bifrost/ROLLBACK_RUNBOOK.md`
- Ops: `Backup-AgentCoreBifrostConfig.ps1`, `Restore-AgentCoreBifrostConfig.ps1`

---

## 22. Swarm exclusion boundary

SwarmRecall, SwarmVault, and SwarmClaw are a **separate ecosystem**.

- Non-Swarm IDEs must not depend on Swarm MCP.
- Bifrost cutover must not modify Swarm product installs (exclude-only from IDE baselines).
- OpenClaw/ClawX are outside this IDE gateway cutover.
- Historical Swarm-first baseline docs are superseded for non-Swarm IDE work (`DOC_AUTHORITY.md`).

---

## APPENDIX: Historical direct per-IDE full-server blocks

> **ROLLBACK / HISTORICAL ONLY — NOT NORMAL ARCHITECTURE.**
> Before Bifrost, each IDE carried a full direct MCP server list (arabold-docs, serena, sequential-thinking, swarmrecall, swarmvault, filesystem with broad roots, etc.). That model drifted and is superseded by the single `agentcore-gateway` entry.
> Keep backups under `E:\AgentCore-Backups\...` for emergency restore. Do not present the blocks below as the current baseline. Prefer restore-from-backup over re-authoring a hybrid.

### Historical pattern (illustrative — do not deploy as normal)

```json
{
  "mcpServers": {
    "arabold-docs": { "command": "...", "args": ["..."] },
    "serena": { "command": "...", "args": ["..."] },
    "sequential-thinking": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-sequential-thinking@..."] },
    "swarmrecall": { "url": "..." },
    "swarmvault": { "command": "...", "args": ["..."] }
  }
}
```

Per-IDE cleanup prompts under `docs/prompts/*-cleanup-prompt.md` may still describe older direct-server remediation; for gateway install use `docs/prompts/install-agentcore-gateway-in-ide.md` instead.

Experiment note: `experiments/bifrost-go-sdk-smoke/` remains an isolated Go SDK POC — not a rollback path for the MCP gateway.
