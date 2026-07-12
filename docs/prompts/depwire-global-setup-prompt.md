# Universal DepWire Setup Prompt — All Managed IDE/Agent Clients

Paste the text below into each IDE/agent client. It is intentionally schema-aware: the receiving agent must discover that client's live MCP format instead of blindly pasting JSON.

```text
Configure this IDE/agent client to use the governed local DepWire MCP integration on CHAOSCENTRAL.

Source authority:
D:\github\agentcore-control-plane

Read first:
- D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
- D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md
- D:\github\agentcore-control-plane\contracts\master-mcp-server-config.json
- D:\github\agentcore-control-plane\rules\global-mcp-routing.md

Important credential fact:
- depwire-cli MCP does NOT consume a DepWire API key or license-key environment variable.
- DepWire Pro uses the VS Code/Cursor extension setting `depwire.licenseKey` only.
- Never copy the Pro license key into an MCP config, prompt, report, log, source file, or .env file.
- For Cursor/VS Code Pro activation, use the command palette action `Depwire: Enter License Key`; report only activated/not activated, never the value.

Safety and merge procedure:
1. Identify this client's actual active MCP config path, schema, and current server set. Do not guess.
2. Create a timestamped backup before editing. Preserve unrelated MCP servers, auth/session/profile state, model settings, context-window settings, approval settings, and desktop/runtime settings.
3. Do not create .env files. Do not print or commit secrets.
4. Check the global install first:
   - expected package: depwire-cli@1.8.2
   - expected launcher: C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd
   - validate with: depwire --version
   If missing or different, install the governed version with `npm install --global depwire-cli@1.8.2`, then re-check the absolute launcher path. Do not use a repository-local install.
5. Set Windows User-scope `DEPWIRE_NO_TELEMETRY=1` if it is not already set. Restart/reload the client after environment or MCP changes.
6. Verify the configured global Git excludes file contains `.depwire/` and `depwire-output.json`; back it up and append those patterns if missing. `connect_repo` creates `.depwire/cache.db` even for read-only graph use.
7. Merge a server named exactly `depwire` using stdio:
   command: C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd
   args: ["mcp"]
   env: DEPWIRE_NO_TELEMETRY=1
   Do not add an API-key/license-key env var.

JSON-family shape (adapt only the outer container to this client's verified schema):
{
  "depwire": {
    "type": "stdio",
    "command": "C:\\Users\\ynotf\\AppData\\Roaming\\npm\\depwire.cmd",
    "args": ["mcp"],
    "env": {
      "DEPWIRE_NO_TELEMETRY": "1"
    }
  }
}

Codex TOML shape:
[mcp_servers.depwire]
command = "C:\\Users\\ynotf\\AppData\\Roaming\\npm\\depwire.cmd"
args = ["mcp"]
startup_timeout_sec = 120.0
tool_timeout_sec = 300.0
required = false
default_tools_approval_mode = "prompt"

[mcp_servers.depwire.env]
DEPWIRE_NO_TELEMETRY = "1"

If the client supports per-tool approval policy, allow read-only graph queries without repeated prompts and keep these write-capable/side-effect-capable tools on prompt:
- connect_repo (can clone/pull when given a remote URL)
- visualize_graph
- update_project_docs
- claim_files
- release_files
- record_decision

Install/enforce these global DepWire rules in this client's durable global instruction/rules surface:
- DepWire complements Serena: use Serena for semantic symbol navigation and targeted edits; use DepWire for deterministic dependency edges, blast radius, structural simulation, verification, architecture health, and graph-aware security.
- Connect DepWire only to the verified local repository root. Never pass a GitHub/remote URL or allow clone/pull/fetch unless the operator explicitly authorizes that remote operation.
- For a significant repo task, connect the local repo once and request `get_architecture_summary`; then use targeted graph queries instead of repeatedly dumping the whole graph.
- Before deleting, renaming, moving, splitting, or merging files/symbols—or before a risky multi-file refactor—run `impact_analysis` and, where supported, `simulate_change`.
- Before completion of a structural change, run `verify_change`; run the repo's native tests/build/lint as well because DepWire does not replace project validation.
- Use `security_scan` for security-sensitive changes and when graph reachability materially changes risk. Treat results as findings to verify, not permission to rewrite unrelated code.
- Do not call `update_project_docs`, `visualize_graph`, or coordination/decision tools unless the task needs their side effects and the user has authorized repository mutation.
- Keep the entire `.depwire/` directory and `depwire-output.json` ignored globally. Release file claims when work ends.
- Do not use DepWire `record_decision` as the normal durable memory path and do not dual-write decisions already governed by AgentCore memory/RAG policy.
- Treat `.depwire/cache.db`, generated docs, temporal output, claims, and decisions as local runtime state. Never commit them. For a very large repository, check cache disk impact and task scope before a full graph build.
- Keep `DEPWIRE_NO_TELEMETRY=1`. Do not use DepWire cloud repo connections for governed local source unless explicitly approved.

Validation required before reporting success:
1. Parse the resulting JSON/TOML with the client's native parser or CLI.
2. Confirm registration: server name `depwire`, absolute launcher, args `["mcp"]`, telemetry disabled, no key literal.
3. Confirm protocol handshake: `initialize` succeeds and `tools/list` exposes 23 tools, including `connect_repo`, `impact_analysis`, `simulate_change`, `security_scan`, and `verify_change`.
4. After restart/reload, prove live adoption in a fresh session. Registration alone is not live-tool proof.
5. Run a read-only smoke against the current verified local repo: connect local path, get architecture summary, and perform one targeted dependency/impact query. The ignored `.depwire/cache.db` created by `connect_repo` is expected local runtime state; do not generate docs, claims, decisions, or visualizations during the smoke.
6. For Cursor/VS Code only, report whether the extension Pro license is activated; do not expose the license value. This is separate from MCP readiness.

Final report must include:
- detected client and active config path
- backup path
- package version and launcher path
- server added/updated and preserved settings
- telemetry setting status
- MCP registration result
- handshake/tool count and required-tool presence
- read-only smoke result
- Pro extension activation status if applicable (status only)
- restart/reload performed or still required
- exact blockers and rollback path
```
