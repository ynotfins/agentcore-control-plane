# Bifrost Tool Surface Matrix & Classification Audit (2026-09-09)

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`, `contracts/agentcore-gateway-client.json`, `contracts/agentcore-project-enrollment.json`  
**Execution Environment:** Windows 10 x64, Bifrost v2.0.0 (`F:\AgentCore\runtime\bifrost`), PostgreSQL 18 (`127.0.0.1:55433`), Node.js, Python 3.13  
**Base Branch:** `setup/zoo-code-qdrant-nfa-20260820`  
**Primary Owner:** Cursor is sole primary owner of the Bifrost MCP contract plane (`AGENTS.md` 2026-09-08); Codex is independent reviewer / challenge only.

---

## 1. Executive Summary & Live Evidence

Bifrost aggregates all AgentCore developer tools behind a single IDE endpoint: `agentcore-gateway`. To prevent LLM context-window degradation from eager tool schema loading, the tool surface is partitioned into two distinct execution tiers:

1. **Classic / Always-Discoverable (Eager `tools/list`):**
   - High-frequency, compact foundation tools (memory, planning, documentation, subagents, capability discovery).
   - Eager tool count is bounded: currently 48 eager tools in the builder profile across 9 classic servers.
2. **Code Mode (Lazy VFS Meta-Tools):**
   - Large-catalog, heavy execution tools discovered via `listToolFiles` -> `readToolFile` -> `getToolDocs` -> `executeToolCode`.
   - Current global virtual filesystem binding level: `code_mode_binding_level = tool`.
   - **Live `listToolFiles` verified inventory (2026-09-09 Cursor session, post Phase 0–3 work):**
     * `servers/apify_research.pyi`
     * `servers/exa_research.pyi`
     * `servers/firecrawl_research.pyi`
     * `servers/morph_mcp.pyi`
     * `servers/playwright.pyi`
     * `servers/tavily_research.pyi`
   - **Honesty note:** Registry/renderers also flag `mcp_prompt_optimizer`, `openrouter` (JIT), and `serena` (HTTP shim `:18090`) as Code Mode clients. This Cursor session still hydrates `mcp_prompt_optimizer` as eager dynamic tools; `openrouter` and `serena` were **absent** from live `listToolFiles` until the Serena shim is running and Bifrost reconnects. Do not claim VFS parity from registry flags alone.
   - Code Mode saves heavy schemas from entering eager LLM context on every conversation turn when the VFS path is actually hydrated.

---

## 2. Complete 40-Server Registry Audit & Surface Mapping

Source of truth: `contracts/bifrost-upstream-mcp-registry.json` (40 upstream entries).

| # | Canonical ID | In Registry? | Enabled? | Registry Status | Code Mode Client? | Tool Count | Target Surface Bucket | Context-Bloat Control Rationale | Admission / Activation Gaps |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `agentcore-capability-catalog` | Yes | Yes | `active` | No (`false`) | 2 | **Classic Active** | 2 tools; lightweight metadata for capability elevation discovery. | Admitted; healthy. |
| 2 | `arabold-docs` | Yes | Yes | `active` | No (`false`) | 10 | **Classic Active** | Primary machine-global docs store; agents must have eager access for library lookups. | Admitted; healthy. |
| 3 | `serena` | Yes | Yes (registry) | `active` (HTTP shim) | Yes (`true`) | 21 | **Phase 3 Code Mode via HTTP Shim** | 21 symbol tools; STDIO sticky retired. | Default-deny identity fixed 2026-09-09 (`session_identity.py`); live VFS needs shim process + Bifrost reconnect. |
| 4 | `sequential-thinking` | Yes | Yes | `active` | No (`false`) | 1 | **Classic Active** | 1 tool; foundation planning mechanism required by operating rules. | Admitted; healthy. |
| 5 | `cursor-agent-mcp` | Yes | Yes | `active` | No (`false`) | 8 | **Classic Active** | 8 tools; Cursor subagent orchestration controls. | Admitted; healthy. |
| 6 | `mcp-prompt-optimizer` | Yes | Yes | `active` | Yes (`true`) | 7 | **Code Mode Active** | 7 prompt analysis/optimization tools; heavy JSON schemas, executed on demand. | Admitted; Code Mode enabled 2026-09-08. |
| 7 | `context-fabric` | Yes | No | `dormant_project_scoped` | No (`false`) | 4 | **Dormant Project-Scoped (Phase 3b Sibling)** | Git continuity tools; lacks caller project identity on shared gateway. | Needs session-identity adapter or explicit repo hook. |
| 8 | `mcp-debugger` | Yes | No | `disabled` | No (`false`) | 1 | **Disabled** | Debugger attach capability; security-restricted. | Explicit operator enablement only. |
| 9 | `depwire` | Yes | No | `dormant_project_scoped` | No (`false`) | 6 | **Dormant Project-Scoped (Phase 3b Sibling)** | Pattern A host-owned CLI preferred (`depwire mcp`); lacks caller cwd. | Blocked on cwd injection or host-owned local tool. |
| 10 | `depwire-cloud` | Yes | No | `disabled` | No (`false`) | 3 | **Deferred / Disabled** | Hosted cloud graph queries; remote service dependency. | Cloud API key and connection health check. |
| 11 | `tentra` | Yes | No | `dormant_project_scoped` | No (`false`) | 5 | **Dormant Project-Scoped (Phase 3b Sibling)** | Project knowledge index; local runtime data under AgentRuntime. | Blocked on cwd/project injection. |
| 12 | `obsidian-vault` | Yes | No | `disabled` | No (`false`) | 4 | **Disabled** | Human-readable durable notes; local wrapper. | Explicit operator activation only. |
| 13 | `playwright` | Yes | Yes | `active` | Yes (`true`) | 24 | **Code Mode Active** | 24 browser automation tools; massive schemas would overwhelm eager context. | Admitted; Code Mode live. |
| 14 | `filesystem` | Yes | No | `dormant_project_scoped` | No (`false`) | 14 | **Dormant Project-Scoped (Phase 3b Sibling)** | Raw filesystem tool; must never be global root; requires enrolled project root binding. | Blocked on session cwd binding (Phase 3b). |
| 15 | `github-mcp` | Yes | No | `deferred` | Yes (`true`) | 26 (est) | **Code Mode Preflagged (Deferred)** | 26+ GitHub tools. Heavy; must be Code Mode when admitted. | Transitional wildcard `["*"]` must be replaced with named inventory; Docker container health gate. |
| 16 | `agentcore-memory` | Yes | Yes | `active` | No (`false`) | 10 | **Classic Active** | 10-tool canonical memory facade; required on every turn for session recovery. | Admitted; healthy. |
| 17 | `openrouter` | Yes | Yes | `authenticated_dormant` | Yes (`true`) | 13 | **Code Mode Active (JIT Leased)** | Model catalog and account tools; zero default exposure; JIT lease activation. | OAuth bound in Bifrost store; M6 lease required for discovery. |
| 18 | `agentcore-project-router` | Yes | Yes | `active` | No (`false`) | 4 | **Classic Active (Operator Only)** | 4 tools; administrative project activation; not for general agent continuity. | Admitted; restricted to operator profile. |
| 19 | `skills-hub` | Yes | Yes | `active` | No (`false`) | 3 | **Classic Active** | 3 tools; dynamic skill metadata inspection (`install_skill` denied). | Admitted; healthy. |
| 20 | `firebase-mcp` | Yes | No | `dormant_project_scoped` | No (`false`) | 8 | **Dormant Project-Scoped** | Firebase Auth/Firestore tools; project-bound. | Dedicated project credentials; operator approval. |
| 21 | `google-sheets-mcp` | Yes | No | `preview` | No (`false`) | 5 | **Preview / Deferred** | Google Sheets API; write-capable external SaaS. | Google Cloud OAuth 2.0 token; operator approval. |
| 22 | `clasp-mcp` | Yes | No | `quarantine` | No (`false`) | 6 | **Quarantine** | Unbounded filesystem path access in upstream tools. | Architecture flaw: accepts unconstrained paths outside worktree. |
| 23 | `pipedream-google-sheets` | Yes | No | `candidate_pending_oauth` | No (`false`) | 4 | **Candidate Pending OAuth** | Alternative Sheets integration via Pipedream v2. | Pipedream OAuth connection flow. |
| 24 | `morph-mcp` | Yes | Yes | `active` | Yes (`true`) | 7 | **Code Mode Active** | 7 Fast Apply, search, and Reflex tools; large response payloads. | Admitted; Code Mode live. |
| 25 | `apify-research` | Yes | Yes | `active` | Yes (`true`) | 5 | **Code Mode Active** | 5 Actor discovery and execution tools. | Admitted; Code Mode live. |
| 26 | `exa-research` | Yes | Yes | `active` | Yes (`true`) | 2 | **Code Mode Active** | 2 Exa neural search tools. | Admitted; Code Mode live. |
| 27 | `firecrawl-research` | Yes | Yes | `active` | Yes (`true`) | 8 | **Code Mode Active** | 8 web crawling and paper search tools. | Admitted; Code Mode live. |
| 28 | `tavily-research` | Yes | Yes | `active` | Yes (`true`) | 5 | **Code Mode Active** | 5 search/crawl/map/research tools. | Admitted; Code Mode live. |
| 29 | `brightdata-research` | Yes | No | `catalogued_unverified` | Yes (`true`) | 4 | **Catalogued Unverified** | Web scraping; startup side-effects create provider zones. | Unverified startup behavior; billing risk. |
| 30 | `context7` | Yes | Yes | `active` | No (`false`) | 2 | **Classic Active** | 2 tools; same-turn public doc bridge while Arabold scrape runs. | Admitted; healthy. |
| 31 | `nia` | Yes | Yes | `active` | No (`false`) | 12 | **Classic Active** | 12 search and codebase exploration tools. | Admitted; healthy. |
| 32 | `shadcn` | Yes | No | `catalogued_unverified` | No (`false`) | 3 | **Catalogued Unverified** | UI component discovery and installation. | Missing official pin and project scope validation. |
| 33 | `posthog` | Yes | No | `catalogued_unverified` | No (`false`) | 5 | **Catalogued Unverified** | Analytics and product telemetry MCP. | Remote OAuth/API key unconfigured. |
| 34 | `agentmail` | Yes | No | `candidate_unverified` | No (`false`) | 6 | **Candidate Unverified** | Agent email sending/receiving. | Tier-4 external communications risk; operator approval required. |
| 35 | `fetch-mcp` | Yes | No | `rejected` | No (`false`) | 0 | **Rejected** | Generic network fetch; high SSRF risk; redundant with Arabold/Tavily/Exa. | Architectural rejection: unconstrained network egress. |
| 36 | `wcgw` | Yes | No | `rejected` | No (`false`) | 0 | **Rejected** | Unrestricted shell and WSL execution; violates Stage B security. | Architectural rejection: security boundary bypass. |
| 37 | `docker-mcp-toolkit` | Yes | No | `rejected` | No (`false`) | 0 | **Rejected** | Second MCP aggregator; conflicts with Bifrost gateway ownership. | Architectural rejection: dual-aggregator collision. |
| 38 | `postgresql-mcp` | Yes | No | `rejected` | No (`false`) | 0 | **Rejected** | Raw SQL queries; violates database contract; bypasses `agentcore-memory` facade. | Architectural rejection: direct database access forbidden. |
| 39 | `sqlite-mcp` | Yes | No | `rejected` | No (`false`) | 0 | **Rejected** | Raw SQLite queries; unresolved paths and schema mutation risk. | Architectural rejection: direct database access forbidden. |
| 40 | `ref-mcp` | Yes | No | `rejected` | No (`false`) | 0 | **Rejected** | Redundant remote documentation provider; Arabold is local authority. | Architectural rejection: redundant remote documentation. |

---

## 3. Operator Wishlist Classification & Placement

| Wishlist Candidate | Canonical ID / Identity | Current Registry Status | Target Surface Bucket | Bloat Control / Architectural Placement | Admission Gaps & Requirements |
|---|---|---|---|---|---|
| **sequential-thinking** | `sequential-thinking` | Active (`enabled=true`) | **Classic Active** | 1 tool; essential reasoning engine; keep eager. | Admitted; PASS. |
| **arabold-docs** | `arabold-docs` | Active (`enabled=true`) | **Classic Active** | 10 tools; primary machine-global doc lookup; keep eager. | Admitted; PASS. |
| **context7** | `context7` | Active (`enabled=true`) | **Classic Active** | 2 tools; gateway-only public doc miss bridge; keep eager. | Admitted; PASS. |
| **Serena** | `serena` | Dormant (`enabled=false`) | **Phase 3 Primary (Code Mode via HTTP Shim)** | 21 tools; heavy code navigation; must be Code Mode. | Admitted via `serena_session_shim.py` on HTTP loopback `:18090`. |
| **filesystem** | `filesystem` | Dormant (`enabled=false`) | **Phase 3b Sibling (Dormant Project-Scoped)** | 14 tools; dangerous if global; must bind to enrolled project root. | Needs session-bound root routing (Phase 3b). |
| **GitHub MCP** | `github-mcp` | Deferred (`enabled=false`) | **Code Mode Preflagged (Deferred)** | 26+ tools; heavy catalog; must be Code Mode when admitted. | Replace wildcard `["*"]` with named tool list; Docker container health gate. |
| **Playwright MCP** | `playwright` | Active (`enabled=true`) | **Code Mode Active** | 24 tools; browser automation; kept lazy in Code Mode VFS. | Admitted; PASS. |
| **Fetch** | `fetch-mcp` | Rejected (`enabled=false`) | **Rejected** | Generic fetch introduces SSRF and duplicates Tavily/Exa/Arabold. | REJECTED: Do not admit raw fetch. |
| **Superpowers** | *Not an MCP* | N/A | **Not-an-MCP (Skill/Plugin Layer)** | Superpowers is a Cursor skill framework, not a Bifrost MCP server. | Use via Cursor skills directory; do not add MCP entry. |
| **Cline** | *Not an MCP* | N/A | **Not-an-MCP (IDE/Host Client)** | Cline is an autonomous coding extension/client that connects to Bifrost. | Enroll via `contracts/agentcore-gateway-client.json`. |
| **ZooCode** | *Not an MCP* | N/A | **Not-an-MCP (IDE/Host Client)** | Zoo Code is an IDE profile client that connects to `agentcore-gateway`. | Enrolled in `contracts/agentcore-gateway-client.json`. |
| **SQLite MCP** | `sqlite-mcp` | Rejected (`enabled=false`) | **Rejected** | Raw SQL tool; breaks canonical memory architecture; high corruption risk. | REJECTED: Use `agentcore-memory` or governed Python admin scripts. |
| **Postgres MCP** | `postgresql-mcp` | Rejected (`enabled=false`) | **Rejected** | Raw SQL tool; leaks credentials; violates PG18 security definer boundaries. | REJECTED: Use `agentcore-memory` facade and LangGraph ops. |
| **Tentra MCP** | `tentra` | Dormant (`enabled=false`) | **Phase 3b Sibling (Dormant Project-Scoped)** | 5 tools; project-scoped index; Pattern A host-owned CLI preferred. | Cwd binding requirement; evaluate in Phase 3b. |
| **Depwire MCP** | `depwire` | Dormant (`enabled=false`) | **Phase 3b Sibling (Dormant Project-Scoped)** | 6 tools; dependency graphs; Pattern A local explicit-cwd preferred. | Cwd binding requirement; evaluate in Phase 3b. |
| **Zed MCP** | *Not an MCP* | N/A | **Not-an-MCP (IDE Client)** | Zed is an enrolled editor connecting to `agentcore-gateway`. | Enrolled in `contracts/agentcore-gateway-client.json`. |
| **Cherry Studio** | *Not an MCP* | N/A | **Not-an-MCP (IDE Client)** | Cherry Studio is an enrolled client connecting to `agentcore-gateway`. | Enrolled in `contracts/agentcore-gateway-client.json`. |
| **FastAPI** | *Clarification* | Absent | **Catalog Candidate / Arabold Docs** | FastAPI is a Python web framework, not a standard MCP server. | Framework docs indexed in `arabold-docs`; application wrappers live in app code. |
| **OpenDeepSearch** | `opendeepsearch-mcp` | Absent | **Catalog Candidate (Code Mode)** | Deep web research with multi-source synthesis. | Needs official package pin, license, API key env, tool inventory. |
| **Context Mode (mksglu)** | `context-mode` | Absent | **Catalog Candidate (Code Mode)** | Context window optimization and token compression MCP. | Needs npm package pin, license check, tool schema verification. |
| **Docker** | `docker-cli-bounded` | Absent | **Catalog Candidate (Code Mode Bounded)** | Bounded container management (NOT second aggregator `docker-mcp-toolkit`). | Strict isolation: only inspect/run explicitly permitted project containers. |
| **LanceDB** | `lancedb-mcp` | Absent | **Catalog Candidate (Evaluation Gated)** | Embedded vector database; AgentCore baseline is pgvector in PG18. | Evaluation candidate; requires ADR before Context Engine integration. |
| **graphify** | `graphify-mcp` | Absent | **Catalog Candidate (Evaluation Gated)** | Codebase knowledge graph generator (`0.9.22`). | Evaluation gated; forbidden from Context Engine dependency without ADR. |
| **repowise** | `repowise-mcp` | Absent | **Catalog Candidate (Code Mode)** | Codebase summarization and architecture map MCP. | Needs official pin, repository verification, named tool list. |
| **Grafana** | `grafana-mcp` | Absent | **Catalog Candidate (Code Mode)** | Observability dashboards, metrics, and incident diagnosis. | Needs Grafana instance URL, service token env, read-only tools list. |
| **Stripe** | `stripe-mcp` | Absent | **Catalog Candidate (Code Mode)** | Stripe developer docs, API queries, and event inspection. | Needs restricted API key env, read-only vs write-capable separation. |
| **Chrome DevTools** | `chrome-devtools-mcp` | Absent | **Catalog Candidate (Code Mode)** | CDP inspection; note Playwright and cursor-ide-browser already cover this. | Avoid duplicate capabilities; evaluate necessity vs existing tools. |
| **ElevenLabs** | `elevenlabs-mcp` | Absent | **Catalog Candidate (Code Mode)** | Audio and voice synthesis. | Needs API key env, tool schema inventory, billable tool gating. |
| **Figma** | `figma-mcp` | Absent | **Catalog Candidate (Code Mode)** | Design tokens, components, and layout inspect MCP (`mcp.figma.com`). | Remote HTTP endpoint, OAuth/PAT token env, read-only inspect tools. |

---

## 4. Target Surface Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │            agentcore-gateway                 │
                    │         http://127.0.0.1:8080/mcp            │
                    └──────────────────────┬───────────────────────┘
                                           │
             ┌─────────────────────────────┴─────────────────────────────┐
             ▼                                                           ▼
┌─────────────────────────┐                                 ┌─────────────────────────┐
│     CLASSIC SURFACE     │                                 │     CODE MODE SURFACE   │
│     (Eager Discovery)   │                                 │    (Lazy VFS Discovery) │
│                         │                                 │                         │
│ • agentcore-memory (10) │                                 │ • morph-mcp (7)         │
│ • sequential-thinking(1)│                                 │ • playwright (24)       │
│ • arabold-docs (10)     │                                 │ • exa-research (2)      │
│ • context7 (2)          │                                 │ • firecrawl-research (8)│
│ • cursor-agent-mcp (8)  │                                 │ • tavily-research (5)   │
│ • skills-hub (3)        │                                 │ • apify-research (5)    │
│ • nia (12)              │                                 │ • mcp-prompt-optimizer(7│
│ • agentcore-catalog (2) │                                 │ • openrouter (13, JIT)  │
│                         │                                 │ • serena (21, via Shim) │
│ Total: 48 eager tools   │                                 │ Total: 92 lazy tools    │
└─────────────────────────┘                                 └─────────────────────────┘
```

---

## 5. Phase 0 Conclusions & Action Gates

1. **Classic Surface is Frozen & Protected:** The 9 classic servers remain eager. No heavy servers will be promoted to classic.
2. **Code Mode is the Sole Expansion Path:** Any new capabilities pass admission into Code Mode only.
3. **Phase 1 Action:** Synchronize Bifrost runtime config, capture tool inventory counts, and enforce rejected server guards. Keep `github-mcp` deferred until named inventory + Docker health canary.
4. **Phase 3 Action (Primary Deliverable):** HTTP session-shim on `:18090` with enrollment-contract project resolution (default-deny; no control-plane fallback), ADR, and isolation canary.
5. **Phase 3b:** Shared `session_identity` only; `filesystem` / `depwire` / `tentra` / `context-fabric` remain `enabled=false` (see `PHASE3B_PROJECT_SCOPED_RESIDUAL_BLOCKERS_2026-09-09.md`).
6. **Phase 4:** Catalog wishlist leftovers as Code Mode candidates with official pins; admit nothing that fails pin/license/inventory/canary.
