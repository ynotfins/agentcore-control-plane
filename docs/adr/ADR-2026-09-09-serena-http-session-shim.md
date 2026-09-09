# ADR-2026-09-09 — Serena Multi-IDE Concurrency via HTTP Session-Shim

**Status:** Accepted  
**Date:** 2026-09-09  
**Authority:** `contracts/bifrost-upstream-mcp-registry.json`, `contracts/agentcore-project-enrollment.json`, `SERENA.md`, `GATEWAY_AND_BIFROST_DEVELOPER_GUIDE.md`

## Context

Bifrost v2.0.0 aggregates developer MCP tools for all enrolled IDEs under a single endpoint: `http://127.0.0.1:8080/mcp`. Serena (`v1.5.4.dev0`) provides deep semantic code intelligence (LSP-backed symbol navigation, reference discovery, file diagnostics, and structural code refactoring).

To operate correctly, Serena requires an explicit project path (`--project <path>`) at startup.

Under Bifrost's architecture:
1. **STDIO connections are sticky and process-static:** In Bifrost, `stdio_config` supports only `command`, `args`, and `envs`. It has no `working_directory` configuration and no mechanism to vary working directory or startup flags per request turn.
2. **STDIO lacks per-request headers:** Dynamic caller metadata (`allowed_extra_headers`, per-user credentials) exists only for HTTP and SSE connections.
3. **Machine-global `active-project.json` fails multi-IDE concurrency:** The prior shared Serena wrapper (`ops/bifrost/wrappers/serena-prewarm.js`) inspected a single machine-global file (`active-project.json`). When multiple IDEs or autonomous agents work concurrently across different repositories (e.g., Cursor working on `agentcore-control-plane` while Devin or Zed works on `agentcore-context-engine` or `nfa-platform`), a single shared process either re-binds to the wrong repository or serves stale symbol cache, causing severe cross-project symbol leakage and race conditions.

Because of this limitation, Serena was classified as `dormant_project_scoped` in the Bifrost registry and forbidden from shared gateway enablement.

## Decision

1. **Deploy an AgentCore HTTP Session-Shim (`scripts/bifrost/serena_session_shim.py`):**
   - The shim runs as a lightweight loopback HTTP MCP server on `http://127.0.0.1:18090/mcp`.
   - Bifrost connects to Serena as an HTTP MCP client:
     ```json
     {
       "name": "serena",
       "connection_type": "http",
       "connection_string": "http://127.0.0.1:18090/mcp",
       "auth_type": "none",
       "is_code_mode_client": true,
       "allowed_extra_headers": ["x-agentcore-project", "x-bf-session-id", "x-session-id", "x-bf-vk"]
     }
     ```
2. **Session & Project Identity Resolution:**
   - On incoming MCP JSON-RPC requests, the shim resolves project identity from:
     * Request headers: `x-agentcore-project`, `x-bf-session-id`, `x-session-id`, `x-bf-vk` (forwarded by Bifrost via `allowed_extra_headers`).
     * Session-to-project registry maintained by the shim (`/session/bind` for enrolled keys only).
     * Absolute enrolled candidate paths in tool arguments when present.
   - Shared resolver: `scripts/bifrost/session_identity.py` (`EnrollmentRegistry`).
   - **Default-deny:** Missing headers, unknown `project_key`, or unenrolled path returns `PROJECT_NOT_ENROLLED`. The shim **never** falls back to `agentcore-control-plane` or any other enrolled default.
3. **Strict Enrollment Boundary & Swarm Exclusion:**
   - Every resolved target is validated against `contracts/agentcore-project-enrollment.json`:
     * Default-deny: Any path or key not present in `contracts/agentcore-project-enrollment.json` is rejected with `PROJECT_NOT_ENROLLED`.
     * Swarm exclusion: Any path matching `foreign_roots` or `foreign_markers` (e.g. `swarm-ecosystem-control`, `SwarmRecall`, `H:\SwarmData`) is rejected with `swarm_project_refused`.
4. **Isolated Subprocess Routing:**
   - The shim manages a pool of isolated Serena child processes keyed by `project_key`.
   - When a tool call arrives for an enrolled project, the shim dispatches it to that project's dedicated Serena child process:
     `serena start-mcp-server --transport stdio --context ide --project <enrolled_path>`.
   - Two concurrent sessions targeting different enrolled projects run against physically distinct Serena subprocesses with separate language servers, separate caches, and separate working directories.
5. **Ping & Lifecycle Handling:**
   - The shim intercepts `ping` requests and immediately returns `{"jsonrpc": "2.0", "id": id, "result": {}}`, eliminating ping timeouts.
   - Child processes are gracefully stopped on shutdown.
6. **Code Mode Surface Placement:**
   - Serena exposes 21 tool definitions. To prevent eager context bloat, Serena is admitted with `is_code_mode_client: true`.
   - Serena tools are discovered via `listToolFiles` -> `servers/serena.pyi` and executed via `executeToolCode`.

## Consequences

- **Concurrent Multi-IDE Safety:** Different IDEs can call Serena simultaneously through the single Bifrost gateway without cross-project symbol or file collisions.
- **Context Protection:** Serena's 21 tool schemas remain in Code Mode VFS, saving ~4,500 tokens of eager context on every turn.
- **Contract Adherence:** No machine-global `active-project.json` is used as a security boundary.
- **Sticky STDIO Forbidden:** The rule remains absolute: Serena must never be enabled on shared sticky STDIO.
