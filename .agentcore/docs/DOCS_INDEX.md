# AgentCore Docs Index

Machine-oriented index of documentation libraries available via **arabold-docs**
(through `agentcore-gateway` → Bifrost → `arabold_docs-*` tools).

**Last refreshed:** 2026-07-14 (Arabold scrape/search via live Bifrost `127.0.0.1:8080/mcp`; runtime status cross-check updated after gateway repair)
**Evidence:** `artifacts/bifrost-gateway-cutover-2026-07-12/arabold-docs/`
**Cross-ref report:** `artifacts/bifrost-gateway-cutover-2026-07-12/ARABOLD_DOCS_CROSSREF_2026-07-12.md`

---

## How agents must use this index

1. Prefer **arabold-docs** (`arabold_docs-search_docs` / `arabold_docs-fetch_url`) over stale memory.
2. Pin searches to the **version rows below** when answering config/API questions.
3. Cross-check live AgentCore contracts under `contracts/` and runtime under `H:\AgentRuntime\bifrost`.
4. If Arabold is missing a library/version, scrape it before implementing.
5. Cursor no longer has a direct `user-arabold-docs` server — call Arabold **through the gateway**.

---

## Indexed libraries (live Arabold inventory after refresh)

| Library | Pinned / indexed version | Official docs root used | Index status | Live AgentCore pin |
|---------|--------------------------|-------------------------|--------------|--------------------|
| `bifrost` | `2.0.0-prerelease1` | https://docs.getbifrost.ai/ | **completed** deep scrape (`4fea1d70-…`) | Native `bifrost-http.exe` v2.0.0-prerelease1 |
| `openrouter-mcp` | `live` | https://openrouter.ai/mcp | **completed** (2026-07-17 live research) | `openrouter` dormant upstream behind Bifrost |
| `depwire` | `1.8.2` | https://depwire.dev/ | **completed** (`c9fbbbca-…`) | `depwire-cli@1.8.2` → **23 tools** connected |
| `tentra-mcp` | `1.3.3` | GitHub `rdanieli/tentra-mcp` + npm | **completed** (GitHub/npm); trytentra.com/docs ETIMEDOUT | `tentra-mcp@1.3.3 --local` → **35 tools** |
| `serena` | `1.5.4` | https://oraios.github.io/serena/ + GitHub | Partial: hostname scrapes abort; **key pages fetched** (`020_running`, `030_clients`, tools, README) | Live `1.5.4.dev0`; Bifrost STDIO handshake still deferred |
| `modelcontextprotocol` | `2025.6.18` | https://modelcontextprotocol.io/specification/2025-06-18 | **completed** (`a056d1b6-…`) | Bifrost STDIO peer init = protocolVersion **`2025-06-18`** (NDJSON) |
| `playwright-mcp` | `0.0.78` | https://github.com/microsoft/playwright-mcp | **completed** | `@playwright/mcp@0.0.78` → **24 tools** |
| `context-fabric` | `1.0.7` | https://github.com/VIKAS9793/context-fabric | **completed** | vendored `1.0.7` → **5 tools** (`cf_*`) |
| `sequential-thinking` | `2026.7.4` | npm `@modelcontextprotocol/server-sequential-thinking` | **completed** (`36ab8d32-…`) | package `2026.7.4` → **1 tool** |
| `mcp-filesystem` | `2026.7.10` | npm `@modelcontextprotocol/server-filesystem` | **completed** (`43897113-…`) | package `2026.7.10` → **14 tools** |
| `cursor-agent-mcp` | `1.0.5` | npm `cursor-agent-mcp@1.0.5` (+ fetch) | **completed** (npm; Cloudflare sometimes blocks root package URL) | `1.0.5` → **9 tools** |
| `arabold` (server) | n/a | local vendor | live host | vendored **2.4.2** as Bifrost upstream |

Also previously indexed (unchanged): `drizzle-orm`, `hono`, `langgraph-js`, `meilisearch`, `next.js`, `pgvector`.

---

## Failed / deferred doc roots (do not use)

| Attempted URL | Result | Replacement |
|---------------|--------|-------------|
| `https://docs.depwire.dev/` | DNS `ENOTFOUND` | `https://depwire.dev/` |
| `https://www.tentra.ai/docs` | DNS `ENOTFOUND` | GitHub `rdanieli/tentra-mcp` / npm; hosted `trytentra.com/docs` timed out |
| `https://oraios.github.io/serena/` full crawl | aborted (~50%+ child failures) | Fetch numbered pages / `_sources` (see Serena section) |
| Old Serena paths `02-usage/running.html` (no number) | 404 / empty | Use `02-usage/020_running.html` and `_sources/02-usage/020_running.md` |

---

## Bifrost (MCP Gateway) — primary

| Field | Value |
|-------|-------|
| Library | `bifrost` |
| Version | `2.0.0-prerelease1` |
| Docs root | https://docs.getbifrost.ai |
| Schema | https://www.getbifrost.ai/schema |
| Role | Official Bifrost Gateway / HTTP MCP docs for pinned native Windows binary |
| AgentCore runtime | `H:\AgentRuntime\bifrost` |
| Contracts | `contracts/bifrost-upstream-mcp-registry.json`, `contracts/agentcore-gateway-client.json` |

