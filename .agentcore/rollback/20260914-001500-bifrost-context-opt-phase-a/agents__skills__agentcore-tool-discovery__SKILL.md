---
name: agentcore-tool-discovery
description: Use when a task asks what tools are available, requests tool inventory or discovery, or may depend on hidden Bifrost Code Mode capabilities.
---

# AgentCore Tool Discovery

Discover capabilities without treating visibility as authorization. This skill is read-only guidance: do not mutate routers, listeners, configs, leases, or execute workload tools.

## Discovery lifecycle

1. At session or task start, call `listToolFiles`; use `tools/list` only when Code Mode is unavailable. Retain compact server/tool names only, not full schemas.
2. For an authorized later operation, use `listToolFiles` -> `readToolFile` for the smallest relevant stub -> optional `getToolDocs` when the signature is insufficient -> `executeToolCode`. Discovery itself stops before `executeToolCode`.
3. Refresh inventory at Milestone entry or a reported registry change. At exit, record tools actually used and release or let JIT leases expire. Do not unconditionally reload the catalog.

## Routing map

| Capability | When to use |
| --- | --- |
| `agentcore-memory` | Enrolled-project startup, recovery, evidence, handoff, and close; gateway only. |
| `sequential-thinking` | Architecture, migration, recovery, concurrency, major refactor, or cross-system decisions. |
| Serena | Symbol/reference-sensitive work when native source tools are insufficient; exact project-owned process only. |
| Depwire | Before and after structural dependency changes; exact project cwd. |
| Tentra | Milestone-required architecture or code-graph evidence; explicit project root. |
| Filesystem | Only when Bifrost reports it and scopes it to the exact enrolled project. Never assume a drive, whole-drive root, or home/profile root. |
| GitHub | Remote code search, issues, PRs, reviews, or provenance; read by default. |
| Playwright | Reproducible browser, UI, or E2E acceptance. |
| Morph | External GitHub patterns, precise repository search, or an approved surgical edit; never architecture authority. |
| PostgreSQL / SQLite | Approved database semantics through a governed read-only facade with exact DB/file identity; writes stay in the owning migration workflow outside MCP. |
| Shadcn | Candidate for shadcn/ui component and registry work. |
| PostHog | Candidate for project analytics, flags, experiments, or observability. |
| Fetch | Candidate for bounded allowlisted HTTP reads. |
| wcgw | Candidate for scoped shell/computer operations when no native equivalent exists. |
| Docker | Candidate for owning-project container build, logs, health, or lifecycle. |
| Ref | Candidate for admitted reference results unavailable from primary docs routes. |
| AgentMail | Candidate for agent-owned mailbox, draft, thread, or attachment work. |

Candidates are not installed or available until current Bifrost inventory and admission evidence prove them.

## Hard boundaries

A direct MCP exception requires a proven Bifrost parity gap and rollback evidence. Never duplicate memory, database, Recall, or other Swarm routes.

Do not access `D:\github\nfa-platform` or its alerts database unless a future, separate task explicitly authorizes that exact access.
