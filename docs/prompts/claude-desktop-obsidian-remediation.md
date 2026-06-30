# Claude Desktop — Obsidian Key Remediation (Adjacent Surface)

> Claude Desktop is an ADJACENT surface, not a first-class managed rollout client. This prompt covers only the Obsidian single-writer/secret-hygiene concern. Do not print secret values.

Context: PC Master Specs flag a historical plaintext Obsidian API key risk in Claude Desktop's config. The P0 audit found `AppData\Roaming\Claude\claude_desktop_config.json` currently contains a preferences blob with **no `mcpServers` and no Obsidian key present** — so no live key was found at audit time. This prompt is preventive.

Inspect (read-only first): `C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json`.

Rules:
1. The active Obsidian vault (`D:\Obsidian\Dungeon Vault`) must be written through the single approved REST/MCP path (`obsidian-vault` MCP → `https://127.0.0.1:27124`) only. No second writer.
2. If an Obsidian plaintext API key is ever present in this config, do NOT print it. Replace it with a Windows environment variable reference and rotate the key at the provider — **operator approval required for rotation**. Report by field/path only.
3. Do not add Claude Desktop to the mandatory MCP rollout. No `.env` files.

Report: whether any Obsidian key is present (yes/no, by field name only), and whether single-writer is preserved. Do not edit without explicit operator approval if a live key is found.
