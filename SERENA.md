# Serena — AgentCore Semantic Code Intelligence

**Authority:** `D:\github\agentcore-control-plane`
**Scope:** AgentCore-managed developer tooling and the optional neutral dual-control-plane
Cursor workspace for read-only collision/boundary audits only
**Runtime:** Serena `1.5.4.dev0` catalogued; shared Bifrost upstream dormant pending explicit per-session project routing
**Last verified:** 2026-08-02

This document describes how Serena is configured, routed, isolated, validated,
and used by supported IDEs. It is a developer-tooling contract. It does not
make Serena a memory database, a workflow engine, or an authority over Swarm.

## Authority and ownership

Use this order when Serena behavior conflicts with another document:

1. `D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`
2. `D:\github\agentcore-control-plane\DOC_AUTHORITY.md`
3. `D:\github\agentcore-control-plane\BLUEPRINT.md`
4. `D:\github\agentcore-control-plane\CONTEXT_BLOCK.md`
5. `D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json`
6. This file and current Serena repair evidence

AgentCore owns:

- the Bifrost Serena registry entry and renderer wiring;
- project-router selection and write-scope policy;
- the Serena maintenance validator and rollback procedure;
- the semantic-toolchain policy rendered to IDE profiles.

Serena owns only semantic code intelligence: language-server-backed symbol
navigation, references, diagnostics, safe refactors, and project-local Serena
cache/memory. Serena does not own:

- AgentCore PostgreSQL or `agentcore-memory`;
- LangGraph checkpoints or workflow state;
- generated `STATE.md` projections;
- Bifrost policy or virtual keys;
- Swarm runtime memory, databases, credentials, or processes.

The accepted concurrent-safe path is:

```text
IDE
  -> one agentcore-gateway MCP entry
  -> Bifrost at http://127.0.0.1:8080/mcp for global/project-explicit tools
IDE/host native project tools or explicit-cwd local diagnostics
  -> language servers and project-local cache
```

The prior shared Serena route used one machine-global `active-project.json` and cannot isolate simultaneous IDE sessions on different projects because Bifrost does not forward trusted caller/project identity to the shared STDIO process. Serena therefore remains dormant in normal gateway profiles. Do not re-enable it by profile alone.

The memory path is separate:

```text
IDE -> agentcore-gateway -> agentcore-memory -> PostgreSQL 18
```

Serena contributes semantic evidence to the agent; it does not replace the
durable memory or database path.

## Current project configurations

Global Serena configuration:

`C:\Users\ynotf\.serena\serena_config.yml`

The current baseline registry may contain the two control-plane roots for
neutral dual-workspace boundary audits:

- `D:\github\agentcore-control-plane`
- `D:\github\swarm-ecosystem-control`

That dual listing does **not** authorize normal AgentCore IDE continuity on
Swarm projects. If the operator-selected project is Swarm-owned, HARD STOP with
`swarm_project_refused`. Do not open AgentCore memory sessions, enroll IDE
profiles, or persist Swarm work through AgentCore for Swarm-owned roots.

AgentCore:

`D:\github\agentcore-control-plane\.serena\project.yml`

Configured languages:

- `python`
- `powershell`

Swarm control-plane path (boundary-audit only; not AgentCore continuity):

`D:\github\swarm-ecosystem-control\.serena\project.yml`

Configured languages:

