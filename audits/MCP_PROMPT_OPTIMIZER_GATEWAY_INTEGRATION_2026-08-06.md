# MCP Prompt Optimizer Gateway Integration - 2026-08-06

## Scope

Register `mcp-prompt-optimizer` once behind `agentcore-gateway` so Cursor and other AgentCore-enrolled IDEs keep the single MCP endpoint.

## Installed Source

- Source: `D:\github\vendor\mcp-prompt-optimizer`
- Upstream: `https://github.com/Bubobot-Team/mcp-prompt-optimizer`
- Commit: `317e83a1685253085972dcb60b60618362c19182`
- Runtime launch: `uv run --no-project --directory D:\github\vendor\mcp-prompt-optimizer --with mcp==0.9.1 python prompt_optimizer.py`

## AgentCore Wiring

- Cursor global MCP restored to gateway-only at `C:\Users\ynotf\.cursor\mcp.json`.
- Bifrost registry server: `mcp-prompt-optimizer`
- Bifrost client name: `mcp_prompt_optimizer`
- Capability profile: `builder`
- Tool exposure: exact named allowlist only.
- Secrets: none.
- Durable database/app data: none.
- Swarm dependency: none.

## Tools Exposed

- `analyze_prompt`
- `optimize_prompt`
- `auto_optimize`
- `get_prompt_template`
- `advanced_optimize`
- `get_domain_template`
- `list_domain_templates`

## Compatibility Finding

The upstream Git package build path is not usable as-is:

- `uv run --from git+https://github.com/Bubobot-Team/mcp-prompt-optimizer mcp-prompt-optimizer` fails because setuptools rejects the flat module layout.
- Current `mcp` 2.x is incompatible with upstream's `Server.list_tools` decorator API.
- Pinning `mcp==0.9.1` and launching `prompt_optimizer.py` directly works.

## Rollback

1. Set `contracts/bifrost-upstream-mcp-registry.json` server `mcp-prompt-optimizer.enabled=false`.
2. Remove `mcp-prompt-optimizer` from `capability_profiles.builder.allowed_server_ids`.
3. Re-render with `python scripts\bifrost\render_bifrost_config.py`.
4. Restart Bifrost with repo-owned ops scripts.
5. Cursor remains gateway-only.

Runtime config backup before render:

`E:\AgentCore\Backups\bifrost-config\20260806-020843-mcp-prompt-optimizer`

## Validation

- `python scripts\bifrost\validate_contracts.py` - PASS
- `python scripts\bifrost\validate_output_schemas.py` - PASS offline contract/render gates
- `ops\bifrost\Test-AgentCoreBifrostGateway.ps1` - PASS
- Direct stdio MCP tools/list through pinned runtime - PASS, 7 expected tools
- Live gateway tools/list - PASS, `mcp_prompt_optimizer-*` tools visible
- Live gateway tool call - PASS, `mcp_prompt_optimizer-analyze_prompt` returned prompt analysis

## Residual

`python scripts\bifrost\validate_output_schemas.py --probe-gateway` still reports missing live `outputSchema` for all gateway tools, including pre-existing AgentCore tools. This is not specific to `mcp-prompt-optimizer`; the offline contract/render gates pass.
