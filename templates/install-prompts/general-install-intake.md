# General Install Intake Prompt

```text
INSTALL INTAKE - READ ONLY FIRST

I am about to install or configure:
Name: <APP / TOOL / REPO>
Source URL or installer: <URL / COMMAND / PATH>
Purpose: <WHY THIS IS BEING INSTALLED>
Expected runtime/UI: <DESKTOP / WEB UI / CLI / SERVICE / MCP>
Expected database/vector store/cache: <YES / NO / UNKNOWN>
Expected MCP exposure: <YES / NO / UNKNOWN>
Expected AgentCore project continuity: <YES / NO / UNKNOWN>

Work from @D:\github\agentcore-control-plane.

Before changing anything, read:
@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
@D:\github\agentcore-control-plane\DOC_AUTHORITY.md
@D:\github\agentcore-control-plane\docs\install-platform\INSTALLATION_POLICY.md
@D:\github\agentcore-control-plane\docs\install-platform\INSTALL_NEW_THING.md
@D:\github\agentcore-control-plane\docs\install-platform\SCENARIO_CATALOG.yaml
@D:\github\agentcore-control-plane\contracts\install-target-policy.json

Rules:
1. Do not install, migrate, create services, edit configs, register MCP, or create databases until the plan is approved.
2. No durable databases, vector stores, app data, runtime state, or persistent caches on C: or D:.
3. Third-party local app data defaults to I:\LocalApps\<AppName>.
4. Third-party local app backups default to E:\LocalApps\Backups\<AppName>.
5. Source repos may live on D:\github or another approved source root.
6. Do not attach third-party apps directly to AgentCore PG18, legacy PG16, neutral SwarmRecall, SwarmVault, or Swarm-owned databases.
7. AgentCore memory integration is only agentcore-gateway -> agentcore-memory.
8. MCP exposure goes through the governed Bifrost/AgentCore path only after approval.
9. Secrets use Windows User-scope environment variables only.
10. If this becomes an enrolled project repo, create or update project-root AGENTS.md and CLAUDE.md.

Output the plan with:
- project/app root
- scenario classification
- source location
- data/database/vector/index location
- backup location
- runtime/log/cache location
- MCP exposure decision
- AgentCore project continuity decision
- secrets/env vars
- rollback plan
- validation checks
- commands pending approval
```
