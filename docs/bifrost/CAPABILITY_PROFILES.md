# Capability Profiles — AgentCore Bifrost Gateway

**Authority:** `contracts/bifrost-upstream-mcp-registry.json` → `capability_profiles`
**Updated:** 2026-07-12

Profiles select which upstream MCP servers (and, where implemented, which tools) a virtual key may use. Primary builder key env: `BIFROST_MCP_VIRTUAL_KEY`. Profile-specific stub envs are named in the registry notes (`BIFROST_MCP_VK_*`).

## builder

- **Purpose:** Full AgentCore coding and planning surface.
- **Servers:** arabold-docs, serena, sequential-thinking, cursor-agent-mcp, context-fabric, mcp-debugger, artiforge, depwire, tentra, obsidian-vault, playwright, filesystem, agentcore-memory, agentcore-project-router
- **Policy:** allow_permitted
- **VK:** `BIFROST_MCP_VIRTUAL_KEY`

## reviewer

- **Purpose:** Read-focused review; deny debugger attach / admin write tools.
- **Servers:** arabold-docs, serena, sequential-thinking, context-fabric, depwire, obsidian-vault, filesystem, agentcore-memory, agentcore-project-router
- **Policy:** profile_override (mcp-debugger attach tools denied)
- **VK stub:** `BIFROST_MCP_VK_REVIEWER`

## database-validator

- **Purpose:** Health/status against memory/database contracts without credential exposure.
- **Servers:** agentcore-memory, arabold-docs, agentcore-project-router
- **Policy:** deny_by_default
- **VK stub:** `BIFROST_MCP_VK_DATABASE_VALIDATOR`

## docs-knowledge

- **Purpose:** Documentation lookup and durable note retrieval.
- **Servers:** arabold-docs, obsidian-vault, sequential-thinking, agentcore-project-router
- **Policy:** allow_permitted
- **VK stub:** `BIFROST_MCP_VK_DOCS_KNOWLEDGE`

## operator

- **Purpose:** Operational gateway administration and project routing.
- **Servers:** agentcore-project-router, agentcore-memory, depwire, artiforge, obsidian-vault, arabold-docs
- **Policy:** allow_permitted
- **VK stub:** `BIFROST_MCP_VK_OPERATOR`

## Rules

- Do not invent profile names outside the registry.
- Do not put profile secrets in Git.
- Swarm servers are not members of any non-Swarm profile.
- Deferred servers (`depwire-cloud`, `github-mcp`) are not active until `enabled: true` after health gates.