### Must-read Bifrost pages (fetched + indexed)

- `/mcp/gateway` — Bifrost as MCP Gateway (`POST/GET /mcp`)
- `/mcp/gateway-auth` — `mcp_server_auth_mode`: `headers` \| `both` \| `oauth`
- `/mcp/connecting-to-servers` — STDIO/HTTP/SSE clients, `tools_to_execute`, health/retry
- `/quickstart/gateway/setting-up` — `-app-dir`, host/port, config modes
- `/features/governance/virtual-keys` — VK headers, budgets, MCP tool scoping

---

## Serena — current doc paths (URL drift fixed)

Use these when searching/fetching (old unnumbered paths are dead):

- https://oraios.github.io/serena/02-usage/020_running.html (and `_sources/.../020_running.md`)
- https://oraios.github.io/serena/02-usage/030_clients.html
- https://oraios.github.io/serena/01-about/035_tools.html
- https://github.com/oraios/serena + raw README

Docs confirm: `serena start-mcp-server [options]` with STDIO as typical client-launched mode — matches registry args; Bifrost handshake timeout is an AgentCore integration issue, not a wrong CLI from docs.

---

## Cross-reference: docs ↔ this exact workstation

### Aligns with docs (verified live 2026-07-13)

| Topic | Docs say | Our system |
|-------|----------|------------|
| MCP Gateway endpoint | `/mcp` on gateway HTTP port | `http://127.0.0.1:8080/mcp` |
| Bind | localhost / configurable | `-host 127.0.0.1 -port 8080` |
| App directory | `-app-dir` holds config + DBs | `H:\AgentRuntime\bifrost` |
| Auth for IDE clients | VK via Bearer / `x-bf-vk` | `BIFROST_MCP_VIRTUAL_KEY`, `mcp_server_auth_mode=headers` |
| Depwire tool surface | “23 MCP tools” | Live **23** tools connected |
| Context Fabric tools | five `cf_*` tools | Live **5** tools |
| Tentra local mode | `--local`; docs also advertise `init --hook` | Registry: `--local` only; AgentCore **forbids** `init --hook` |
| Playwright MCP | browser automation MCP | Live **24** tools |
| Filesystem MCP | allowed-directory tools | Live **14** tools (`2026.7.10`) |
| Sequential thinking | single planning tool | Live **1** tool (`2026.7.4`) |
| Cursor agent MCP | background agents API | Live **9** tools (`1.0.5`); npm readme matches `CURSOR_API_KEY` |
| MCP initialize | spec `2025-06-18` transports | Bifrost peer init uses **`2025-06-18`**; transports page fetched |

### Drift / caveats (actionable)

| Issue | Evidence | AgentCore action |
|-------|----------|------------------|
| Windows STDIO `envs` allowlist | Listed envs must exist; empty allowlist inherits parent | Renderer uses **empty `stdio_config.envs`**; launcher loads User env |
| Custom Python MCP framing | Spec emphasizes Content-Length; Bifrost Windows Gateway spoke NDJSON | `agentcore_memory` / `agentcore_project_router` speak **NDJSON** |
| MCP draft in Arabold index | Search can surface draft SEPs removing initialize handshake | **Ignore drafts**; implement only what Bifrost `v2.0.0-prerelease1` speaks |
| `find_version(bifrost)` | Reports “unversioned docs exist” even though `2.0.0-prerelease1` scrape completed | Always pass `version=2.0.0-prerelease1` in `search_docs` |
| Tentra hosted docs | `trytentra.com/docs` ETIMEDOUT | Re-scrape when reachable; GitHub/npm sufficient for `--local` |
| Serena full site | Sphinx child-page failure threshold | Prefer numbered HTML / `_sources` fetches; do not trust old paths |
| Artiforge | HTTP 401 inactive user | Deferred in registry |
| Serena under Bifrost | Docs OK; live connect times out | Keep in registry; treat connection as deferred |

### Live Bifrost upstream snapshot (runtime repair cross-check)

Direct authenticated `tools/list` through `agentcore-gateway` returns **127** visible tools for the builder VK.

Connected (10): `agentcore_memory`(2), `agentcore_project_router`(4), `arabold_docs`(10), `context_fabric`(5), `cursor_agent_mcp`(9), `depwire`(23), `filesystem`(14), `playwright`(24), `sequential_thinking`(1), `tentra`(35).

Disconnected upstream caveats: `obsidian_vault` and `serena` currently time out during Bifrost upstream reconnect. The gateway itself is healthy and the expected Cursor-facing tool families above are available.

---

## Refresh commands (via gateway)

```text
arabold_docs-scrape_docs  url=https://docs.getbifrost.ai/  library=bifrost  version=2.0.0-prerelease1  maxPages=500 maxDepth=5 scope=hostname
arabold_docs-search_docs  library=bifrost  version=2.0.0-prerelease1  query=<topic>
arabold_docs-fetch_url    url=https://oraios.github.io/serena/02-usage/020_running.html
```

Re-run Tentra hosted docs when `https://trytentra.com/docs` is reachable.
Re-run Serena full hostname crawl only if Arabold failure threshold improves.
