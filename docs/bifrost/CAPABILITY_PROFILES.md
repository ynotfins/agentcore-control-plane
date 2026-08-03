# Capability Profiles — AgentCore Bifrost Gateway

**Authority:** `contracts/bifrost-upstream-mcp-registry.json` → `capability_profiles`
**Updated:** 2026-08-02
**Dormant catalog:** `docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md`

Profiles select which upstream MCP servers (and, where implemented, which tools) a virtual key may use. Primary builder key env: `BIFROST_MCP_VIRTUAL_KEY`. Profile-specific stub envs are named in the registry notes (`BIFROST_MCP_VK_*`).

## builder

- **Purpose:** Full AgentCore coding and planning surface.
- **Servers:** arabold-docs, sequential-thinking, cursor-agent-mcp, playwright, agentcore-memory, skills-hub
- **Deferred:** mcp-debugger, artiforge
- **Policy:** allow_permitted
- **VK:** `BIFROST_MCP_VIRTUAL_KEY`

## reviewer

- **Purpose:** Read-focused review; deny debugger attach / admin write tools.
- **Servers:** arabold-docs, sequential-thinking, agentcore-memory
- **Policy:** profile_override (mcp-debugger attach tools denied)
- **VK stub:** `BIFROST_MCP_VK_REVIEWER`

## database-validator

- **Purpose:** Health/status against memory/database contracts without credential exposure.
- **Servers:** agentcore-memory, arabold-docs
- **Policy:** deny_by_default
- **VK stub:** `BIFROST_MCP_VK_DATABASE_VALIDATOR`

## docs-knowledge

- **Purpose:** Documentation lookup and durable note retrieval.
- **Servers:** arabold-docs, sequential-thinking
- **Policy:** allow_permitted
- **VK stub:** `BIFROST_MCP_VK_DOCS_KNOWLEDGE`

## operator

- **Purpose:** Operational gateway administration and project routing.
- **Servers:** agentcore-project-router, agentcore-memory, arabold-docs
- **Policy:** allow_permitted
- **VK stub:** `BIFROST_MCP_VK_OPERATOR`

## chatgpt

- **Purpose:** Narrow read-focused ChatGPT secure-tunnel surface.
- **Servers:** arabold-docs, sequential-thinking, agentcore-memory, skills-hub
- **Policy:** deny_by_default with named tools
- **VK stub:** `BIFROST_MCP_VK_CHATGPT`

## Rules

- Do not invent profile names outside the registry.
- Do not put profile secrets in Git.
- Swarm servers are not members of any non-Swarm profile.
- Deferred servers (`depwire-cloud`, `github-mcp`) are not active until `enabled: true` after health gates.
- Disabled servers (`mcp-debugger`, `artiforge`) are not active until their account/runtime health gates pass.
- Implicit project-bound servers (`serena`, `depwire`, `tentra`, `filesystem`, `context-fabric`) are dormant in shared profiles until a per-session project identity is enforced. Native IDE tools, repo-local hooks, and explicit-cwd CLIs are the interim path.
- `agentcore-project-router` mutation is operator-only and must not be treated as a multi-IDE isolation boundary.
- `openrouter` is registered **dormant** and must NOT be added to any profile's `allowed_server_ids`. Tools require a live M6 capability lease plus Bifrost VK grant via `scripts/bifrost/jit_vk_bridge.py`. See `docs/operations/OPENROUTER_MCP.md`. The server's `capability_profiles: ["operator"]` field is a JIT-eligibility reference only — not a permanent exposure grant.
- Classified OpenRouter groups (zero default exposure): `openrouter-discovery-read` (includes `get-preset`, `list-presets`), `openrouter-account`, `openrouter-media-generation` (`generate-speech`), `openrouter-transcription` (`transcribe-audio`), `openrouter-billable` (`send-message`/`generate-image` remain denied).
- LangGraph / Studio use the shared MCP client in `scripts/agentcore_workflow/mcp_client.py`. Prefer `BIFROST_MCP_VK_WORKFLOW` when set; otherwise the governed builder key `BIFROST_MCP_VIRTUAL_KEY` with node-scoped tool filtering (`node_tool_policy.py`). No Bifrost admin tools are granted to graph nodes.
- Future catalogued MCP capabilities (GitLab, Firecrawl, Sheets, Cloudflare, AgentMail, Vercel, docs MCPs, etc.) must not be added to permanent profile grants until official pin, named inventory, and an enablement gate pass. Context7 and Hostinger remain `blocked_authority`.
