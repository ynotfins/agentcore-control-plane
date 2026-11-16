# Audit: OpenHands AgentCore enrollment (2026-11-15)

Times are America/New_York (EST).

- Running: uvx `openhands-agent-server==1.59.0` on 127.0.0.1:18000 and `openhands-automation==1.26.1` on 127.0.0.1:18001, both started 2:40 PM. The agent-server REST API answers 401 without the app session key. The key was not extracted.
- Gateway: `settings.json` `agent_settings.mcp_config.agentcore-gateway` points at `http://127.0.0.1:8080/mcp` with an encrypted bearer (pre-existing, kept). The builder surface is 27 tools after PR #17.
- Changes at 4:12 PM, with backups `settings.json.bak-20261115-1612`, `agent-profiles/default.json.bak-20261115-1612` and `config.toml.bak-20261115-1612`:
  - new `profiles/omniroute-*.json` files (env-referenced key, base_url `http://127.0.0.1:20128/v1`)
  - `active_profile=omniroute-default`, with `agent_settings.llm` mirrored from that profile
  - `conversation_settings.confirmation_mode=false`
  - the default agent profile's `llm_profile_ref=omniroute-default`
  - CLI `config.toml` `[llm]` points at OmniRoute and adds `[security] confirmation_mode=false`
- OmniRoute check: combos `default`, `auto`, `agent-glm-5-3`, `fast-glm-5-3-flash`, `review-qwen3-8-max`, `default-deepseek-v4-pro` and `sol-kie-heavy` all returned completions. sol-kie-heavy needs max_tokens of at least 16. Nine providers are active, no circuit breakers are open, and there is no Codex provider.
- Rollback: restore the three `.bak-20261115-1612` files and delete `profiles/omniroute-*.json`.
- Restart required: OpenHands must be restarted to load the file changes. The running GUI may otherwise overwrite them.
