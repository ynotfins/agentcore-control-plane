# MAF Recall Realignment Status

Status: **COMPLETE_WITH_NONBLOCKING_FOLLOWUPS**

Key decisions are now locked:

- Shared memory/tools policy is **one governed external gateway first**, not “every app must be stripped to one total plugin.”
- **Local Devin** is the default coder execution path. No token is needed for ordinary local use.
- **Devin Outposts** is optional isolation. It does need a token because the control plane is Devin Cloud even when execution lands on your box.
- **Codex** and **Devin** keep temporary direct-helper exceptions for now; they are documented transition exceptions, not silent drift.
- **Open Interpreter Desktop** inherits Codex-backed MCP helpers from the selected Codex profile; treat those as the same Codex transition exception, not a separate OI memory/database route.
- The system is now explicitly aimed at a **high-assistance vibe-coder workflow**: agents should use planning, semantic code understanding, dependency graph tools, and durable rolling context instead of asking the operator to restate long prompts.
- **OpenHands** is the fourth execution runtime and is live as Docker-first Agent Canvas at `http://127.0.0.1:8003/canvas/`, with state on `I:/LocalApps/OpenHands/state` and projects on `D:/OpenHandsProjects`.
- **Azure Foundry cloud** is connected as a provider lane and `DeepSeek-V4-Pro` is deployed as `deepseek-v4-pro`; the MAF host prefers Azure Foundry first and OpenRouter second.
- **Desktop is OneDrive-backed** on this machine and should not be used for active repositories, Docker bind roots, or runtime state. Use `D:/github` or `D:/devin-workspace`.
- Docker VHDX stays on `F:/Docker/wsl`; binds stay under `I:/LocalApps`.

Current follow-ups:

- Foundry Local CLI is not installed yet.
- OpenHands startup assets under `I:/LocalApps/OpenHands` still need materialization once host-path writes are allowed; the live container is already healthy.
- The stale created-only container `openhands-local` still needs removal; do not touch `openhands-local-8003`.
- Targeted Docker removals (`D:/docker/n8n`, `D:/docker/portainer`, old images) were identified but host cleanup was blocked in this session.
- Recall service is healthy through the governed path; the direct `:3300` health path needs the correct route, not a new deployment.

See `scripts/maf_recall/post_build_audit.md` and `audits/MAF_RECALL_REALIGNMENT_AUDIT_2026-08-26.json`.

## Overnight convergence state

Decision: **no direct IDE-to-IDE mesh**. Professional control remains hub-and-spoke:
IDEs and agents use `agentcore-gateway` at `http://127.0.0.1:8080/mcp`, durable memory,
runtime-specific execution layers, and auditable handoffs. Peer IDE links are rejected because
they create hidden authority, unclear memory ownership, and hard-to-debug drift.

Verified runtime evidence:

- `8080`, `55433`, `3300`, `3456`, `65432`, `7700`, and `8003` all accepted TCP connections.
- `OpenHands` returned `200` at `http://127.0.0.1:8003/ready`; Canvas is live at `http://127.0.0.1:8003/canvas/`.
- `OpenHands` container `openhands-local-8003` uses image `ghcr.io/openhands/agent-canvas:1.13.0`, publishes only `127.0.0.1:8003->8000`, and has no `F:/` or `H:/` mounts.
- Docker VHDX remains under `F:/Docker/wsl`; Docker reports the tuned WSL envelope.
- Azure Foundry `DeepSeek-V4-Pro` deployment `deepseek-v4-pro` is `Succeeded` / `Running`.
- The MAF host route plan keeps Bifrost live on `:8080`, rejects direct IDE mesh, and chooses Azure Foundry before OpenRouter.
- Devin filesystem scope is corrected: no global `C:/Users/ynotf/Documents/Codex` filesystem MCP remains; future filesystem access is project-scoped per repo/worktree.
- Project enrollment is clean: `D:/OpenHands` is enrolled, `D:/devin-workspace` and `D:/OpenHandsProjects` are staging/project-parent roots only, and Swarm/runtime roots remain unenrolled.

IDE convergence classification:

- Gateway-only: Cursor, Zoo-Code, Open Interpreter CLI, OpenCode.
- Documented transition exceptions: Codex (`node_repl`, `morph-mcp`, `cheap-workers`, `devin`), Open Interpreter Desktop through Codex profile inheritance, Devin (`github-mcp-server`, `mcp-playwright`).
- Forbidden remains unchanged: raw Recall MCP, direct `:65432` SQL, broad drive-root filesystem MCP, direct OpenRouter MCP baseline outside an approved exception.

Morning checklist:

1. Decide whether to install Foundry Local CLI for the local GPU lane; Azure Foundry cloud is already connected and `DeepSeek-V4-Pro` is deployed.
2. Optionally clean old Docker images/leftovers (`n8n`, `portainer`) in a bounded cleanup pass.
3. Create a selective git commit only for this realignment package and intentional config-template changes; do not commit the whole dirty tree.

Completed after finalizer:

- `I:/LocalApps/OpenHands/docker-compose.yml`, `START_OPENHANDS.md`, and `Start-OpenHands.ps1` exist.
- Stale created-only container `openhands-local` was removed.
- Live `openhands-local-8003` remains healthy at `http://127.0.0.1:8003/canvas/`.
