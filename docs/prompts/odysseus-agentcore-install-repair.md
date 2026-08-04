# Odysseus AgentCore Install Repair Prompt

```text
ODYSSEUS INSTALL REPAIR - READ ONLY FIRST

Goal:
Straighten out Odysseus so it follows AgentCore PC install policy without attaching it directly to AgentCore, Swarm, or neutral SwarmRecall databases.

Known project root from prior read-only check:
@D:\odysseus

Known current state from prior read-only check:
- Git project root: D:\odysseus
- Branch: dev
- Remote: https://github.com/odysseus-dev/odysseus.git
- Existing uncommitted files: app.py, launch-windows.ps1, setup.py
- The app has a web UI.
- It previously appeared to inherit a non-Odysseus DATABASE_URL and tried to use an AgentCore/SwarmRecall-looking database path.

Work from:
@D:\github\agentcore-control-plane

Read first:
@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
@D:\github\agentcore-control-plane\DOC_AUTHORITY.md
@D:\github\agentcore-control-plane\docs\install-platform\INSTALLATION_POLICY.md
@D:\github\agentcore-control-plane\docs\install-platform\INSTALL_NEW_THING.md
@D:\github\agentcore-control-plane\docs\install-platform\SCENARIO_CATALOG.yaml
@D:\github\agentcore-control-plane\contracts\install-target-policy.json
@D:\github\agentcore-control-plane\contracts\agentcore-project-enrollment.json

Rules:
1. Start read-only. Do not edit, install, migrate, delete, create a service, or commit until the plan is approved.
2. Prove the Odysseus project root with git -C D:\odysseus rev-parse --show-toplevel.
3. Inventory current Odysseus storage behavior and inspect app.py, launch-windows.ps1, setup.py, config files, and docs for DATABASE_URL, SQLite, Chroma, vector stores, cache, log, upload, and data paths.
4. Do not use any inherited global DATABASE_URL for Odysseus.
5. Do not attach Odysseus directly to AgentCore PG18, legacy PG16, neutral SwarmRecall PG/Meili, SwarmVault, or Swarm-owned databases.
6. No Odysseus durable DB/vector/index/app data on C: or D:.
7. Target durable Odysseus data root: I:\LocalApps\Odysseus.
8. Target Odysseus backup root: E:\LocalApps\Backups\Odysseus.
9. If upstream requires D:\odysseus\data, propose backing it up and replacing it with an NTFS junction to I:\LocalApps\Odysseus\data.
10. If Odysseus should become AgentCore-managed, add D:\odysseus to contracts/agentcore-project-enrollment.json only after explicit approval.
11. If AGENTS.md or CLAUDE.md are missing in D:\odysseus and the project is approved for AgentCore continuity, create them at the Odysseus project root using the AgentCore root rules template from MASTER_CONFIG_AND_PROMPT.md.
12. Do not push to the upstream Odysseus remote unless ownership/remote policy is explicitly approved.

Required output before mutation:
- confirmed project root
- current dirty Git state
- current storage/database behavior
- proposed I:\LocalApps\Odysseus layout
- backup and rollback plan
- AGENTS.md / CLAUDE.md decision
- AgentCore enrollment decision
- exact files that would change
- validation checks
- commands pending approval
```
