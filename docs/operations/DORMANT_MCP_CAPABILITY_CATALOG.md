# Dormant MCP Capability Catalog

**Status:** `DORMANT MCP CAPABILITY CATALOG READY` (documentation + registry reconciliation; zero default tool exposure for dormant entries)
**Authority:** `contracts/bifrost-upstream-mcp-registry.json`, `contracts/project-tool-lifecycle.json`, `PROJECT_ANCHOR.md`
**Updated:** 2026-09-09
**Scope:** Non-Swarm AgentCore gateway only. SwarmRecall / SwarmVault / SwarmClaw excluded.

## Purpose

This catalog is the single human-readable index of MCP capabilities that are:

1. already registered behind `agentcore-gateway` but **dormant / deferred / disabled**, or
2. approved for future registration after official-source and compatibility checks, or
3. **blocked** by current authority and must not be silently enrolled.

It does **not** authorize live IDE configuration changes. Each enrolled IDE keeps one `agentcore-gateway` entry selected by `contracts/agentcore-gateway-client.json`: direct `http://127.0.0.1:8080/mcp` with environment-backed authentication, `http://127.0.0.1:18082/mcp` only for approved process-attested Trust Class A clients, and no active entry for clients whose `gateway_auth_mode` is `unverified`.

## Invariants

| Rule | Enforcement |
| -- | -- |
| Single IDE MCP entry | `contracts/agentcore-gateway-client.json` + generated IDE rules |
| Zero tools without a lease for dormant servers | Not listed in `capability_profiles[*].allowed_server_ids`; M6 lease for JIT |
| Do not duplicate `openrouter`, `obsidian-vault`, or `filesystem` | Registry already owns one of each |
| Do not extend wildcard `permitted_tools: ["*"]` to new servers | `contracts/project-tool-lifecycle.json` wildcard_policy |
| Secrets | Windows User env names only; never commit values |
| Hostinger | **Blocked** pending explicit `PROJECT_ANCHOR.md` authority change |
| Context7 | **Active** behind Bifrost only (arabold-first same-turn public bridge; never IDE mcp.json) |
| Community servers | Catalog-only until official pin + checksum + operator activation gate |

## Lifecycle states used here

| State | Meaning |
| -- | -- |
| `active` | Enabled in registry and eligible for profile grants |
| `installed_dormant` / `dormant` | Present in Bifrost config (or registry-enabled) but **zero** permanent tools |
| `deferred` | Registry entry exists; `enabled=false`; not rendered into live Bifrost clients |
| `catalogued_pending_registration` | Documented here only; no Bifrost client yet |
| `catalog_only` | Framework/reference inventory; never auto-installed |
| `candidate_unverified` | Named request without verified official MCP pin |
| `blocked_authority` | Explicitly forbidden by `PROJECT_ANCHOR.md` until operator overrides authority |

---

## Already registered (reconcile; do not re-register)

### Active — already exposed through profiles when healthy

| Canonical ID | Pin / provenance | Transport | Env names | Default exposure | Notes |
| -- | -- | -- | -- | -- | -- |
| `playwright` | `@playwright/mcp` (registry pin) | stdio | none | builder/openclaw profiles | Browser automation; operator-risk class |
| `arabold-docs` | `@arabold/docs-mcp-server` vendored pin | stdio | `OPENAI_API_KEY` | builder/reviewer/docs/database/operator/chatgpt/openclaw profiles | Core documentation lookup; eager/classic mode |
| `sequential-thinking` | `@modelcontextprotocol/server-sequential-thinking@2026.7.4` | stdio | `DISABLE_THOUGHT_LOGGING` | builder/reviewer/docs/chatgpt/openclaw profiles | One-tool planning surface; classic mode |
| `agentcore-memory` | repo-owned Python server | stdio | inherited AgentCore env | builder/reviewer/database/operator/chatgpt/openclaw profiles | Canonical memory facade; classic mode |
| `agentcore-project-router` | repo-owned Python server | stdio | none | operator profile | Operator-only project activation; classic mode |
| `cursor-agent-mcp` | `cursor-agent-mcp@1.0.5` | stdio | `CURSOR_API_KEY`, `CURSOR_API_URL` | builder profile | Cursor subagent controls; exact allowlist; classic mode |
| `skills-hub` | isolated local wrapper | stdio | none | builder/chatgpt/openclaw profiles | `install_skill` denied |
| `agentcore-capability-catalog` | repo-owned Python server | stdio | none | normal governed profiles except OpenClaw | Read-only `list_capabilities` / `get_capability_detail`; exposes policy metadata, never upstream schemas or credentials |
| `exa-research` | `exa-mcp-server@3.4.1` | stdio | `EXA_API_KEY` | builder profile through Code Mode | Two admitted read-only tools |
| `tavily-research` | `tavily-mcp@0.2.22` | stdio | `TAVILY_API_KEY` | builder profile through Code Mode | Five admitted read-only tools |
| `firecrawl-research` | `firecrawl-mcp@3.24.0` | stdio | `FIRECRAWL_API_KEY` | builder profile through Code Mode | Eight admitted read-only web, paper, and public-code tools |
| `apify-research` | `@apify/actors-mcp-server@0.15.4` | stdio | `APIFY_API_KEY` (adapter aliases child `APIFY_TOKEN`) | builder profile through Code Mode | Five admitted discovery/docs tools including bounded `call-actor`; never auto-executed |

