# Dormant MCP Capability Catalog

**Status:** `DORMANT MCP CAPABILITY CATALOG READY` (documentation + registry reconciliation; zero default tool exposure for dormant entries)
**Authority:** `contracts/bifrost-upstream-mcp-registry.json`, `contracts/project-tool-lifecycle.json`, `PROJECT_ANCHOR.md`
**Updated:** 2026-08-05
**Scope:** Non-Swarm AgentCore gateway only. SwarmRecall / SwarmVault / SwarmClaw excluded.

## Purpose

This catalog is the single human-readable index of MCP capabilities that are:

1. already registered behind `agentcore-gateway` but **dormant / deferred / disabled**, or
2. approved for future registration after official-source and compatibility checks, or
3. **blocked** by current authority and must not be silently enrolled.

It does **not** authorize live IDE configuration changes. IDEs keep the single entry `agentcore-gateway` at `http://127.0.0.1:8080/mcp`.

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
| `playwright` | `@playwright/mcp` (registry pin) | stdio | none | builder profile | Browser automation; operator-risk class |
| `arabold-docs` | `@arabold/docs-mcp-server` vendored pin | stdio | `OPENAI_API_KEY` | builder/reviewer/docs/database/operator/chatgpt profiles | Documentation lookup; Code Mode enabled |
| `sequential-thinking` | `@modelcontextprotocol/server-sequential-thinking@2026.7.4` | stdio | `DISABLE_THOUGHT_LOGGING` | builder/reviewer/docs/chatgpt profiles | One-tool planning surface; classic mode |
| `agentcore-memory` | repo-owned Python server | stdio | inherited AgentCore env | builder/reviewer/database/operator/chatgpt profiles | Canonical memory facade; classic mode |
| `agentcore-project-router` | repo-owned Python server | stdio | none | operator profile | Operator-only project activation; classic mode |
| `cursor-agent-mcp` | `cursor-agent-mcp@1.0.5` | stdio | `CURSOR_API_KEY`, `CURSOR_API_URL` | builder profile | Cursor subagent controls; exact allowlist; classic mode |
| `skills-hub` | isolated local wrapper | stdio | none | builder/chatgpt profiles | `install_skill` denied |

### Deferred / dormant — zero default tools

| Canonical ID | Status | Pin / endpoint | Auth | Env names | Activation | Deactivation / rollback |
| -- | -- | -- | -- | -- | -- | -- |
| `openrouter` | `dormant` registry + `authenticated_dormant` lifecycle (`enabled=true`, not in default `allowed_server_ids`) | `https://mcp.openrouter.ai/mcp` | OAuth (`mcp` scope) bound in Bifrost store | none (OAuth in Bifrost store); `BIFROST_ENCRYPTION_KEY` required | M6 lease + `jit_vk_bridge` for exact groups — see `docs/operations/OPENROUTER_MCP.md` | revoke lease / revoke OAuth; re-render; restart `\AgentCore\AgentCore-Bifrost-Gateway` |
| `filesystem` | `dormant_project_scoped` (`enabled=false`) | `@modelcontextprotocol/server-filesystem@2026.7.10` through project router | none | Explicit project identity + lease; do not expose as default global filesystem | `enabled=false`; no per-IDE duplicate |
| `obsidian-vault` | `disabled` (`enabled=false`) | OpenClaw launcher script (registry) | none | Explicit operator enable only | `enabled=false`; no per-IDE duplicate |
| `github-mcp` | `deferred` (`enabled=false`) | `ghcr.io/github/github-mcp-server` via Docker | PAT | `GITHUB_PERSONAL_ACCESS_TOKEN`, `GITHUB_PAT_TOKEN` | Health gate + named tool inventory + remove wildcard before enable | Remain `enabled=false`; no Docker start from this catalog alone |
| `mcp-debugger` | `disabled` | registry pin | none | — | Explicit operator enable | `enabled=false` |
| `artiforge` | `disabled` | registry pin | none | — | Explicit operator enable | `enabled=false` |
| `depwire-cloud` | `disabled`/`deferred` | `https://api.depwire.dev/mcp` | Bearer | `DEPWIRE_API_KEY` | Cloud connection health gate | `enabled=false` |

**OpenRouter current evidence (2026-07-20):** registered once; OAuth authorized + client `connected` (`audits/OPENROUTER_MCP_OAUTH_BIND_2026-07-20.md`); registry `status` remains `dormant`; lifecycle `authenticated_dormant`; zero OpenRouter tools on VKs without an M6 lease; JIT bridge proven for discovery (13 tools) + revoke-to-zero. Classification: `contracts/openrouter-tool-manifest.json`. Do not claim IDE model availability from MCP registration; do not add direct OpenRouter MCP IDE entries.

**GitHub MCP note:** still carries transitional `permitted_tools: ["*"]`. Wildcard must be replaced with a named inventory before any enablement (wildcard_policy transitional exception must not be extended).

---

## Approved for future registration (catalogued; not yet Bifrost clients)

Entries below are **not** duplicated into the Bifrost registry until an official pin, transport, auth/env names, discovered tool inventory + timestamp, risk group, and activation/rollback procedure are verified. Default exposure remains **zero**.

| Canonical ID | Domain | Official-source target | Likely transport | Likely env / auth | Risk group | Catalog state | Compatibility check |
| -- | -- | -- | -- | -- | -- | -- | -- |
| `gitlab-mcp` | Git hosting | Official GitLab MCP / docs.gitlab.com | stdio or http | `GITLAB_TOKEN` (name only) | write_capable / operator | `catalogued_pending_registration` | Verify current official package or remote endpoint; pin version; named tools only |
| `gitkraken-mcp` | Git UX | Official GitKraken MCP docs | stdio | vendor token env name | write_capable | `catalogued_pending_registration` | Confirm Windows support; avoid dual Git authority with github-mcp |
| `firecrawl-mcp` | Web crawl | Official Firecrawl MCP | stdio/http | `FIRECRAWL_API_KEY` | billable / network | `catalogued_pending_registration` | Prefer official server; do not substitute unverified community forks |
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
