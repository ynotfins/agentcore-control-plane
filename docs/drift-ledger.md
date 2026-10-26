# Documentation drift ledger

## 2026-10-21 — G: second-copy headroom

- **Cleared (normal_workstream):** retention policy, backup/PITR runbook, drive-write boundary, global agent rules, automation ops, database overview WAL note, M8 lifecycle registry.
- **Open governed/locked:** `contracts/global-agent-policy.yaml` still lacks the 75%/8 GB G: headroom sentence now in `docs/GLOBAL_AGENT_RULES.md`. Requires AUTH / documentation maintainer.
- **Outside worktree:** `D:\postgreSQL18-control-plane\DATABASE.md` §6 still says only “second copy on G:” with no headroom rule.

## 2026-10-25 — governed-doc-drift: MiniMax MCP connect timeout unit (milliseconds)

- **ID:** `governed-doc-drift-2026-10-25-minimax-mcp-timeout-ms`
- **Class:** `governed_mutable` (`contracts/authority-lock.yaml`)
- **File:** `MASTER_CONFIG_AND_PROMPT.md`
- **Section:** §9 “Exact gateway contract and host-native exceptions”
- **Current:** `- Timeout: 300 seconds` (`MASTER_CONFIG_AND_PROMPT.md:324`)
- **Proposed:** `- Timeout: 300 seconds for hosts that read the field in seconds; MiniMax Code reads the MCP server timeout field in milliseconds and requires 300000 ms (contracts/agentcore-gateway-client.json → client_render_hints.minimax.connect_timeout_ms)`
- **Source:** `renderers/gateway-clients/minimax.json:6` (`timeout: 300000`), `ide-profiles/minimax/MCP_CONFIG_TEMPLATE.json:6` (`timeout: 300000`), `ops/bifrost/Reconcile-AgentCoreTrustAClients.ps1:321` (`$gateway.timeout = 300000`), `contracts/agentcore-gateway-client.json` (`client_render_hints.minimax.connect_timeout_ms: 300000`), live effective file `C:\Users\ynotf\.minimax\mcp.json` (`timeout: 300000`)
- **Why it matters:** the generic line still reads as “300 for every client”. MiniMax Code reads the MCP server timeout field in milliseconds, so it needs 300000 ms rather than a seconds-denominated 300; the other Trust Class A clients genuinely read the field in seconds and must keep 300. The agent-turn discovery path caps HTTP connects at 2000 ms regardless of this value, so the timeout governs the uncapped settings-panel path only.
- **Cleared (normal_workflow):** `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` — MiniMax canonical config block and Supported IDE Matrix timeout cell now state `timeout: 300000` (milliseconds).
- **Requires:** authority_maintainer + AUTH id + rollback + validators + independent review
- **Status:** OPEN — operator adjudication deferred by the caller on 2026-10-25. The proposal is accurate and independently verified, but `MASTER_CONFIG_AND_PROMPT.md` is `governed_mutable` and carries unrelated in-flight edits from another session; applying it inside this change would bundle that work into a governed commit. The entry is retained as the durable escalation record. Memory proposal `NOT_AVAILABLE` (the AgentCore memory gateway was not reachable from the docs-guardian session).