### Deferred / dormant — zero default tools

| Canonical ID | Status | Pin / endpoint | Auth | Env names | Activation | Deactivation / rollback |
| -- | -- | -- | -- | -- | -- | -- |
| `openrouter` | `dormant` registry + `authenticated_dormant` lifecycle (`enabled=true`, not in default `allowed_server_ids`) | `https://mcp.openrouter.ai/mcp` | OAuth (`mcp` scope) bound in Bifrost store | none (OAuth in Bifrost store); `BIFROST_ENCRYPTION_KEY` required | M6 lease + `jit_vk_bridge` for exact groups — see `docs/operations/OPENROUTER_MCP.md` | revoke lease / revoke OAuth; re-render; restart `\AgentCore\AgentCore-Bifrost-Gateway` |
| `filesystem` | `dormant_project_scoped` (`enabled=false`) | `@modelcontextprotocol/server-filesystem@2026.7.10` through project router | none | Explicit project identity + lease; do not expose as default global filesystem | `enabled=false`; no per-IDE duplicate |
| `obsidian-vault` | `disabled` (`enabled=false`) | OpenClaw launcher script (registry) | none | Explicit operator enable only | `enabled=false`; no per-IDE duplicate |
| `github-mcp` | `deferred` (`enabled=false`) | `ghcr.io/github/github-mcp-server` via Docker | PAT | `GITHUB_PERSONAL_ACCESS_TOKEN`, `GITHUB_PAT_TOKEN` | Health gate + named tool inventory + remove wildcard before enable | Remain `enabled=false`; no Docker start from this catalog alone |
| `mcp-debugger` | `disabled` | registry pin | none | — | Explicit operator enable | `enabled=false` |
| `depwire-cloud` | `disabled`/`deferred` | `https://api.depwire.dev/mcp` | Bearer | `DEPWIRE_API_KEY` | Cloud connection health gate | `enabled=false` |
| `brightdata-research` | `catalogued_unverified` (`enabled=false`, profileless) | `@brightdata/mcp@2.11.1` | API token | `BRIGHTDATA_API_KEY` | Disposable-account startup and provider-zone side-effect review | Remain uninstalled, disabled, and profileless |
| `serena` | `active` via HTTP session shim (`enabled=true`, Code Mode) | `http://127.0.0.1:18090/mcp` (`scripts/bifrost/serena_session_shim.py`) | none | none | Shim must be running; identity via `session_identity.py` default-deny | `enabled=false`; fall back to host-owned Serena |
| `filesystem` / `depwire` / `tentra` / `context-fabric` | `dormant_project_scoped` | see registry | — | Phase 3b residual blockers: need per-session identity adapters; stay `enabled=false` | Host-owned Pattern A / repo-local CLI | Remain disabled; see `audits/bifrost/PHASE3B_PROJECT_SCOPED_RESIDUAL_BLOCKERS_2026-09-09.md` |

**OpenRouter current evidence (verified 2026-09-08):** registered once; OAuth authorized + client `connected` (original bind evidence: `audits/OPENROUTER_MCP_OAUTH_BIND_2026-07-20.md`); registry `status` remains `dormant`; lifecycle `authenticated_dormant`; zero permanent builder exposure; JIT bridge proven for discovery (13 tools) + revoke-to-zero. Classification: `contracts/openrouter-tool-manifest.json`. Do not claim IDE model availability from MCP registration; do not add direct OpenRouter MCP IDE entries.

**GitHub MCP note:** still deferred (`enabled=false`). Named inventory + Docker daemon health canary required before any enablement. Do not enable in this AUTH window.

