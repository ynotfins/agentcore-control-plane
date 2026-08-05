# Bifrost Code Mode Runbook

> **TASK-SPECIFIC RUNBOOK — EXCLUDED FROM DEFAULT PROJECT SOURCES.** Code Mode is a task-specific VFS meta-tool feature of Bifrost. Excluded from default ChatGPT Project Sources unless a Code Mode workstream is explicitly active.

**Authority:** `renderers/bifrost/config.json` (mcp.tool_manager_config)  
**Updated:** 2026-08-05
**Current State:** Binding level `server` is rendered explicitly. Code Mode is enabled only for named heavy global clients in `contracts/bifrost-upstream-mcp-registry.json`.

## What is Code Mode

Code Mode exposes a virtual file system (VFS) of tool definitions through four meta-tools:
- `listToolFiles` — list available tool definition files
- `readToolFile` — read a specific tool definition
- `getToolDocs` — get documentation for a tool
- `executeToolCode` — execute tool code

This can reduce context usage for large-catalog servers. Bifrost's current documentation says Code Mode is configured per MCP client with `is_code_mode_client: true`, while `code_mode_binding_level` is a global organization setting for the virtual file system.

## Current Config

`code_mode_binding_level` is rendered as `server`.

Enabled Code Mode clients:

- `arabold_docs` — documentation/search client with a 10-tool global surface
- `playwright` — browser automation client with a 22-tool default allowlist

Classic clients:

- `agentcore_memory`
- `agentcore_project_router`
- `cursor_agent_mcp`
- `sequential_thinking`
- `skills_hub`

## Servers That Must Remain in Classic Mode (Core Direct)

- agentcore_memory — stable 10-tool surface; no context savings needed
- agentcore_project_router — 4 tools; no context savings needed
- cursor_agent_mcp — subagent controls should remain directly discoverable
- sequential_thinking — 1 tool; no context savings needed
- skills_hub — 3 tools; no context savings needed

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
      "code_mode_binding_level": "server"
    }
  }
}
```

For tool-level binding (large catalogs like Tentra):
```json
"code_mode_binding_level": "tool"
```

## VK Permission Enforcement

Virtual-key permissions are still enforced inside Code Mode. A VK that doesn't have access to a tool in classic mode also cannot access it in Code Mode.
