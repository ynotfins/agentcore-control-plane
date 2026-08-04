# Documentation Read Order (Every Agent, Every Managed Project)

**Authority:** `PROJECT_ANCHOR.md` §0.1 → this policy. Machine-readable: `contracts/project-execution-policy.json`.

Hardcoded read sequence for a managed project:

1. Global `PROJECT_ANCHOR.md` and `DOC_AUTHORITY.md` (in `D:\github\agentcore-control-plane`)
2. Global `BLUEPRINT.md` and current `CONTEXT_BLOCK.md`
3. Global agent policy (`docs/agent-policy/` in the control-plane repo)
4. Project `AGENTS.md` and `CLAUDE.md`
5. `<project>/.agentcore/PROJECT_CHARTER.md`
6. `<project>/.agentcore/MILESTONES.md`
7. Current Milestone file and checklist (`.agentcore/milestones/M<n>-*.md`, `.agentcore/checklists/state.json`)
8. `<project>/.agentcore/TOOL_MANIFEST.yaml`
9. Project state and decisions (`.agentcore/PROJECT_STATE.json`, `.agentcore/DECISIONS.md` when present)
10. Manifests and lockfiles (package.json/lock, pyproject/uv.lock, etc.)
11. Context Fabric current state (capture/drift)
12. Arabold exact-version docs index (`.agentcore/docs/DOCS_INDEX.md` or project equivalent)
13. Relevant implementation files

Rules:

- Agents must **not** load every historical document automatically. Historical/superseded documents (per `DOC_AUTHORITY.md` classification and in-file banners) are read only when a specific fact requires them.
- For control-plane memory/database work, the additional authority chain is `CONTEXT_BLOCK.md` → `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`. Historical implementation handoffs are consulted only for a specifically cited evidence question.
- Machine facts (hardware, drives, installed software) come from `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md`, never from ad-hoc memory.
- When authoring **Cursor prompts** that list authority or evidence files, write each path as `@` + full absolute Windows path (for example `@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`, `@C:\Users\ynotf\.cursor\plans\<plan>.plan.md`). Do not use shortened relative paths. If further Cursor work remains, end with a ready-to-paste `CURSOR CONTINUATION PROMPT` section.