---

## Approved for future registration (catalogued; not yet Bifrost clients)

Entries below are **not** duplicated into the Bifrost registry until an official pin, transport, auth/env names, discovered tool inventory + timestamp, risk group, and activation/rollback procedure are verified. Default exposure remains **zero**.

| Canonical ID | Domain | Official-source target | Likely transport | Likely env / auth | Risk group | Catalog state | Compatibility check |
| -- | -- | -- | -- | -- | -- | -- | -- |
| `gitlab-mcp` | Git hosting | Official GitLab MCP / docs.gitlab.com | stdio or http | `GITLAB_TOKEN` (name only) | write_capable / operator | `catalogued_pending_registration` | Verify current official package or remote endpoint; pin version; named tools only |
| `gitkraken-mcp` | Git UX | Official GitKraken MCP docs | stdio | vendor token env name | write_capable | `catalogued_pending_registration` | Confirm Windows support; avoid dual Git authority with github-mcp |
| `google-sheets-mcp` | Sheets | Official Google Workspace MCP / Composio only if re-enabled | http/stdio | Google OAuth or service account env name | write_capable | `catalogued_pending_registration` | Composio remains quarantine until explicitly re-enabled |
| `google-workspace-search-mcp` | Workspace search | Official Google MCP | http | OAuth | read_only / account | `catalogued_pending_registration` | Confirm scopes; no silent broad Gmail/Drive grant |
| `cloudflare-api-mcp` | Cloudflare API | Official Cloudflare MCP | http | `CLOUDFLARE_API_TOKEN` | write_capable / operator | `catalogued_pending_registration` | Separate docs vs API surfaces; zone-scoped tokens only |
| `cloudflare-docs-mcp` | Cloudflare docs | Official Cloudflare docs MCP or arabold index | http | none | read_only | `catalogued_pending_registration` | Prefer arabold-docs when already indexed |
| `agentmail-mcp` | Agent email | Official AgentMail MCP | http/stdio | AgentMail API env name | write_capable / outbound | `catalogued_pending_registration` | Drafts-over-send policy; confirm inbox list before send |
| `vercel-mcp` | Deploy/hosting | Official Vercel MCP | http | `VERCEL_TOKEN` | deploy / operator | `catalogued_pending_registration` | Tier-4 deploy actions require explicit operator confirmation |
| `langchain-docs-mcp` | Framework docs | Official LangChain docs MCP **or** arabold `langchain`/`langgraph` | http | none | read_only | `catalogued_pending_registration` | Prefer arabold-docs when library already indexed |
| `agno-docs-mcp` | Framework docs | Official Agno docs MCP **or** arabold | http | none | read_only | `catalogued_pending_registration` | Prefer arabold-docs when indexed |

### Activation procedure (any catalogued_pending_registration entry)

1. Official-source + version pin verified (arabold-docs / vendor docs).
2. Add registry server with `status: dormant` or `deferred`, `enabled: false` initially (or dormant with empty permanent profile grants).
3. Enumerate `permitted_tools` by name (no new wildcards).
4. Define `tool_groups` + access policies (`jit_short` / `operator_scope` / `billable_approval`).
5. Keep out of all `allowed_server_ids` until a lease or explicit profile grant is approved.
6. Render sanitized Bifrost config; restart only via scheduled-task owner after operator approval.
7. Record inventory hash + timestamp in an audit under `artifacts/` or `audits/`.
8. Rollback: `enabled=false`, re-render, restart; revoke tokens at provider.

### Health / deactivation

- Unhealthy upstream → set `enabled=false` or `status: quarantine`; do not leave broken clients in default profiles.
- Lease expiry / session close / project change revoke JIT exposure (M6).
- Never paste dormant upstreams into per-IDE `mcp.json`.

---

## Catalog-only frameworks and reference servers

| Name | State | Reason |
| -- | -- | -- |
| CrewAI | `catalog_only` | Orchestration framework, not an AgentCore IDE MCP baseline |
| AutoGen | `catalog_only` | Same |
| MCP Registry / reference servers | `catalog_only` | Useful discovery; do not install community reference servers merely to fill gaps |

---

## Candidate unverified

| Name | State | Required before any registration |
| -- | -- | -- |
| YouTube MCP | `candidate_unverified` | Official pin, license, tool inventory, quota/cost model |
| Dropbox MCP | `candidate_unverified` | Official pin, scoped auth, write boundary review |

Do **not** install community packages to satisfy these rows.

---

