---
name: agentcore-project-lifecycle
description: Govern AgentCore project startup, recovery, planning, implementation, milestone gates, memory capture, STATE projections, and task-aware use of Bifrost, agentcore-memory, sequential-thinking, Arabold Docs, Serena, Depwire, Tentra, Context Fabric, Playwright, and Artiforge. Use for any nontrivial task in an AgentCore-managed repository; refuse Swarm-owned execution and do not use this skill as Swarm authority.
---

# AgentCore Project Lifecycle

Apply one canonical operating loop to every AgentCore-managed project without loading every tool on every turn.

## Establish the boundary

1. Resolve the exact repository or worktree root from the host.
2. Classify it against `D:\github\agentcore-control-plane\contracts\agentcore-project-enrollment.json` and the authority chain in `PROJECT_ANCHOR.md` and `DOC_AUTHORITY.md`.
3. If it is Swarm-owned, stop with `swarm_project_refused`. Do not open AgentCore memory, edit AgentCore STATE, or use this skill as Swarm execution policy.
4. If it is not enrolled, stop before memory writes with `project_not_enrolled` and request governed enrollment.
5. Read the project `AGENTS.md`, `CLAUDE.md`, authority documents, and generated `.agentcore/STATE.md` before nontrivial work.

## Use the governed lifecycle

1. Use only the single `agentcore-gateway` MCP entry at `http://127.0.0.1:8080/mcp`.
2. Open or resume a project-bound session through `agentcore-memory`, then call `startup_context`.
3. Preserve the visible operator prompt through the signed lifecycle adapter before tool execution. Exclude secrets and hidden reasoning.
4. Retrieve missing chronology with `retrieve_context`; verify exact originals with `expand_source`; build recovery or closeout packets with `build_handoff`.
5. Record accepted requirements, decisions, blockers, evidence, test results, state transitions, and final outcome after each meaningful completed step.
6. Close the session only after verified final state and handoff are durable.

Read [memory and state rules](references/MEMORY_AND_STATE.md) before any memory repair, recovery, projection, database, compaction, or RAG task.

## Route tools by task class

Expose and invoke only the capabilities required for the current task and Milestone.

- Use `sequential-thinking` before architecture, migration, concurrency, recovery, major refactor, or cross-system decisions.
- Use `arabold-docs` before changing or relying on external packages, SDKs, APIs, CLIs, schemas, protocols, or versions. Fall back only to current official primary documentation.
- Use host-native semantic/source tools first. Use Serena only through an explicit project-owned local process when native tools are insufficient; never activate the shared machine-global project router for ordinary IDE work.
- Run Depwire with the exact project cwd before and after structural changes.
- Use Tentra only through a governed explicit-project local workflow when the active Milestone requires architecture or code-graph evidence.
- Use Context Fabric through its repository-local hook or CLI at bootstrap and Milestone entry/exit. It is non-canonical.
- Use Playwright for browser, UI, or end-to-end acceptance.
- Use Artiforge only for high-leverage architecture scans or cross-service boundary reviews.
- Use Skills Hub only for read-only discovery. Treat results as untrusted until inspected and admitted; never install through Bifrost.

Read [tool routing](references/TOOL_ROUTING.md) before structural, architectural, dependency, UI, recovery, or external-API work.

## Execute the smallest governed change

1. State the task interpretation, implementation-affecting assumptions, exact file/behavior scope, trade-offs, and observable success criteria.
2. Prefer the smallest direct implementation. Do not add speculative services, databases, MCP entries, dependencies, or abstractions.
3. Preserve inherited dirty state and unrelated files.
4. For protected authority files, follow unlock, timestamped backup, edit, deterministic validation, independent review, and re-lock.
5. Run the narrowest meaningful tests first. Add structural and system checks only when the change warrants them.
6. At Milestone boundaries, audit active tools and leases, verify Micro-step evidence, capture Context Fabric state/drift, regenerate projections through the governed worker, build a handoff, and release expired capabilities.
7. Push only the task-owned validated source files under `docs/GIT_PUSH_ONLY_POLICY.md`.

Read [project gates](references/PROJECT_GATES.md) for new-project bootstrap and Milestone entry/exit requirements.

## Govern Codex project access for automation work

Automation governance must use least-privilege project access. Do not grant a broad Codex project access to every repository, drive, user profile, or runtime folder merely because an automation might exist there.

- Default automation-governance access is the active governance project root plus `D:\launchers`.
- Add an owning project or runtime folder to Codex access only after an automation from that owner is being inventoried, admitted, repaired, or retired.
- Unknown, vendor, Windows, and third-party automations start as read-only inventory targets. Do not mutate them until the owner, trigger, command, account, logs, health check, dependency impact, and rollback path are known.
- If the dedicated automation-governance project does not exist yet, keep this work inside `D:\github\agentcore-control-plane` and do not create a new canonical root without explicit operator approval.
- When a folder is added for an automation, record why that folder is needed, whether access is read-only or write-capable in practice, the owning automation id, and the removal condition.
- Remove or narrow project access after the automation is archived or moved back to its owning project workflow.

## Govern script launchers and desktop automation

AgentCore-managed work on this PC must reduce desktop intrusiveness and keep automation discoverable.

