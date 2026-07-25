# Bifrost Code Mode Runbook

**Authority:** `renderers/bifrost/config.json` (mcp.tool_manager_config)  
**Updated:** 2026-07-24  
**Current State:** Binding level `server` (Bifrost default; set in config.db)

## What is Code Mode

Code Mode exposes a virtual file system (VFS) of tool definitions through four meta-tools:
- `listToolFiles` — list available tool definition files
- `readToolFile` — read a specific tool definition
- `getToolDocs` — get documentation for a tool
- `executeToolCode` — execute tool code

This can reduce context usage for large-catalog servers.

## Current Config

No `code_mode_binding_level` is set in config.json (runtime uses Bifrost default).
The Bifrost log shows: `code mode binding level: server`

## Servers That Must Remain in Classic Mode (Core Direct)

- agentcore_memory — stable 10-tool surface; no context savings needed
- agentcore_project_router — 4 tools; no context savings needed
- sequential_thinking — 1 tool; no context savings needed
- skills_hub — 3 tools; no context savings needed

## Benchmark Process (Before Enabling Code Mode)

1. Create a disposable canary VK with Code Mode enabled
2. For each candidate server (depwire, playwright, tentra, arabold_docs, filesystem):
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
