# Agent Orchestrator (AO) — Operations Runbook

**Product Version:** `0.10.3`  
**CLI Signature:** `ao version dev`  
**Status:** FULLY CONFIGURED AND PATH BLOCKERS RESOLVED  
**Updated:** 2026-07-19

---

## 1. Product Characteristics & Location

Agent Orchestrator (AO) is a lightweight process and worktree orchestrator. It does not possess its own database or manage its own LLM provider contracts directly. Instead, it relies on system-level child agents (harnesses) and system-scope environment variables.

### 1.1 Executable Paths and PATH Status
- **Authoritative CLI Daemon Path:** `C:\Program Files\agent-orchestrator\resources\daemon\ao.exe`
- **PATH Status:** `RESOLVED`. The daemon directory `C:\Program Files\agent-orchestrator\resources\daemon` has been registered in the Windows User-scope environment PATH.
- **GUI Application Path:** `C:\Program Files\agent-orchestrator\agent-orchestrator.exe`

### 1.2 Configuration Paths
- **Application Configuration Root:** `C:\Users\ynotf\.ao`
- **Application State Tracking File:** `C:\Users\ynotf\.ao\app-state.json`

---

## 2. Integrated Child Agents (Harnesses)

AO manages tasks by launching specialized CLI agents inside isolated Git worktrees. Supported harnesses include:
- `claude-code` (Claude Code)
- `codex` (Open Interpreter)
- `aider` (Aider)
- `opencode`, `grok`, `droid`, `cursor`, etc.

### 2.1 The Codex Harness (Open Interpreter) Integration
The primary integration path for OpenRouter-backed model execution is the `codex` harness, which launches the local Open Interpreter.
- **System-Scope Configuration:** The system-wide Open Interpreter configuration (`C:\Users\ynotf\AppData\Roaming\interpreter\`) is pre-loaded with:
  - `autonomous-os` (default): minimax/minimax-m3 (OpenRouter)
  - `autonomous-gpt-sol`: openai/gpt-5.6-sol (OpenRouter)
  - `autonomous-minimax-m27`: minimax/minimax-m2.7 (OpenRouter)
  - `autonomous-free`: google/gemma-4-31b-it:free (OpenRouter - zero cost)
- **Environment Inheritance:** Child agents launched by AO automatically inherit the Windows environment variables `%OPENROUTER_API_KEY%` and `%BIFROST_MCP_VIRTUAL_KEY%`.
- **Memory Integration:** Open Interpreter connects to `agentcore-gateway` on the system-wide MCP registry, ensuring all spawned AO tasks write their trace events and memory snapshots directly into the canonical PostgreSQL 18 memory tables.

---

## 3. Operations Manual

### 3.1 Managing Projects
Projects must be registered as local Git repositories before sessions can be spawned.
```powershell
# List registered projects
ao project ls

# Add a project
ao project add --path "D:\github\<project-name>" --name "<display-name>"

# Remove a project (use -y to skip prompt)
ao project rm <project-id> -y
```

### 3.2 Spawning and Controlling Sessions
Sessions run in isolated Git worktrees created automatically under `C:\Users\ynotf\.ao\data\worktrees\<project-id>\`.
```powershell
# Spawn a Codex (Open Interpreter) worker session with a prompt
ao spawn --project <project-id> --harness codex --name "fix-issue" --prompt "Add error handling to db.py"

# List active sessions
ao session ls

# Terminate/kill an active session
ao session kill <session-id>

# Clean up terminated sessions from worktree storage
ao session cleanup
```

---

## 4. Smoke Test Validation Summary

An isolated smoke test was successfully executed on a disposable scratch drive (`I:`) with these results:
1. **Creation:** A temporary Git repo was created at `I:\disposable-ao-project` and added to AO via `ao project add`.
2. **Execution:** An active session `disposable-ao-project-1` was spawned using the `codex` harness with the zero-cost profile (`autonomous-free`).
3. **Isolation:** The worktree was created cleanly under `C:\Users\ynotf\.ao\data\worktrees\disposable-ao-project\disposable-ao-project-1\` without affecting the production repository.
4. **Cleanup:** The session was terminated via `ao session kill`, the project removed with `ao project rm -y`, and the temporary folder on `I:\` removed cleanly.
