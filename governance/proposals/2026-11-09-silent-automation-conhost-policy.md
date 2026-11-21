# Proposal: AgentCore silent automation (conhost headless mandate)

**Date:** 2026-11-09  
**Status:** PROPOSED — repo artifacts live; governed AGENTS.md / authority wording unchanged until UNLOCK path  
**AUTH id:** `AUTH-2026-11-09-SILENT-AUTOMATION-CONHOST`  
**Capability:** `authority_maintainer` (implementation in `agentcore-control-plane`; operator applies via Paperclip / ops scripts)

## Problem

ChaosCentral runs many logon and repeating Windows scheduled tasks for Bifrost, NFA edge health, backups, and local services. When tasks invoke **PowerShell directly** (`pwsh.exe` / `powershell.exe` as the task `Execute` target) or rely on the **default console host** (Windows Terminal / visible `conhost` without `--headless`), scheduled work **steals focus**: consoles flash, taskbar entries appear, and the operator's active IDE session is interrupted dozens of times per day.

`-WindowStyle Hidden` on a direct `pwsh.exe` action is **not sufficient**; Task Scheduler still materializes a visible hosting path in common configurations. The regressions are operational noise and trust erosion, not functional failures — but they block uninterrupted IDE work.

## Desired state

All **covered** shell-backed scheduled tasks (name patterns in the contract) must use a single silent action shape:

| Layer | Requirement |
| --- | --- |
| **Execute** | `conhost.exe` |
| **Arguments (lead)** | `--headless` then embedded `pwsh.exe` (or `powershell.exe` where required) |
| **Pwsh tokens** | `-NoProfile`, `-NonInteractive`, `-WindowStyle Hidden`, `-ExecutionPolicy Bypass`, then `-File "..."` or inline script |
| **Task settings** | `Hidden = true` on the scheduled task **and** headless conhost wrapper — **both** required |

Non-shell actions (e.g. `cloudflared.exe`, `wscript.exe`) remain allowed as listed in the contract without a conhost wrapper.

**Direct `pwsh.exe` / `powershell.exe` as task Execute = FAIL** (validator and repair scripts treat this as regression).

## Machine-readable contract

**Authority:** `contracts/agentcore-silent-automation-policy.json`

- `silent_action_shape`: conhost + `--headless` + pwsh hidden-window tokens  
- `name_match_patterns`: `AgentCore`, `NFA-`, `OmniRoute`, `Paperclip`, `OpenClaw`, `ZooCode`, `Reasonix`, `DailyDrift`, `SwarmRecall`, `Nightly`, …  
- `tasks[]`: per-task file paths, `repair.make_silent_allowed` / `disable_allowed`, critical flags  
- `audit_log_path`: `I:/LocalApps/Paperclip/logs/automation-board-audit.log`

Installers and repair logic must read this contract; hardcoded task lists outside the contract are drift.

## Install, repair, and disable

| Script | Role |
| --- | --- |
| `ops/Install-AgentCoreSilentAutomationPolicy.ps1` | Idempotent apply: backup task XML, rewrite covered tasks to contract shape, register validator hook, export catalog evidence |
| `ops/Repair-AgentCoreSilentAutomationTask.ps1` | Targeted repair for one enrolled task name (operator or Paperclip board) |
| `ops/Disable-AgentCoreNoisyAutomationTask.ps1` | Disable-only path when `make_silent_allowed` is false (e.g. legacy `DailyDriftCheck`) |

Shared helpers: `ops/AgentCoreSilentAutomation.Common.ps1` (`Get-AgentCoreSilentPolicyContract`, `Test-AgentCoreTaskIsSilent`, audit writer).

## Validator (acceptance gate)

**Script:** `ops/bifrost/Test-AgentCoreSilentAutomationTasks.ps1`

- Enumerates **enabled** scheduled tasks matching `name_match_patterns`  
- **PASS:** `Settings.Hidden` **and** action `Execute` = `conhost.exe` with `--headless` and pwsh chain including `-WindowStyle Hidden`  
- **FAIL examples:**  
  - Direct `pwsh.exe` / `powershell.exe` as Execute (focus-stealing host)  
  - `conhost.exe` without `--headless`  
  - `Hidden` task setting without conhost headless shell action  
  - **`-WindowStyle Hidden` alone** on a direct pwsh task (no conhost headless) — treated as FAIL, not pass  

Exit `0` = pass; exit `1` = regression list for operator repair.

## Operator UI (Paperclip)

- **Plugin:** `agentcore.automation-board` (`plugins/paperclip-automation-board`)  
- **Surface:** Paperclip local at `http://127.0.0.1:3100` → sidebar **Automations**  
- **Actions:** catalog view, "Make silent" (repair), "Disable noisy" where policy allows; audit lines append to contract `audit_log_path`  
- Scheduled task `Paperclip-Local-3100` is in-scope for silent shape like other AgentCore logon services.

## Installer alignment (Bifrost / Serena)

Bifrost and Serena session shim **installers must emit conhost headless** task actions when they register or refresh scheduled tasks — not raw `pwsh.exe` Execute:

- `ops/bifrost/Install-AgentCoreBifrostGateway.ps1`  
- `ops/bifrost/Install-AgentCoreSerenaSessionShim.ps1`  

New or re-run installs should converge to the contract without a separate manual repair pass.

## Applied / in-repo artifacts (reference)

- `contracts/agentcore-silent-automation-policy.json`  
- `ops/Install-AgentCoreSilentAutomationPolicy.ps1`  
- `ops/Repair-AgentCoreSilentAutomationTask.ps1`  
- `ops/Disable-AgentCoreNoisyAutomationTask.ps1`  
- `ops/AgentCoreSilentAutomation.Common.ps1`  
- `ops/bifrost/Test-AgentCoreSilentAutomationTasks.ps1`  
- `ops/Export-AgentCoreScheduledTaskCatalog.ps1`  
- `plugins/paperclip-automation-board/`  

## Non-goals

- **No Stage B weakening** — Cursor hooks, enrollment, and device assertion remain unchanged; silent automation is Task Scheduler presentation only.  
- **Keep critical watchdogs running** — `AgentCore-Bifrost-Watchdog`, `NFA-*` watchdog/restart tasks, and OmniRoute poll tasks stay **enabled**; policy makes them silent, not disabled (except explicit `disable_allowed` legacy cases).  
- **No Bifrost contract-plane ownership change** — Cursor sole-primary Bifrost MCP rule (2026-09-08) unchanged.  
- **No operator requirement to edit task XML by hand** — repair/install scripts and Paperclip board own convergence.

## Proposed authority sync (protected — proposal only)

When UNLOCK allows, mirror a short bullet under workstation automation / ops policy: covered AgentCore and NFA scheduled shell tasks use `conhost.exe --headless` + Hidden settings per `contracts/agentcore-silent-automation-policy.json`; `WindowStyle Hidden` without conhost headless is insufficient.
