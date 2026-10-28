# Open Design control-plane enrollment

Date: 2026-10-26
Approval: AUTH-2026-10-26-OPEN-DESIGN-ENROLLMENT
Project key: `open-design`
Source root: `D:\open-design`

This file is evidence for a control-plane admission plus a narrow Cursor host-native MCP exception. Open Design stays a desktop product. AgentCore does not host its memory, database, or MCP server.

## Decision

Open Design is an AgentCore-enrolled project at the exact path `D:\open-design` (RGDS package / this Cursor folder). It is not a Bifrost upstream. It is not Trust Class A. It is not attached to AgentCore PG18, SwarmRecall, SwarmVault, or SwarmClaw.

Durable Open Design product data remains under `%AppData%\Roaming\Open Design\namespaces\release-stable-win\data`. That path is **not** enrolled.

## Storage

- Enrolled source: `D:\open-design` only
- Product data: `%AppData%\Roaming\Open Design\namespaces\release-stable-win\data` (not enrolled)
- Installer: `%LocalAppData%\Programs\Open Design` (not enrolled)
- Do not enroll AppData, the install folder, or create `I:\LocalApps\OpenDesign` in this task

## Database

No PG18 database, role, extension, or SwarmRecall path. Open Design local memory stays on disk in the product data folder. AgentCore memory, if used later, is only `agentcore-gateway` → `agentcore-memory` against this enrolled root.

## Gateway

No Bifrost capability profile. No `open-design` server in `contracts/bifrost-upstream-mcp-registry.json`. IDEs keep one AgentCore entry: `agentcore-gateway`.

## Cursor-only Open Design MCP exception

Official Open Design docs require copying the in-app generated MCP launch snippet into the target agent (`Settings → OpenDesign MCP`). Bifrost cannot replace that product MCP (it exposes the live Open Design project, not AgentCore tools).

AUTH grants a **host-native companion** in Cursor only:

- Name: `open-design`
- Transport: stdio via the generated absolute `Open Design.exe` + `ELECTRON_RUN_AS_NODE` + `daemon-cli.mjs mcp` (never a bare `od` command)
- Scope: Open Design project/design tools only
- Proof of parity gap: product MCP is unavailable through Bifrost; attaching it as an upstream would put a desktop-session server behind the machine gateway
- Does not duplicate AgentCore memory, database, Swarm, admin, or registry routes
- Desktop app must be running
- Other IDEs stay unattached until a later AUTH

Rollback: restore `C:\Users\ynotf\.cursor\mcp.json` from the timestamped backup created at attach time. Remove only the `open-design` key.

## Plugins and skills

Official marketplace only. Community marketplace stays restricted. This task does not import extra community plugins. The desktop 0.26.1 bundled official catalog remains the capability set.

## Validation

- Enrollment contract: `project_key=open-design`, paths=`D:\open-design` only
- Live `require_enrolled_path(D:\open-design)` returns `open-design`; AppData and install paths return none
- `scripts/test_open_design_enrollment.py`: 3 passed
- `scripts/bifrost/validate_contracts.py` / `test_contracts.py` still fail on pre-existing raven-branch schema/profile gaps (not introduced here); enrollment check itself is default-deny + unique paths
- Tracked-source secret scan: no keys in Git; Cursor MCP still uses `${env:BIFROST_MCP_VIRTUAL_KEY}`
- Rollback copy: `.agentcore/rollback/20261026-open-design-enrollment/`
- Cursor attach backup: `C:\Users\ynotf\.cursor\mcp.json.bak-opend-design-20261026`
- Live Bifrost apply/restart: not required
- Official plugins: 465 bundled; community marketplace remains restricted; none added
- Desktop 0.26.1 running; default design system `user:rgds` published; local memory on

## Not done in this task

- Bifrost profile or live gateway restart
- PG18 changes
- Claude / Codex / other IDE MCP attach
- Community plugin import
- Unlock edits to `CONTEXT_BLOCK.md` / `AGENTS.md` (proposal only)
