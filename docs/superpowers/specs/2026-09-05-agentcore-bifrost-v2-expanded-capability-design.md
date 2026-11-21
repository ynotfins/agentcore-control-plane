# AgentCore Bifrost v2 Expanded Capability Design

**Approval:** `AUTH-2026-09-05-UNIVERSAL-IDE-BIFROST-SKILLS-ALIGNMENT`
**Status:** Approved design input; non-authoritative planning artifact
**Authority:** `PROJECT_ANCHOR.md` -> `DOC_AUTHORITY.md` -> `BLUEPRINT.md` -> `CONTEXT_BLOCK.md` -> current contracts

## Goal

Make Bifrost v2.0.0 the reliable AgentCore MCP and optional inference gateway for every supported non-Swarm IDE and autonomous runtime on this PC, while maximizing useful tool availability without loading large tool schemas into every model turn.

## Hard Boundaries

- Do not modify `D:\github\nfa-platform`, its live client configuration, its alerts database, database roles, migrations, containers, services, or credentials during this rollout.
- SwarmClaw, SwarmRecall, and SwarmVault remain outside AgentCore execution authority.
- OpenClaw is AgentCore-owned under this approval and should use `agentcore-gateway`.
- A future Swarm-to-OpenClaw adapter may use only its documented protocol. It receives no AgentCore virtual key, AgentCore memory session, AgentCore database credential, Recall credential, or AgentCore write root.
- IDEs receive no raw PostgreSQL, SQLite, Recall, or other database credentials.
- Bifrost remains loopback-only. No public tunnel or broad network bind is introduced.
- Existing dirty-worktree changes are preserved and excluded from task commits.

## Capability Model

All healthy, approved, non-destructive tools should be discoverable to builder-class agents. Availability and context exposure are separate:

- Small, frequently used servers remain classic MCP tools.
- Heavy servers use Bifrost Code Mode and are discovered through `listToolFiles`, `readToolFile`, optional `getToolDocs`, and `executeToolCode`.
- Every admitted MCP server has a named per-tool allowlist. Destructive, administrative, secret-bearing, deploy, write-anywhere, cross-project, or Swarm tools are denied or require an expiring JIT/operator lease.
- Project-scoped tools that cannot receive trustworthy project identity through Bifrost use explicit project-owned local processes or exact-cwd CLIs.
- Direct installation is an exception. It requires a host-native smoke test proving a necessary capability or material performance characteristic is lost through Bifrost, plus rollback evidence and no duplicate memory or database route.

The `agentcore-tool-discovery` skill is read-only discovery guidance. It creates no listener, intercepts no traffic, mutates no configuration, selects no provider route, and executes no tool. Bifrost remains the sole MCP routing authority.

## Required Tool Routing

| Capability | Required use | Default boundary |
| --- | --- | --- |
| AgentCore memory | Session start, recovery, accepted evidence, handoff, clean close | `agentcore-gateway` only; no raw SQL or Recall |
| Sequential Thinking | Architecture, migration, recovery, concurrency, major refactor, cross-system decisions | Classic, non-destructive |
| Serena | Symbol/reference-sensitive edits when native source tools are insufficient | Exact project-owned process; no shared implicit project |
| Depwire | Before and after structural dependency changes | Exact project cwd |
| Tentra | Milestone-required architecture/code graph evidence | Explicit project root |
| Filesystem | Bounded project files only | No whole-drive/home roots |
| GitHub | Repository discovery, issues, PRs, and source operations | Read by default; mutation requires task scope |
| Playwright | Browser, UI, and end-to-end acceptance | Code Mode; unsafe code and unrestricted uploads denied |
| Database tools | Schema/status/query work only when explicitly required | Governed read-only facade for normal IDEs; all writes stay in the owning migration workflow; no NFA access in this rollout |
| Morph | External GitHub/source patterns, precise search, surgical approved edits | Read tools broad; edits bounded to approved paths |

## MCP Admission Set

Already registered: Serena, Sequential Thinking, Tentra, Depwire, Filesystem, GitHub MCP, and Playwright.

Admission candidates: Shadcn, PostHog, Fetch, wcgw, Docker, PostgreSQL, SQLite, Ref, and AgentMail. Each candidate must resolve to an exact official package or repository, version pin, license, transport, authentication method, storage boundary, complete tool inventory, health probe, Code Mode decision, safe allowlist, denied list, and rollback path before activation. An unresolved candidate is `catalogued_unverified`, not installed.

## Skills

The Bifrost Skills Repository remains the central versioned source for approved AgentCore skills. The initial governed set is:

- `agentcore-project-lifecycle`
- `agentcore-tool-discovery`
- `morph-source-workflows`
- `zoo-roo-code-workflows`
- `nia`
- `langfuse`

Skill-aware hosts install versioned skills. Other hosts receive generated rules or a documented runtime adapter. Installation never upgrades a host beyond its proven certification state.

Zoo Code/Roo Code is a VS Code-family client extension, not a Bifrost upstream MCP server. Install it directly only in compatible extension hosts. Other hosts receive the workflow skill/rules and the same Bifrost tool capabilities where supported.

## Host Scope

Managed candidates: Cursor, Codex, Devin, Eigent, Zed, MiniMax Code/Mavis, Reasonix, OpenCode, Open Design, AutoGPT, Agent Orchestrator, Cherry Studio, LobeHub, OpenHands, Antigravity, Zcode, Open Interpreter, and OpenClaw.

Certification states are exactly:

- `source_ready`
- `installed_unverified`
- `configured_restart_required`
- `live_validated`
- `manual_import_pending`
- `UI_only_pending`
- `unsupported_with_reason`

## Process Lasso

Keep Process Governor and ProBalance. Disable SmartTrim working-set trimming and standby-cache purging because current 40% activation repeatedly discards useful cache while the machine still has substantial available RAM. Preserve unrelated Process Lasso settings and use exact executable, path, parent, or command-line rules. Do not boost generic `node.exe`, `python.exe`, Docker, WSL, or `vmmemWSL`.

Observe committed memory, hard faults, and operator-visible stalls for 24 hours. Roll back if committed memory exceeds 85%, paging or stalls worsen, or priority applications regress.

## Bifrost v2 Features

Keep the proven semantic cache and MCP Code Mode. Prioritize:

1. Exact virtual-key MCP allowlists and per-tool filtering.
2. Skills Repository versioning and host installation.
3. Prompt Repository for governed setup and worker prompts.
4. Built-in observability, bounded retention, error classification, and provider latency/cost evidence.
5. Retries and provider fallbacks.
6. Model limits, budgets, and required headers.
7. Complexity routing and routing rules after inference canaries.
8. Async inference and signed webhooks only for workflows that benefit from durable asynchronous completion.

Inference canaries use one non-NFA client, explicit manual requests or at most 5% eligible traffic, and 24 hours of observation. Acceptance requires zero authentication failures, correct provider/model selection, cost within the virtual-key budget, no data leakage, and no material p95 latency regression. Roll back immediately for wrong routing, leakage, authentication errors, or p95 latency degradation above 20%.

## Acceptance

Completion requires exact-version docs proof, contract and renderer tests, host-profile parity, secret scans, gateway/watchdog restart recovery, safe tool canaries, skill publication/install evidence, Process Lasso persistence evidence, and independent protected-document plus code/contract review. No host is called `live_validated` from configuration presence alone.
