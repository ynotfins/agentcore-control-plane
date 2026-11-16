# Contract proposal (t286u) — do not apply in this change

> Pin correction (2026-11-09, later the same night): the CursorTouch **PyPI package** is `windows-mcp==0.8.8`. The server advertises `serverInfo.version` `4.1.7`, which is not a published package version (`uvx windows-mcp==4.1.7` is unsatisfiable). Live Bifrost `windows_mcp` was delete+recreated with `windows-mcp==0.8.8` because `stdio_config` is immutable after create. File edits to that field are ignored. This proposal does not edit locked contracts.

Locked file (do not edit until Tony/AgentCore accepts this proposal):

`D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json`

Also keep the renderer (`D:\github\agentcore-control-plane\renderers\bifrost\config.json`) in sync by re-running `render_bifrost_config.py` after the contract change. The live runtime file `F:\AgentCore\runtime\bifrost\config.json` was updated directly in t286u because `source_of_truth=config.json` and a restart was required to apply it. A later official render from an un-updated contract will drop these live additions.

## Already true in the live contract, still needed in the file/runtime

- Flip `servers.context7.is_code_mode_client` from `false` to `true`.
- Add `"ide"` to `servers.context7.capability_profiles` (live runtime already grants Context7 to the `ide` VK).
- Note remains valid: `CONTEXT7_API_KEY` is absent from Windows User/Machine env; Context7 stays on the rate-limited free tier until Tony sets that User env var. Keep `env_var_names: ["CONTEXT7_API_KEY"]`.

## Add server: eye2byte

Suggested entry (canonical_id uses a hyphen-less id matching the live Bifrost client name `eye2byte`):

- `canonical_id` / `bifrost_client_name`: `eye2byte`
- `display_name`: Eye2byte desktop perception
- `connection_type`: stdio
- `executable_or_url`: `C:\Users\ynotf\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\Scripts\eye2byte-mcp.exe`
- Launch through the existing output-schema adapter (`--server eye2byte`); adapter fail-opens if the output-schema contract has no family yet.
- `is_code_mode_client`: **false** (interactive desktop tool; eager schemas). Tradeoff: grokbot now sees 20 read-only eye2byte tools in the classic list (context cost) in exchange for lower latency and no Code Mode sandbox around screen tools.
- `write_classification`: `write_capable` (package includes click/type/macros)
- `permitted_tools`: the 62 tools discovered from eye2byte 0.7.0 (see live runtime client, or relist after reconnect)
- `capability_profiles`:
  - `builder`, `ide`, `openclaw`: all 62 tools
  - `grokbot`: read-only observational subset only (cloud-exposed; no click/type/window-move/macros):
    `capture_and_summarize`, `summarize_screenshot`, `get_recent_context`, `get_screen_elements`, `search_context_history`, `get_context_timeline`, `list_windows`, `get_pixel_color`, `get_runtime_capabilities`, `powertoys_status`, `eventghost_status`, `eventghost_get_value`, `eventghost_get_all_values`, `list_macros`, `list_playbooks`, `get_playbook`, `get_events`, `get_event_listeners`, `get_latest_frame`, `get_frame_buffer_status`
- Packaging note: PyPI 0.7.0 is missing `eye2byte_policy.py` (imported by the MCP interaction/desktop modules; not in the sdist RECORD). A local compatibility shim that always allows (`policy_denial_payload` returns `None`) was placed at the 3.12 user site-packages path documented in `ROLLBACK-t286u.md`. Upstream GitHub (`wolverin0/Eye2byte`) returned 404 on 2026-11-09. Prefer an official package fix when one exists.
- Doctor on 2026-11-09 8:57 PM EST: `ok=True`, warnings: missing optional `pyautogui`, EventGhost down, Node-RED down.

## Add server: windows-mcp (CursorTouch)

- `canonical_id`: `windows-mcp`
- `bifrost_client_name`: `windows_mcp`
- Official package: CursorTouch `windows-mcp`, launched `C:\Users\ynotf\.local\bin\uvx.exe --python 3.14 windows-mcp==0.8.8 serve`
- Python 3.14.7 is installed at `C:\Python314\python.exe`. Preflight stdio handshake succeeded: package `windows-mcp==0.8.8` advertises server `windows-mcp` 4.1.7, 21 tools.
- `is_code_mode_client`: **false** (same interactive-desktop reason as eye2byte)
- Tools (package 0.8.8 / server 4.1.7): `ControlStatus`, `App`, `DisplayInventory`, `PowerShell`, `FileSystem`, `Snapshot`, `Screenshot`, `Click`, `Type`, `Scroll`, `Move`, `Shortcut`, `Wait`, `WaitFor`, `Scrape`, `MultiSelect`, `MultiEdit`, `Clipboard`, `Process`, `Notification`, `Registry`
- `capability_profiles`:
  - `builder`, `ide`, `openclaw`: all 21 tools
  - `grokbot` read-only: `ControlStatus`, `DisplayInventory`, `Snapshot`, `Screenshot`, `Scrape`, `Wait`, `WaitFor`
- Do not add a per-client HTTP port; STDIO only, launched by native Windows Bifrost (not Docker).
- Live issue to mention in the contract notes: first post-restart registration hit `context deadline exceeded` after 5 retries (same burst also delayed `figma_framelink_mcp` and `apify_research`). Consider a longer per-client init timeout. A reconnect (not necessarily a full gateway restart) is needed if it is still down.

## Do not add: Open Machine

Do not invent a Windows STDIO command. The credible product is [OpenMachineLabs/openmachine](https://github.com/OpenMachineLabs/openmachine) / [openmachine.app](https://openmachine.app/): a real, maintained MCP machine runtime, but official docs say the current installer targets Apple Silicon macOS and **Windows is not supported**. OpenMachineCore is a different industrial HMI org, not this MCP. Leave it out of the registry until there is an official Windows STDIO server.

## Do not add a second Pi coding-agent MCP

`pi-agents` (`pi_agents`, HTTP `http://127.0.0.1:18091/mcp`, Code Mode ON) is already the governed front door to `@earendil-works/pi-coding-agent@1.4.0`. The contract already forbids sticky host-native STDIO for this engine. Do not expose a second STDIO Pi MCP.

## OpenRouter LLM provider (not the OpenRouter MCP)

Google's claimed governance caps of max tokens 100 / max requests 100 were **not** present in the 8:43 PM EST GitOps file or in the pre-restart `config.db` (`governance_rate_limits` was empty; OpenRouter provider had no `budget_id` / `rate_limit_id` / `network_config`). Default `max_retries` was 0. t286u set `providers.openrouter.network_config.max_retries` to 3 with backoff 500/5000 ms. If the renderer/contract owns provider network_config, add that there too.

The separate **OpenRouter MCP** client (`openrouter`, HTTP) failed to register on restart with `oauth2 token expired` — that is not the LLM provider, and is out of this proposal unless Tony wants a re-auth pass (`Invoke-AgentCoreOpenRouterMcpReauth.ps1` already exists).

## Output-schema contract

Optional follow-up (also locked): add families for `eye2byte` and `windows-mcp` in `contracts/mcp-tool-output-schemas.json`. The adapter already fail-opens to raw passthrough without them.
