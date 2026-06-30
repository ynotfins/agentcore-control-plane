# SwarmVault Schema — AgentCore Control Plane

**Vault root:** `F:\AgentCore\agentmemory\swarmvault`  
**Purpose:** Local-first RAG, wiki, knowledge graph, context packs, and task ledger for the AgentCore control-plane and Swarm ecosystem repos on CHAOSCENTRAL.

---

## Vault Purpose

This vault covers the AgentCore automation control plane and its governed Swarm ecosystem:

- MCP server governance (renderers, contracts, supervisor model, validators)
- Local-only memory architecture (PostgreSQL `agent_core`, SwarmRecall, SwarmVault, projector pipeline)
- Swarm repo integration (SwarmRecall, SwarmVault, SwarmClaw, SwarmRelay, SwarmFeed, SwarmDock)
- Managed IDE baseline rollout (Cursor, Codex, OpenClaw, Open Interpreter, MiniMax, Mavis, Antigravity, Claude Code)
- Security/incident evidence and rollout artifacts from `D:\github\agentcore-control-plane`

**Intended audience:** Agents and operators working on this control plane who need source-grounded context without pulling entire repos into the prompt.

**Questions this vault should answer well:**
- What does the current MCP baseline look like for each managed IDE?
- What is the governed memory write pipeline?
- What are the current acceptance validator results?
- What rollout phases are complete, pending, or blocked?
- What are the key runtime facts (ports, paths, env vars, roles)?

---

## Naming Conventions

- Use stable, descriptive page titles that reflect the component or decision being documented.
- Prefer names like `SwarmRecall Local Runtime`, `Validator Acceptance State`, `IDE Cleanup Prompts`, `Memory Projection Pipeline`.
- Avoid date-stamped titles for concept pages; use them only for dated evidence/snapshot pages.

---

## Page Structure Rules

- **Source pages** must stay grounded in the original material (repo files, validator output, runtime evidence). Do not paraphrase away key constraints.
- **Concept pages** must aggregate source-backed claims. Cite the source file or validator by path when stating a fact.
- Preserve contradictions between documents rather than smoothing them away — the contradiction is often the important signal.
- Tag pages that describe a superseded state as historical.

---

## Categories

- `mcp-governance` — server contracts, renderers, supervisor model, validator state
- `memory-architecture` — gateway tools, projector pipeline, agent_core schema, SwarmRecall, SwarmVault
- `rollout-state` — phase completion, acceptance evidence, blockers
- `security` — incident reconciliation, secret hygiene, LAN exposure, live config drift
- `ide-baseline` — per-IDE MCP config state, cleanup prompts, adoption status
- `runtime-facts` — ports, paths, drive roles, env var names, Postgres roles

---

## Relationship Types

- Mentions
- Supports
- Contradicts
- Depends on
- Supersedes

---

## Grounding Rules

- Prefer raw source files and validator output over agent summaries.
- Cite source path (e.g. `contracts/master-mcp-server-config.json`, `ops/Test-AgentCoreSwarmRecall.ps1`) when making factual claims.
- Do not treat the wiki as a source of truth when the raw repo material disagrees.
- When a validator result and a doc disagree, prefer the validator result.

---

## Exclusions

The compiler must **not** generate or include:

- Raw secret values (API keys, bearer tokens, passwords, private keys, connection strings with credentials)
- Live IDE config file content from `C:\Users\ynotf\.*`
- Runtime database dumps or raw Postgres rows
- `F:\AgentCore` filesystem state (database cluster files, meilisearch raw data, projection-state binary files)
- Contents of `D:\Autonomy\secrets-backups\`
- Docker volume contents
- Content that has not been approved for the `agent_core` write path
- node_modules, .next, dist, build, coverage, or generated cache directories from vendor repos
