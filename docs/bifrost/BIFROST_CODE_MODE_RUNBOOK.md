# Bifrost Code Mode Runbook

> **TASK-SPECIFIC RUNBOOK — EXCLUDED FROM DEFAULT PROJECT SOURCES.** Code Mode is a task-specific VFS meta-tool feature of Bifrost. Excluded from default ChatGPT Project Sources unless a Code Mode workstream is explicitly active.

**Authority:** `renderers/bifrost/config.json` (`mcp.tool_manager_config`), `contracts/bifrost-upstream-mcp-registry.json`  
**Updated:** 2026-09-09  
**Current State:** Binding level `tool` is rendered explicitly. Code Mode is enabled for heavy global clients. Classic servers remain eager. Serena is admitted only via the HTTP session-shim architecture (never sticky STDIO).

## What is Code Mode

Code Mode exposes a virtual file system (VFS) of tool definitions through four meta-tools:
- `listToolFiles` — list available tool definition files
- `readToolFile` — read a specific tool definition
- `getToolDocs` — get documentation for a tool
- `executeToolCode` — execute tool code

This dramatically reduces context usage for large-catalog servers. In Bifrost v2.0.0, Code Mode is configured per MCP client with `is_code_mode_client: true`, while `code_mode_binding_level` is a global organization setting for the virtual file system.

## Current Config

`code_mode_binding_level` is rendered as `tool`.

```json
{
  "mcp": {
    "tool_manager_config": {
      "tool_execution_timeout": "2m",
      "max_agent_depth": 1,
      "disable_auto_tool_inject": true,
      "code_mode_binding_level": "tool"
    }
  }
}
```

Binding level `tool` is preferred for large catalogs; `server` remains a valid option when a whole client binds as a single VFS unit.

## Active Code Mode Clients (Rendered into VFS)

- `morph_mcp` — 7 executable source-discovery/edit tools
- `playwright` — 24 executable browser automation tools; no automatic execution allowlist
- `exa_research` — 2 executable web research tools
- `tavily_research` — 5 executable search/extract/crawl/map/research tools
- `firecrawl_research` — 8 executable web/paper/github research tools
- `apify_research` — 5 executable actor discovery/docs tools; never auto-executed
- `mcp_prompt_optimizer` — 7 prompt analysis and optimization tools
- `openrouter` — OpenRouter model catalog tools (zero default exposure; requires M6 lease + JIT VK bridge)

## Pre-Flagged Code Mode (Registered, Not Yet Live)

- `github_mcp` — `is_code_mode_client=true` with `enabled=false` / `status=deferred`; requires named inventory replacing wildcard `["*"]` and container/CLI health gate before activation.

## Servers That Must Remain in Classic Mode (Core Direct)

These servers must remain in Classic (eager) mode across all profile definitions. Never flip them to Code Mode:

1. `agentcore_memory` — stable 10-tool canonical memory facade; must be immediately discoverable for session recovery and prompt continuity without Code Mode meta-tool ceremony.
2. `agentcore_capability_catalog` — 2 tools (`list_capabilities`, `get_capability_detail`); read-only capability and elevation route discovery.
3. `sequential_thinking` — 1 tool (`sequentialthinking`); foundation multi-step reasoning and planning.
4. `arabold_docs` — 10 tools; machine-global official library documentation lookup (`F:\AgentCore\runtime\docs-store\arabold`).
5. `context7` — 2 tools; same-turn public documentation bridge while Arabold scrape runs.
6. `cursor_agent_mcp` — 8 tools; Cursor subagent orchestration controls.
7. `skills_hub` — 3 tools; dynamic skill search and metadata retrieval (`install_skill` denied).
8. `nia` — 12 permitted tools; agentic search across indexed repositories and documentation.
9. `agentcore_project_router` — 4 tools; operator-only project activation (not IDE continuity).

## Serena Hard Stop: Why Sticky STDIO Cannot Work

Per Bifrost architectural documentation (`D:\bifrost-docs-source\docs\mcp\`):
1. **STDIO connections in Bifrost are always sticky.** The `stdio_config` schema accepts only `command`, `args`, and `envs`. It has no `working_directory` parameter and no mechanism to vary working directory per caller turn.
2. **STDIO has no per-request header injection.** `allowed_extra_headers` and per-user credentials only exist for HTTP and SSE transports.
3. **Machine-global `active-project.json` fails multi-IDE concurrency.** If two IDEs (e.g. Cursor on `agentcore-control-plane` and Zed on `agentcore-context-engine`) use the gateway simultaneously, a shared STDIO Serena subprocess either serves the wrong repository or crashes from race conditions.
4. **Hard Stop Rule:** Never set `serena.enabled: true` on a shared STDIO client. Serena is admitted to Bifrost **only** via the AgentCore HTTP session-shim (`scripts/bifrost/serena_session_shim.py`), which maps caller session/VK headers to enrolled projects from `contracts/agentcore-project-enrollment.json` through `scripts/bifrost/session_identity.py` (default-deny; never fall back to `agentcore-control-plane`) and routes to strictly isolated Serena child processes.
5. **Live evidence rule:** Cite current `listToolFiles` for VFS claims. Registry `is_code_mode_client=true` alone does not prove a server appears in the live Code Mode tree.

## VK Permission Enforcement

Virtual-key permissions are strictly enforced inside Code Mode. A VK that does not have access to an MCP server or specific tool in classic mode cannot discover or execute it through Code Mode VFS meta-tools.

`tools_to_auto_execute` remains empty for all Code Mode clients. Code Mode exposes permitted tools as executable functions through `executeToolCode`; it never authorizes autonomous tool execution without LLM invocation.

## Matrix Reference

The full authoritative tool matrix and classification of all ~40 registry servers plus operator wishlist candidates is documented in `audits/bifrost/BIFROST_TOOL_SURFACE_MATRIX_2026-09-09.md`.