## Phase 4 wishlist leftovers (Code Mode candidates only — 2026-09-09)

Default target bucket for every row: **Code Mode** (`is_code_mode_client=true` if admitted). Never Classic unless tool count ≤ ~3 and every-turn critical. Admit nothing that fails official pin + license + named inventory + canary.

| Candidate | Proposed ID | Catalog state | Official-source gate | Notes |
| -- | -- | -- | -- | -- |
| OpenDeepSearch | `opendeepsearch-mcp` | `catalogued_pending_registration` | Official package pin + license + tool list | Research synthesis; Code Mode only |
| Context Mode (mksglu) | `context-mode` | `catalogued_pending_registration` | npm pin + license + schema verify | Token compression; evaluate vs existing Code Mode |
| Bounded Docker CLI | `docker-cli-bounded` | `catalogued_pending_registration` | Strict allowlist of inspect/run only | **Not** `docker-mcp-toolkit` (rejected aggregator) |
| LanceDB | `lancedb-mcp` | `catalog_only` / evaluation-gated | ADR required | AgentCore baseline remains pgvector PG18 |
| graphify | `graphify-mcp` | `catalog_only` / evaluation-gated | ADR + isolation tests | Forbidden as Context Engine dependency without ADR |
| repowise | `repowise-mcp` | `catalogued_pending_registration` | Official pin + named tools | Architecture map candidate |
| Grafana | `grafana-mcp` | `catalogued_pending_registration` | Instance URL + read-only token env | Observability |
| Stripe | `stripe-mcp` | `catalogued_pending_registration` | Restricted key; read vs write split | Billing-sensitive |
| Chrome DevTools | `chrome-devtools-mcp` | `catalogued_pending_registration` | Prefer existing Playwright / cursor-ide-browser | Avoid duplicate CDP surfaces |
| ElevenLabs | `elevenlabs-mcp` | `catalogued_pending_registration` | API key + billable gating | Tier-4 cost risk |
| Figma | `figma-mcp` | `catalogued_pending_registration` | Remote HTTP + OAuth/PAT; read-only | Design inspect |
| Superpowers / Cline / Zoo Code / Zed / Cherry | N/A | `catalog_only` (wrong layer) | — | Skills or IDE clients; not Bifrost MCP servers |
| FastAPI | N/A | Prefer `arabold-docs` | Framework docs, not MCP | Index via Arabold |

SwarmRecall product docs: answer from local arabold index (`swarmrecall`); architecture authority remains ADR/boundaries, not vendor README.

---

## Authority exceptions (blocked)

| Name | State | Authority | Required to unblock |
| -- | -- | -- | -- |
| Context7 | `active_gateway` | AUTH-2026-08-30-GLOBAL-LOCAL-DOCS-INGEST; arabold-first; gateway-only | Keep out of IDE mcp.json; never treat Context7 answers as the local corpus |
| Hostinger | `blocked_authority` | `PROJECT_ANCHOR.md` §9 | Explicit operator authority edit to `PROJECT_ANCHOR.md` |

Context7 is registered behind Bifrost as a same-turn public-docs bridge while arabold scrape_docs runs. Hostinger remains blocked. This catalog does **not** authorize pasting Context7 into per-IDE mcp.json.

---

## Profile grant matrix (current)

Dormant/deferred servers must **not** appear in permanent `allowed_server_ids` unless an enablement gate has passed:

| Server | In any `allowed_server_ids` today? | Correct |
| -- | -- | -- |
| `openrouter` | **No** | Yes — JIT-only |
| `github-mcp` | **No** (capability_profiles list is aspirational; enabled=false) | Yes until health gate |
| `context7` | Yes (active) | Expected — arabold-first same-turn public bridge |
| `playwright` | Yes (active) | Expected — active builder-only browser automation |
| `filesystem` / `obsidian-vault` | No | Expected — dormant/disabled, no permanent default exposure |

Validators: `python scripts/bifrost/validate_contracts.py` (includes OpenRouter zero-exposure invariant).

---

## Related documents

- `docs/operations/OPENROUTER_MCP.md`
- `docs/bifrost/MCP_CLASSIFICATION_MATRIX.md`
- `docs/bifrost/CAPABILITY_PROFILES.md`
- `docs/agent-policy/TOOL_LIFECYCLE_POLICY.md`
- `contracts/global-agent-policy.yaml`
- `audits/CURSOR_EXTENSION_TO_MCP_REPLACEMENT_MATRIX.md` (extension substitution; separate Gate E)
