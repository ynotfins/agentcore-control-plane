# Development-Chat Archive Manifest

**Purpose:** Integrity and precedence record for the archived ChatGPT AgentCore development conversation.  
**Class:** Historical evidence only — never architecture authority.  
**Created:** 2026-07-20  
**Reconstruction:** `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md`

---

## Precedence (hard rule)

```text
chat evidence
  < contracts / validators / runtime probes
  < CONTEXT_BLOCK.md §0a
  < BLUEPRINT.md
  < PROJECT_ANCHOR.md
```

Do not treat assistant recommendations, Cursor completion reports, or chat-final status strings as adopted truth until Git, audits, or live probes corroborate them. Do not infer redacted plugin output.

---

## Inventory

| File | Role | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `chatgpt-chat-agentcore-control-plane.md` | Full exported ChatGPT conversation | 1032252 | `8DAD4B1EA00FB2415A88CA75F107D00E502B2305D9D3E691728310AEB760671F` |
| `BLUEPRINT-yesterday.md` | Archived BLUEPRINT snapshot sibling | 31072 | (see `Get-FileHash` if re-verified) |
| `../BLUEPRINT-2026-07-19.md` | Same-era BLUEPRINT archive outside this folder | 31072 | (see `Get-FileHash` if re-verified) |
| `MANIFEST.md` | This file | — | — |

**Duplicates:** No second copy of the ChatGPT export elsewhere in the repository (search `*chatgpt-chat*`).

---

## Primary export integrity

| Field | Value |
| --- | --- |
| Path | `docs/operations/archive/development-chat/chatgpt-chat-agentcore-control-plane.md` |
| Content lines | 31877 |
| Null bytes | 0 |
| Binary corruption markers | None found |
| Redacted plugin lines | 590 (`The output of this plugin was redacted.`) |
| Speaker headings | `## You` ≈ 642; `## ChatGPT` ≈ 111 |
| First meaningful heading | `# Branch … memory-context-database` |
| Last meaningful headings | `## Accurate completion status` / dormant-catalog next steps |
| Detectable date span | ~2026-07-12 through OpenRouter dormant registration era (~ commit `96c2528`) |
| Ends before | HEAD docs reconcile `794d972` and OAuth-bind claim `f843b97` |

---

## Secret-pattern scan (2026-07-20)

Report categories only — **no secret values**.

| Category | Count | Notes |
| --- | --- | --- |
| Literal bearer / `sk-` / `or-v1-` tokens | 0 | — |
| Password assignments | 0 | — |
| Postgres connection strings with credentials | 0 | — |
| API key assignments with literals | 0 | — |
| Environment-variable **names** / placeholders | 39 | Names only (e.g. `BIFROST_MCP_VIRTUAL_KEY`); not literal values |

**Critical security finding:** None (no probable literal secrets in scan categories above).

---

## Coverage record (reconstruction pass)

The reconstruction agent did **not** claim a full line-by-line read of all 31877 lines.

| Method | Coverage |
| --- | --- |
| Integrity | Full file hash, size, null-byte check |
| Structure | Heading samples, speaker counts, first/last sections |
| Marker index | Counts for Bifrost, Portkey, UTCP, PG16/18, M0–M8, OpenRouter, JIT, Deep Agents, Swarm*, commit SHAs, etc. |
| Detailed samples | ≈ L1–120; L1480–2200 (UTCP/Portkey reject); L5325+; L8360–8450; L12200–13700 (JIT); L24700–26500 (M3.002); L25900 (`a843cf1`); L28800–28950 (`fc3fb16`); L29000–31877 (OpenRouter end) |

---

## Notable superseded chat claims

| Chat claim (end of export) | Current authority |
| --- | --- |
| OpenRouter OAuth pending / Authenticated: no | Lifecycle `authenticated_dormant`; claim `OPENROUTER MCP AVAILABLE THROUGH AGENTCORE-GATEWAY` (`docs/operations/OPENROUTER_MCP.md`, audit 2026-07-20) |
| Broader dormant MCP catalog incomplete | Still accurate as a catalog implementation backlog (`docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md`) |
| Handoff still at HEAD `a843cf1` | Point-in-time; main advanced through OpenRouter/JIT/docs reconcile |

---

## Claim classification guide (for future readers)

When citing this chat, label each significant claim as one of:

- user goal
- tentative proposal
- assistant recommendation
- operator decision
- implementation authorization
- Cursor-reported completion
- Git-corroborated implementation
- runtime-corroborated implementation
- superseded
- unresolved
