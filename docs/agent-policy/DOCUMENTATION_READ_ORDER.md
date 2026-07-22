# Documentation Read Order (Every Agent, Every Managed Project)

**Authority:** `PROJECT_ANCHOR.md` §0.1 → this policy. Machine-readable: `contracts/project-execution-policy.json`.

Hardcoded read sequence for a managed project:

1. Global `PROJECT_ANCHOR.md` and `DOC_AUTHORITY.md` (in `D:\github\agentcore-control-plane`)
2. Global agent policy (`docs/agent-policy/` in the control-plane repo)
3. Project `AGENTS.md` and `CLAUDE.md`
4. `<project>/.agentcore/PROJECT_CHARTER.md`
5. `<project>/.agentcore/MILESTONES.md`
6. Current Milestone file and checklist (`.agentcore/milestones/M<n>-*.md`, `.agentcore/checklists/state.json`)
7. `<project>/.agentcore/TOOL_MANIFEST.yaml`
8. Project state and decisions (`.agentcore/PROJECT_STATE.json`, `.agentcore/DECISIONS.md` when present)
9. Manifests and lockfiles (package.json/lock, pyproject/uv.lock, etc.)
10. Context Fabric current state (capture/drift)
11. Arabold exact-version docs index (`.agentcore/docs/DOCS_INDEX.md` or project equivalent)
12. Relevant implementation files

Rules:

- Agents must **not** load every historical document automatically. Historical/superseded documents (per `DOC_AUTHORITY.md` classification and in-file banners) are read only when a specific fact requires them.
- For control-plane memory/database work, the additional authority chain applies: `CONTEXT_BLOCK.md` → `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` → `docs/handoffs/MEMORY_PLATFORM_IMPLEMENTATION_HANDOFF_2026-07-14.md`.
- Machine facts (hardware, drives, installed software) come from `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md`, never from ad-hoc memory.
- When authoring **Cursor prompts** that list authority or evidence files, write each path as `@` + full absolute Windows path (for example `@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`, `@C:\Users\ynotf\.cursor\plans\<plan>.plan.md`). Do not use shortened relative paths. If further Cursor work remains, end with a ready-to-paste `CURSOR CONTINUATION PROMPT` section.
