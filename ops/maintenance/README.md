# ops/maintenance

Rescue, repair, and one-off maintenance work for the workstation. Each subdirectory is a self-contained incident with its own README, snapshots, and rollback instructions.

Conventions:

- Directory name: `<topic>-YYYYMMDD-HHMM` (operator-local 24h time). Use `codex-rescue-20260724-0144` as the canonical example.
- Always snapshot first; never edit a live client config without a timestamped rollback copy.
- Every rescue directory must contain a `README.md` with: TL;DR, root cause, the change (diff), what was preserved, verification evidence, side issues found, and a recovery / rollback section.
- Use `mavis-trash` (not `rm`/`Remove-Item`) for any deletes.

## Index

| Incident | When | Outcome |
|---|---|---|
| [`codex-rescue-20260724-0144/`](./codex-rescue-20260724-0144/) | 2026-07-24 01:44 EDT | Codex CLI 0.137.0 config was failing to load due to `model_providers.custom.wire_api = "chat"`; flipped to `responses`. **All 360 chat sessions preserved, all MCP servers healthy.** |
