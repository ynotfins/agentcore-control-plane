# Bifrost Code Mode Optimization & Surface Hygiene Audit (2026-09-09)

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`, `renderers/bifrost/config.sanitized.json`, `docs/bifrost/BIFROST_CODE_MODE_RUNBOOK.md`  
**Execution Environment:** Windows 10 x64, Bifrost v2.0.0 (`F:\AgentCore\runtime\bifrost`)  
**Base Branch:** `setup/zoo-code-qdrant-nfa-20260820`  
**Commit:** Phase 1 Code Mode Hygiene

---

## 1. Runtime & Renderer Configuration Verification

The rendered Bifrost configuration was verified across both repository projections and the active live runtime:

| Config Target | Path | `code_mode_binding_level` | Code Mode Clients Verified (`is_code_mode_client: true`) |
|---|---|---|---|
| Sanitized Renderer | `renderers/bifrost/config.sanitized.json` | `tool` | `morph_mcp`, `playwright`, `exa_research`, `tavily_research`, `firecrawl_research`, `apify_research`, `mcp_prompt_optimizer`, `openrouter` (8 servers) |
| Live Bifrost Config | `F:\AgentCore\runtime\bifrost\config.json` | `tool` | `morph_mcp`, `playwright`, `exa_research`, `tavily_research`, `firecrawl_research`, `apify_research`, `mcp_prompt_optimizer`, `openrouter` (8 servers) |

Both config files match the registry contracts with exact parity.

---

## 2. Tool Surface Metrics: Eager vs Lazy VFS

### Classic Eager Tools (Discovered on Every Turn)
Total classic servers: 9  
Total eager tools in `builder` profile: **48 tools**

| Classic Upstream Server | Eager Tools Exposed | Purpose |
|---|---|---|
| `agentcore-memory` | 10 | Canonical database-backed memory facade (`startup_context`, `retrieve_context`, etc.) |
| `agentcore-capability-catalog` | 2 | Capability discovery (`list_capabilities`, `get_capability_detail`) |
| `sequential-thinking` | 1 | Structured step-by-step reasoning (`sequentialthinking`) |
| `arabold-docs` | 10 | Machine-global library documentation search & scrape |
| `context7` | 2 | Public library doc miss bridge |
| `cursor-agent-mcp` | 8 | Cursor cloud agent orchestration |
| `skills-hub` | 3 | Dynamic skill catalog search |
| `nia` | 12 | Agentic multi-repository search and retrieval |
| `agentcore-project-router` | (4) | Restricted to `operator` profile; not in standard `builder` |
| **Meta-tools for Code Mode** | 4 | `listToolFiles`, `readToolFile`, `getToolDocs`, `executeToolCode` |

### Code Mode Lazy VFS Tools (Discovered on Demand via `listToolFiles`)
**Registry / renderer Code Mode clients:** 8 flagged (`morph_mcp`, `playwright`, `exa_research`, `tavily_research`, `firecrawl_research`, `apify_research`, `mcp_prompt_optimizer`, `openrouter`) plus `serena` (HTTP shim, admitted separately).

**Live Cursor `listToolFiles` (2026-09-09 continuation session):** **6** servers only:

| Code Mode Upstream Server | Live in `listToolFiles`? | Notes |
|---|---|---|
| `playwright` | Yes | 24 tools |
| `morph_mcp` | Yes | 7 tools |
| `firecrawl-research` | Yes | 8 tools |
| `tavily-research` | Yes | 5 tools |
| `apify-research` | Yes | 5 tools |
| `exa-research` | Yes | 2 tools |
| `mcp-prompt-optimizer` | No (eager in this Cursor session) | Registry `is_code_mode_client=true`; client still hydrates tools eagerly |
| `openrouter` | No | JIT / dormant; zero default exposure expected |
| `serena` | No until shim live + reconnect | Registry active HTTP `:18090`; default-deny identity fixed 2026-09-09 |

**Context Optimization Impact:** When the VFS path is hydrated, keeping heavy tool schemas out of eager context saves on the order of **~14,000–22,000 tokens** per turn. Claims must cite live `listToolFiles`, not registry flags alone.

---

## 3. GitHub MCP Admission Package & Gate Status

- **Canonical ID:** `github-mcp`
- **Current Registry Status:** `enabled: false`, `status: "deferred"`, `is_code_mode_client: true`
- **Pre-flagged Configuration:** Docker container stdio launch (`ghcr.io/github/github-mcp-server:1.3.0`)
- **Admission Gates Evaluation:**
  1. *Named Tool Inventory:* Upstream GitHub MCP provides 26 tools. Registry currently carries transitional wildcard `permitted_tools: ["*"]`. Under `TOOL_LIFECYCLE_POLICY.md`, wildcard grants are forbidden for active servers. Wildcard must be replaced with an explicit named allowlist prior to activation.
  2. *Runtime Health Canary:* Docker Desktop daemon must be active, attested, and verified with valid `GITHUB_PERSONAL_ACCESS_TOKEN` in Windows User environment. Automated stdio launching of Docker containers on Windows requires verified daemon health.
  3. *Blast Radius:* GitHub tools include write operations (`create_or_update_file`, `push_files`, `merge_pull_request`, `delete_branch`). These require Tier-3 / Tier-4 operator confirmation.
- **Decision:** **LEAVE DEFERRED.** `github-mcp` remains pre-flagged with `is_code_mode_client: true` and `enabled: false`. It will not be enabled until the Docker daemon health canary and named tool allowlist are completed in a dedicated task.

---

## 4. Rejection Verification for High-Risk & Redundant Upstreams

The following candidates are confirmed **REJECTED** (`enabled: false`, `status: "rejected"`) across all contracts and renderers:

| Server | Status | Rejection Basis |
|---|---|---|
| `postgresql-mcp` | `rejected` | Direct raw database queries bypass PG18 SECURITY DEFINER boundaries and violate canonical memory facade. |
| `sqlite-mcp` | `rejected` | Direct SQLite access introduces database path ambiguity and state corruption risks. |
| `fetch-mcp` | `rejected` | Unconstrained network fetch introduces SSRF risks and duplicates admitted search engines (Tavily/Exa/Arabold). |
| `wcgw` | `rejected` | Unrestricted shell and WSL execution violates Stage B workspace boundary enforcement. |
| `docker-mcp-toolkit` | `rejected` | Second MCP aggregator conflicts with Bifrost as the sole MCP gateway. |
| `ref-mcp` | `rejected` | Redundant remote documentation provider; Arabold is the authoritative local machine-global store. |

---

## 5. Contract Validation & Test Results

Deterministic validation commands executed on repo venv (`Python 3.13`):

1. `python scripts/bifrost/validate_contracts.py`
   - Registry and client schema validation: **PASS**
   - Output schema normalizer coverage: **PASS** (0 MissingOutputSchema)
   - Secret scan: **PASS**
2. `python scripts/bifrost/test_contracts.py`
   - **PASS: 198 checks** (0 failures).