- `powershell`
- `typescript` (Serena's JavaScript language-server route)

Other repositories are not modified by this repair. Before using Serena on
another AgentCore / enrolled non-Swarm repository, create or regenerate that
repository's current `.serena\project.yml` with a valid `languages` list and
register it through the approved project workflow. Do not put unrelated
projects into one shared Serena process or create a machine-wide fallback
configuration.

Global behavior:

- `language_backend: LSP`
- `gui_log_window: false`
- `web_dashboard: true`
- `web_dashboard_open_on_launch: false`
- dashboard binds to loopback
- project-local Serena data remains under each project’s `.serena` directory

The Swarm product repositories remain independent runtime projects under Swarm
authority. Do not add Swarm product directories to the AgentCore global MCP
baseline. Do not treat Swarm-owned paths as AgentCore-managed projects.

## Dormant Bifrost route and project switching

The source registry is:

`D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json`

The Serena wrapper is:

`D:\github\agentcore-control-plane\ops\bifrost\wrappers\serena-prewarm.js`

The active project-router state (current Bifrost runtime root) is:

`F:\AgentCore\runtime\bifrost\state\active-project.json`

Historical path `H:\AgentRuntime\bifrost\state\active-project.json` is not the
final AgentCore home; remaining H: vacation is Milestone M9.

The retained wrapper is rollback/future-router material. When explicitly tested by an operator it:

1. starts Serena with a synthetic `initialize`, `tools/list`, and `ping` path
   so Bifrost can complete discovery quickly;
2. buffers readiness safely without forwarding an unbounded child stderr
   stream;
3. starts the child for the active project only;
4. allows only the registered control-plane paths;
5. restarts the Serena child when `agentcore-project-router` switches the
   active AgentCore / enrolled non-Swarm project (or a read-only dual-workspace
   boundary-audit activation);
6. never expands the allowlist to vendor roots or whole-drive paths.

Project switching is not a concurrent-session security boundary. It is one active Serena child
at a time, with separate language-server state and separate `.serena` caches.
A combined Cursor workspace may show both control planes for read-only
collision audits, but the active project and write boundary remain singular,
and normal AgentCore sessions must refuse Swarm-owned selection with
`swarm_project_refused`.

## Optimal agent workflow

Use this sequence for a nontrivial task:

1. Resolve the exact repository/worktree through the host and read its authority files.
2. Use the IDE's native semantic/source tools or an explicit-cwd local Serena diagnostic only when the host owns that process.
3. Complete AgentCore `session_open` and `startup_context` before tool work.
4. If a host-local Serena process is explicitly available, call `initial_instructions` once for that process/session.
5. Start with `get_symbols_overview` for the relevant source file.
6. Use `find_symbol` to locate the precise symbol and, only when needed, read
   its body.
7. Use `find_referencing_symbols` and `find_implementations` before rename,
   delete, interface, or cross-file changes.
8. Use `get_diagnostics_for_file` after changes that affect language-server
   semantics.
9. Use `search_for_pattern` for configuration, documentation, or an unknown
   text location; do not use text search as a substitute for semantic
   references.
10. Use `rename_symbol` or `safe_delete_symbol` for symbol-aware refactors.
11. Run Depwire before and after structural changes.
12. Run the narrowest relevant validators, then record evidence through
   `agentcore-memory`.

Serena does not need to be called for every one-line documentation typo. It is
mandatory before unfamiliar structural edits, public API changes, symbol
moves, rename/delete operations, architecture-sensitive changes, and debugging
where call/reference relationships matter.

## Powerhouse MCP toolchain

The global semantic policy is the canonical enforcement point:

`D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml`

Cursor and other IDE rule renderings are generated from it:

`D:\github\agentcore-control-plane\ide-profiles\<ide>\GLOBAL_RULES.md`

Use the tools by task class rather than loading every server on every turn:

- **Sequential Thinking:** plan, critique, tradeoff, recovery, migration, and
  cross-system decisions.
- **Serena:** optional host-local symbols, references, diagnostics, and semantic refactors when an explicit project-owned process is available; not a shared gateway dependency.
- **Arabold Docs:** exact current documentation and version-specific API/SDK
  behavior before external package or protocol work.
- **Context Fabric:** repo-local capture, drift, health, and decision checkpoints at bootstrap and Milestone entry/exit.
- **Depwire:** explicit-cwd local dependency context, impact analysis, safety simulation, and post-change verification.
- **Artiforge:** high-leverage architecture scans and system-level hotspots;
  not routine single-file work.
- **Tentra:** explicit-project local architecture/code graph work only when the current Milestone requires it.

If a mandatory tool is unavailable, do not silently claim equivalent
verification. Block high-risk structural edits and report the missing evidence.

## IDE usage

All normal AgentCore / enrolled non-Swarm IDE clients use the same gateway contract:

`http://127.0.0.1:8080/mcp`

They do not add a direct Serena entry. Shared Serena is not exposed through normal Bifrost profiles until a per-session project identity is part of the routing contract.

| IDE/client | Gateway configuration | Serena usage |
| --- | --- | --- |
| Cursor | `C:\Users\ynotf\.cursor\mcp.json` | One `agentcore-gateway` entry; activate the project before semantic work. |
| Codex | `C:\Users\ynotf\.codex\config.toml` | Use the gateway and named project router; do not add direct Serena. |
| Claude Code | `C:\Users\ynotf\.claude.json` | Use the gateway; preserve client-local scope. |
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` | Use the gateway; follow its env-header limitation. |
| MiniMax Code / Mavis | `C:\Users\ynotf\.minimax\mcp\mcp.json` | Use the gateway; Mavis is the same data root, not a second baseline. |
| MiniMax Agent Classic | Matrix custom-MCP UI | Enroll only `agentcore-gateway`; no local direct Serena entry. |
| Antigravity / Gemini | `C:\Users\ynotf\.gemini\config\mcp_config.json` or its documented alternate | Use the gateway and project router. |
| Open Interpreter CLI | `%APPDATA%\interpreter\config.json` | Use the gateway; the GUI executable is unsupported for this MCP baseline. |
| Cherry Studio | Governed local storage enrollment | Use only the AgentCore gateway record; never add direct upstream Serena. |
| LangGraph production/Studio | `scripts\agentcore_workflow\mcp_client.py` | Use localhost gateway from the workflow capability profile; never direct Serena credentials. |

Profile restrictions are intentional:

- ChatGPT’s secure tunnel profile excludes Serena, filesystem, shell, Depwire,
  Tentra, and Bifrost administration.
- Reviewer and docs profiles may expose only read-focused subsets.
- A profile that does not include Serena must not be “fixed” by adding a direct
  IDE MCP entry; use the appropriate governed profile.
- SwarmClaw, SwarmRecall, and SwarmVault runtime processes never use
  AgentCore/Bifrost/Serena. Former language permitting AgentCore IDE
  development continuity on Swarm projects is historical and revoked. Use
  Swarm’s own control plane for Swarm work; AgentCore may only perform
  read-only dual-workspace boundary audits.

## Failure handling and self-healing

### `KeyError: 'languages'`

Do not manually edit `state.vscdb`, delete arbitrary Serena data, or add a
second global Serena instance. Use the bounded maintenance operation with an
operator-issued approval identifier:

```powershell
python D:\github\agentcore-control-plane\scripts\agentcore_cursor\serena_maintenance.py repair --capability authority_maintainer --approval-id AUTH-2026-07-26-SERENA-REPAIR --dry-run
python D:\github\agentcore-control-plane\scripts\agentcore_cursor\serena_maintenance.py repair --capability authority_maintainer --approval-id AUTH-2026-07-26-SERENA-REPAIR
```

The maintenance command is limited to the global Serena registry, the two
control-plane project files, and the single Cursor foundation rule. It creates a
rollback copy under
`E:\AgentCore-Backups\agentcore-control-plane\` before writing and validates
the resulting YAML/schema. Stage B allows only the exact approved command shape.

### Cursor global foundation rule

The live Cursor foundation rule is the existing single file:

`C:\Users\ynotf\.cursor\rules\agentcore-foundation.mdc`

Install the current generated rule through the bounded maintenance operation.
This replaces that one rule; do not add a second always-on foundation rule:

```powershell
python D:\github\agentcore-control-plane\scripts\agentcore_cursor\serena_maintenance.py install_cursor_rule --capability authority_maintainer --approval-id AUTH-2026-07-26-SERENA-RULE
```

The installer backs up the live file, derives content from
`D:\github\agentcore-control-plane\ide-profiles\cursor\GLOBAL_RULES.md`, validates
the frontmatter and policy revision, and records a manifest. Fully restart
Cursor after installation so the global rule is reloaded.

### Serena diagnostics

Run:

```powershell
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Test-AgentCoreBifrostGateway.ps1
python D:\github\agentcore-control-plane\scripts\bifrost\validate_contracts.py
```

Then verify:

1. Bifrost `/health` is healthy; normal gateway profiles must not list Serena.
2. If Serena is explicitly launched by a governed project-local host, bind that
   process directly to the exact repository root and run a safe semantic query.
3. Reject Swarm-owned roots for normal AgentCore continuity; an optional
   read-only boundary audit must not persist Swarm work into AgentCore memory.
4. Check the project-local Serena log for a clean startup and absence of
   `KeyError: 'languages'`, fatal exceptions, and uncontrolled restart loops.

Do not use the machine-global project-router state as a concurrent-session
boundary and do not re-enable the dormant shared Bifrost Serena client merely
to satisfy a tool-discovery check.

## Validation and acceptance

Source/config validation:

```powershell
node --check D:\github\agentcore-control-plane\ops\bifrost\wrappers\serena-prewarm.js
python D:\github\agentcore-control-plane\scripts\bifrost\validate_contracts.py
python -m unittest D:\github\agentcore-control-plane\scripts\agentcore_cursor\test_serena_maintenance.py -v
python D:\github\agentcore-control-plane\scripts\agentcore_cursor\test_hook_protocol.py --iterations 10
python D:\github\agentcore-control-plane\scripts\render_ide_rules.py --check
```

Semantic acceptance requires:

- AgentCore: a safe `get_symbols_overview` or `find_symbol` query in
  `D:\github\agentcore-control-plane`.
- Optional boundary-audit only: a read-only semantic query in
  `D:\github\swarm-ecosystem-control` that must not open AgentCore memory
  continuity or treat Swarm as an AgentCore-managed project.

Native IDE acceptance additionally proves the IDE itself can:

- see the gateway after restart;
- keep machine-global project-router mutation absent from ordinary profiles;
- refuse Swarm-owned selection in any governed project-local Serena launch;
- use native semantic/source tooling by default and treat Serena as an optional
  explicit-project local process, never a shared implicit-project dependency;
- keep Git and writes scoped to the active AgentCore / enrolled non-Swarm
  repository;
- preserve the AgentCore memory lifecycle on allowed projects only;
- switch among allowed projects without cross-project semantic or memory leakage.

The current repair evidence is:

`D:\github\agentcore-control-plane\audits\cursor-context\SERENA_DUAL_CONTROL_PLANE_REPAIR_20260726.md`

## Change-control rules

- Do not add a shared global Serena MCP entry to IDE configuration.
- Do not create a machine-global Serena process for unrelated projects; any
  accepted launch is project-owned and explicitly rooted.
- Do not make the combined workspace a third authority.
- Do not add Swarm runtime dependencies to AgentCore or AgentCore runtime
  dependencies to Swarm.
- Do not expose raw database credentials or whole-drive filesystem roots.
- Keep the Bifrost registry, wrapper, project router, policy, renderings, and
  validators aligned.
- After changing this document or the canonical policy, regenerate derived IDE
  rules, run validators, perform a secret/junk scan, and record the result in
  AgentCore memory.
