# Eigent AgentCore Enrollment Evidence — 2026-08-20

## Scope

Live repair/enrollment of Eigent IDE 1.0.2 on this PC into the AgentCore non-Swarm baseline.

## Changed live state

- Live MCP config: `C:\Users\ynotf\.eigent\mcp.json`
- Previous live MCP backup: `E:\LocalApps\Backups\Eigent\20260820-124311\mcp.json`
- Backup SHA-256: `9A7ED3AF3B50D02725233A425068D5AF43443AADF21838930CD2A4C6DAD76823`
- New live MCP SHA-256: `9B9058ECDF873BACB2DD5601AE0B06388FDD2DC68B4258D5E829511682D3DC33`
- Live MCP server count after repair: `1`
- Live MCP server name: `agentcore-gateway`
- Live MCP URL: `http://127.0.0.1:8080/mcp`
- Live MCP timeout: `300`
- Auth handling: bearer value materialized only in live Eigent config from Windows User env `BIFROST_MCP_VIRTUAL_KEY`; value not recorded here.

## Pre-repair findings

- `BIFROST_MCP_VIRTUAL_KEY`, `OPENROUTER_API_KEY`, and `MINIMAX_API_KEY` were present in Windows User env; values were not printed.
- Eigent was running version `1.0.2`.
- The previous `C:\Users\ynotf\.eigent\mcp.json` contained multiple direct MCP servers instead of the AgentCore single-gateway baseline.
- Recent Eigent backend failure was model budget related: `Budget has been exceeded! Current cost: 3.918838, Max budget: 3.5`.
- The failure path used CAMEL `DeepSeekModel` with `deepseek-v4-pro`, not the intended OpenRouter model path.

## Validation

- AgentCore Bifrost health: `GET http://127.0.0.1:8080/health` returned `status=ok`, `db_pings=ok`.
- Bifrost authenticated MCP `tools/list`: passed via `ops\bifrost\Test-AgentCoreBifrostGateway.ps1`; returned 34 tools.
- Repository validator status: inherited non-Eigent contract/schema failures remain in the dirty worktree (`devin_mcp_json`, `opencode_jsonc`, `zoo_code_mcp_json`, and missing output schema for `morph-mcp`). Live gateway checks inside the same validator passed.
- Eigent restarted after MCP change.
- Eigent backend health: `GET http://127.0.0.1:5001/health` returned `status=ok`, `service=eigent`.
- Eigent backend MCP list: `GET http://127.0.0.1:5001/mcp/list` returned exactly one server, `agentcore-gateway`, with auth present and redacted.
- Eigent CAMEL runtime MCPToolkit connected using the live config and returned 34 tools. Sample tools included `agentcore_memory-memory_status`, `agentcore_memory-startup_context`, `agentcore_memory-retrieve_context`, and `agentcore_memory-append_event`.
- OpenRouter model catalog confirmed current preferred model `deepseek/deepseek-v4-pro-0813`; old `deepseek/deepseek-v4-pro` is the 0423 model.
- Direct OpenRouter probe for `deepseek/deepseek-v4-pro-0813`: returned `OK`, model `deepseek/deepseek-v4-pro-0813`.
- Direct OpenRouter probe for `minimax/minimax-m3`: returned `OK`, model `minimax/minimax-m3`.
- Eigent `/model/validate` for `openrouter` + `deepseek/deepseek-v4-pro-0813` with strict OpenAI-compatible params passed all stages, including tool call execution.
- Eigent `/model/validate` for `openrouter` + `minimax/minimax-m3` with strict OpenAI-compatible params passed all stages, including tool call execution.

## Runtime notes

- Do not put OpenRouter-specific request fields such as `reasoning` in Eigent Model Parameters JSON. Eigent 1.0.2 passes `model_config_dict` through the OpenAI SDK path and rejects unsupported kwargs.
- Safe Model Parameters JSON for Eigent OpenRouter provider validation:

```json
{
  "temperature": 0,
  "max_tokens": 1024
}
```

- Preferred model ID for Eigent OpenRouter provider: `deepseek/deepseek-v4-pro-0813`.
- Fallback model ID for Eigent OpenRouter provider: `minimax/minimax-m3`.

## Remaining risk

- I did not directly mutate opaque UI/cloud provider-card state. The backend validator proves the correct provider/model tuple works when the UI sends it.
- Eigent's app UI may still show an old provider/model selection if its provider card is persisted in remote account state. If so, set Provider `OpenRouter`, Model `deepseek/deepseek-v4-pro-0813`, API base `https://openrouter.ai/api/v1`, and the safe Model Parameters JSON above.
- Full AgentCore native memory lifecycle validation steps 6-18 in `ide-profiles/eigent/VALIDATION.md` were not completed; this was a live MCP/provider repair, not a full lifecycle certification.
