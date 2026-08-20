# Zed and Zoo-Code AgentCore Enrollment Evidence

Date: 2026-08-20
Operator task: configure Zed and Zoo-Code for the AgentCore workflow, register Zoo-Code in AgentCore source, and enroll both clients to the single `agentcore-gateway` MCP route.

## Scope

- Zed native client: installed version `1.16.1`.
- Zoo-Code: installed as Cursor/Open VSX extension `zoocodeorganization.zoo-code-3.79.100391-universal`.
- Gateway endpoint: `http://127.0.0.1:8080/mcp`.
- Secret handling: the live configs contain a materialized bearer copied from Windows User `BIFROST_MCP_VIRTUAL_KEY`; no resolved secret is stored in source-controlled templates.

## Boundary Finding

Zoo-Code is documented as a VS Code/Open VSX extension. It was found installed under Cursor extension storage on this host, and no official Zed extension compatibility path was identified. Zed was configured through Zed's native `context_servers` MCP support. Zoo-Code was configured through its own Cursor globalStorage MCP settings.

## Backup Evidence

Backup root: `E:\LocalApps\Backups\Zed-ZooCode\20260820-130809`

Backed up before live mutation:

- `Zed.settings.json`
- `Zed.AGENTS.md`
- `ZooCode.mcp_settings.json`

## Live Config Evidence

Zed settings path:

- `C:\Users\ynotf\AppData\Roaming\Zed\settings.json`
- SHA256: `A7EB4DD68F77DA5524F1F6F8DB45C79D67616C82C61EC40B49DBF144C5E5239B`
- `context_servers`: `agentcore-gateway`
- `agentcore-gateway.url`: `http://127.0.0.1:8080/mcp`
- `Authorization` header present: yes
- default provider: `openrouter`
- default model: `minimax/minimax-m3`
- available OpenRouter models: `minimax/minimax-m3`, `deepseek/deepseek-v4-pro-0813`
- Added profile: `agentcore-gateway`, with only `agentcore-gateway` enabled for context servers.

Zed global rules path:

- `C:\Users\ynotf\AppData\Roaming\Zed\AGENTS.md`
- SHA256: `93BE836623197D365D8C008A8340C35AF019BAAE8701D331630631AC19BAA003`
- Source: `ide-profiles/zed/GLOBAL_RULES.md`

Zoo-Code MCP path:

- `C:\Users\ynotf\AppData\Roaming\Cursor\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json`
- SHA256: `2FE77599F4E8AC38CDC5C7F452F5E2923E7B615E84BFCC6C645313FD1FCDA7A2`
- `mcpServers`: `agentcore-gateway`
- `agentcore-gateway.url`: `http://127.0.0.1:8080/mcp`
- `disabled`: false
- `timeout`: 300
- `Authorization` header present: yes

## Validation Evidence

Passed:

- Live Zed settings JSON parsed successfully.
- Live Zoo-Code MCP JSON parsed successfully.
- Zed live config contains exactly one AgentCore MCP entry: `agentcore-gateway`.
- Zoo-Code live config contains exactly one AgentCore MCP entry: `agentcore-gateway`.
- `python scripts\render_ide_rules.py --check`: `OK: all IDE GLOBAL_RULES.md renderings current`.
- `python scripts\bifrost\validate_client_status.py`: `OK: all client-status semantic/temporal checks passed`.
- `ops\bifrost\Test-AgentCoreBifrostGateway.ps1` live checks:
  - TCP `127.0.0.1:8080` listening.
  - `/health` returned HTTP 200.
  - `BIFROST_MCP_VIRTUAL_KEY` present.
  - authenticated MCP `initialize` succeeded.
  - authenticated MCP `tools/list` returned 34 tools.
  - forbidden MCP tool patterns absent: `swarm`, `postgres`, `psql`, `whole_drive`, `bifrost_admin`.

Known failing inherited validator:

- `python scripts\bifrost\validate_contracts.py`: fails because registry server `morph-mcp` has no entry in `contracts/mcp-tool-output-schemas.json`.
- `python scripts\bifrost\test_contracts.py`: `PASS 172 checks`, `FAIL 1 checks`, same inherited output-schema coverage category.
- `ops\bifrost\Test-AgentCoreBifrostGateway.ps1`: overall result failed only because it invokes `validate_contracts.py`; live gateway smoke checks listed above passed.

## Remaining Risk

- I did not close or restart active Zed/Cursor windows. Use a fresh Zed Agent thread and a fresh Zoo-Code task for activation proof.
- Zoo-Code provider/account state appears to be stored by the extension/Cursor UI. Existing Zoo task history showed `Zoo Gateway`, but no Windows User `ZOO_CODE_API_KEY`, `ZOOCODE_API_KEY`, or `ZOO_API_KEY` was present.
- No paid Zoo-Code performance benchmark was executed in this run. The next proof should time a small Zoo-Code task and confirm AgentCore gateway tools are visible inside the task.