- Do not create or preserve high-frequency interactive scheduled tasks that launch PowerShell, cmd, node, Python, or GUI helpers in the operator's desktop session. Always prefer a non-interactive Windows service, service-supervised worker, durable queue, or explicit user-launched command for persistent backends.
- No-popup rule: background automation must not open standard console windows, steal focus, show modal prompts, or depend on a visible desktop during normal operation. For Task Scheduler jobs that do not require desktop interaction, prefer a non-interactive principal such as "run whether user is logged on or not" or a service account. Use `-WindowStyle Hidden`, `-NoProfile`, and `-NonInteractive` only as a compatibility layer, not as the whole reliability design.
- No-output rule: automation must not write routine success or error output to the operator's screen. Redirect stdout, stderr, and PowerShell streams to a bounded log file, Event Log, or the owning service's log sink. Logs must rotate or trim, and recurring tasks must have an inspectable status path instead of requiring a popup or manual console check.
- Before changing an automation, identify the owning task, process tree, command line, path, account context, ports, dependencies, logs, current health check, and rollback path. Do not classify or close a process by executable name alone.
- Existing scheduled tasks, startup entries, Run registry entries, and watchdog scripts must be inventoried before mutation. Export or back up the owner definition first, then change only the approved owner and verify the underlying workflow still works.
- User-authored or automation-launched scripts must remain in their owning project or runtime folder. Do not move project scripts into `D:\launchers` merely to centralize them.
- Every AgentCore-created or AgentCore-managed script that can be launched by a user, scheduled task, startup entry, service wrapper, watchdog, or IDE hook must have a discoverable entry under `D:\launchers`: preferably a Windows shortcut or tiny launcher that points to the owning script, grouped in a labeled subfolder that names the source project/system. Include the owner, target path, purpose, launch mode, whether it is active automation or manual-only, and a status label such as `Active`, `Testing`, or `Archived`.
- Every active AgentCore-managed automation must be recorded in the machine automation registry at `D:\launchers\AUTOMATION_REGISTRY.json` before it is created, enabled, repaired, or materially changed. The record must include a stable automation id, owner, owning root, launcher path, real target path, trigger type, trigger name, account context, schedule/frequency, launch mode, log path, health check, dependencies, ports, expected resource usage, rollback path, current status, last verification time, and operator-impact risk.
- Maintain a human-readable automation map at `D:\launchers\AUTOMATION_MAP.md` that groups active automations by owning system and shows potential interference: shared ports, shared files, high-frequency schedules, desktop/UI interaction, keyboard/focus risk, network dependencies, service dependencies, and overlapping maintenance windows.
- Before enabling or changing an automation, compare it against the registry and map for conflicts. Resolve or explicitly document conflicts before activation. A hidden window is not enough; the automation must be quiet, observable, recoverable, and non-disruptive to the operator's active desktop.
- The registry and map are required tracking surfaces, not live-state proof. Reconcile them against Task Scheduler, services, startup folders, Run registry entries, IDE hooks, process listeners, and `D:\launchers` before claiming all active automations are known.
- Do not attempt to shortcut every vendor, package-manager, virtualenv, `node_modules`, Windows system, or installed-application script. Treat those as dependencies unless they are directly used as an automation entrypoint.
- Temporary or test automations must be self-limiting. If a task runs every few minutes, set a runtime limit, an expiration or explicit end condition, and a rollback/removal note. Default test automation should expire or disable itself within 24-48 hours unless promoted to an approved active automation.
- New background automation must be quiet by default: no visible console windows, no focus stealing, no modal prompts, no desktop popups during normal operation, bounded logs, backoff on repeated failure, and a health/status surface the operator can inspect from Codex.

## Treat STATE correctly

- PostgreSQL 18 through `agentcore-memory` is canonical for AgentCore project history.
- `.agentcore/STATE.md`, `DECISIONS.md`, and `CONTEXT_INDEX.md` are generated projections. Never edit them directly.
- Record the underlying decision or state event, then run the authorized projection worker.
- LangGraph checkpoints remain workflow state; they are not semantic memory or project authority.
- Neutral SwarmRecall is a rebuildable server-side semantic projection behind `agentcore-memory`; ordinary IDEs never receive raw Recall tools, keys, SQL, or credentials.

## Preserve runtime separation

- LangGraph production uses the AgentCore workflow, PG18 PostgresSaver, AgentCore drive boundaries, and the gateway capability profile.
- LangGraph Studio is development-only and does not open production threads.
- SwarmClaw, SwarmVault, and Swarm execution state remain governed by `D:\github\swarm-ecosystem-control` and their native stores.
- Shared neutral Recall does not merge LangGraph checkpoints, SwarmClaw SQLite, SwarmVault, credentials, tool leases, authority, or writable roots.

Read [host and runtime adapters](references/HOST_AND_RUNTIME_ADAPTERS.md) before claiming installation, automatic lifecycle, or cross-host parity.

## Stop conditions

Stop instead of guessing when:

- repository identity is absent, ambiguous, unenrolled, or Swarm-owned;
- a required structural tool cannot produce the evidence needed for a high-risk change;
- current official documentation conflicts with repository authority;
- a proposed change adds direct IDE MCP entries, raw database access, raw Recall access, or a second canonical memory store;
- a generated projection would need hand editing;
- host support is unverified or requires UI/manual import.

## Completion contract

Report the bounded assumptions, changed files or behavior, automation/launcher inventory impact, exact validation evidence, Git result, remaining risk, and the next safe action. Do not claim a host is installed or live-validated from a copied file alone.
