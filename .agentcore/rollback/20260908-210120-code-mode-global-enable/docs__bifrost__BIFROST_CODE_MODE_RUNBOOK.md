# Bifrost Code Mode Runbook

> **TASK-SPECIFIC RUNBOOK — EXCLUDED FROM DEFAULT PROJECT SOURCES.** Code Mode is a task-specific VFS meta-tool feature of Bifrost. Excluded from default ChatGPT Project Sources unless a Code Mode workstream is explicitly active.

**Authority:** `renderers/bifrost/config.json` (mcp.tool_manager_config)  
**Updated:** 2026-09-08
**Current State:** Binding level `tool` is rendered explicitly. Code Mode is enabled for named heavy global clients in `contracts/bifrost-upstream-mcp-registry.json`.

## What is Code Mode

Code Mode exposes a virtual file system (VFS) of tool definitions through four meta-tools:
- `listToolFiles` — list available tool definition files
- `readToolFile` — read a specific tool definition
- `getToolDocs` — get documentation for a tool
- `executeToolCode` — execute tool code

This can reduce context usage for large-catalog servers. Bifrost's current documentation says Code Mode is configured per MCP client with `is_code_mode_client: true`, while `code_mode_binding_level` is a global organization setting for the virtual file system.

## Current Config

`code_mode_binding_level` is rendered as `tool`.

Enabled Code Mode clients (active / rendered):

- `morph_mcp` — 7 executable source-discovery/edit tools
- `playwright` — 24 executable browser tools; no automatic execution allowlist
- `exa_research` — 2 executable research tools
- `tavily_research` — 5 executable research tools
- `firecrawl_research` — 8 executable research tools
- `apify_research` — 5 executable research tools
- `mcp_prompt_optimizer` — 7 prompt analysis/optimization tools
- `openrouter` — OpenRouter MCP catalog/account tools (still zero default exposure; M6 lease + JIT VK required)

Pre-flagged Code Mode (not enabled / not rendered):

- `github_mcp` — `is_code_mode_client=true` with `enabled=false` / `status=deferred`; do not activate without a separate admission task

Classic clients (must remain eager / non-Code-Mode):

- `agentcore_memory`
- `agentcore_project_router`
- `cursor_agent_mcp`
- `sequential_thinking`
- `skills_hub`
- `arabold_docs`
- `context7`
- `nia`
- `agentcore_capability_catalog`

## Servers That Must Remain in Classic Mode (Core Direct)

- agentcore_memory — stable 10-tool surface; no context savings needed
- agentcore_project_router — 4 tools; no context savings needed
- cursor_agent_mcp — subagent controls should remain directly discoverable
- sequential_thinking — 1 tool; no context savings needed
- skills_hub — 3 tools; no context savings needed
- arabold_docs — 10 tools remain eager for direct documentation access
- context7 — 2 tools remain eager as the same-turn public bridge
- nia — 12 permitted tools remain eager
- agentcore_capability_catalog — 2 tools remain eager for Trust Class B discovery

## Benchmark Process (Before Enabling Code Mode)

1. Create a disposable canary VK or a temporary runtime config with Code Mode enabled only for the candidate client
2. For each candidate server:
   - Compare: static token count, discovery success, call success, latency, result quality
   - Run 5-10 representative test calls in classic and Code Mode
   - Only enable if materially better on context/cost AND equal/better on correctness
3. Document results in `audits/bifrost/CODE_MODE_BENCHMARK_<date>.md`

## Enabling Code Mode

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

Registry per-client flag:

```json
"is_code_mode_client": true
```

Binding level `tool` is preferred for large catalogs; `server` remains a valid Bifrost option when a whole client should bind as one VFS unit.

## VK Permission Enforcement

Virtual-key permissions are still enforced inside Code Mode. A VK that doesn't have access to a tool in classic mode also cannot access it in Code Mode.

`tools_to_auto_execute` is empty for these clients. Code Mode makes permitted tools executable through `executeToolCode`; it does not authorize automatic execution.

## 2026-09-08 expansion notes

- Operator decision: Cursor is sole primary owner of the Bifrost MCP contract plane; Codex reviews/challenges only.
- Expansion acceptance evidence: `audits/bifrost/CODE_MODE_GLOBAL_ENABLE_2026-09-08.md`
- Do not enable postgres / sqlite / sheets / drive / sendgrid / firebase / github as part of this expansion.
