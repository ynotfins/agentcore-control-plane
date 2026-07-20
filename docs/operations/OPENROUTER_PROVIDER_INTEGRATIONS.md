# OpenRouter Provider Integrations

**Authority:** `contracts/openrouter-provider-contract.json`  
**Status:** FULLY INTEGRATED AND SELECTABLE  
**Updated:** 2026-07-19

---

## 1. Overview and System Architecture

This runbook defines the OpenRouter API integrations for all five AgentCore runtimes. It enforces the **Default-Provider Preservation Policy** to ensure that OpenRouter remains opt-in and selectable, except for Open Interpreter where it is the default provider.

### Distinction: OpenRouter API vs. OpenRouter MCP

These are two entirely separate systems governed by distinct rules:
- **OpenRouter API (Inference):** Used for model execution across runtimes. Access is authenticated via `OPENROUTER_API_KEY` stored in Windows User-scope environment variables.
- **OpenRouter MCP (Metadata/Governance):** Supplies model catalog, pricing, and documentation to IDEs through the central `agentcore-gateway` (Bifrost). It uses OAuth 2.1 + PKCE via Bifrost's `config.db` and is never used for normal inference. No direct OpenRouter MCP entries are added to any IDE.

---

## 2. Central OpenRouter Provider Contract

The central contract is stored at `contracts/openrouter-provider-contract.json` (source-controlled, no secrets):

```json
{
  "provider_id": "openrouter",
  "api_base": "https://openrouter.ai/api/v1",
  "api_key_env": "OPENROUTER_API_KEY",
  "models": [
    "minimax/minimax-m3",
    "deepseek/deepseek-v4-pro",
    "openai/gpt-5.6-sol",
    "minimax/minimax-m2.7"
  ],
  "default_for": {
    "open-interpreter": "only"
  },
  "selectable_for": [
    "langgraph",
    "langgraph-studio",
    "cherry-studio",
    "agent-orchestrator"
  ],
  "automatic_fallback": false,
  "auto-routing": false,
  "secret_storage": "Windows User env or supported encrypted app store",
  "logging": {
    "never_log_prompts_by_default": true,
    "never_log_api_keys": true,
    "record_provider_model_cost_metadata_only": true
  },
  "memory": {
    "record_accepted_provider_model_selection_through_agentcore": true
  },
  "trust": {
    "external_model_output_is_evidence_not_authority": true
  }
}
```

---

## 3. Runtime Integration Specifications

### 3.1 Open Interpreter (Codex)
- **Posture:** OpenRouter is the default provider.
- **Primary Model:** `minimax/minimax-m3` (context limit: 1,048,576 tokens).
- **Alternate Profiles:**
  - `autonomous-gpt-sol`: Explicitly selects `openai/gpt-5.6-sol`.
  - `autonomous-minimax-m27`: Explicitly selects `minimax/minimax-m2.7`.
  - `autonomous-free`: Explicitly selects zero-cost fallback model `google/gemma-4-31b-it:free`.
- **API Key Storage:** Loaded from Windows User-scope `%OPENROUTER_API_KEY%`. No keys appear in config files or logs.
- **Memory Integration:** Connects to `agentcore-gateway` (http://127.0.0.1:8080/mcp), exposing exactly ten memory tools. Appends prompt context before execution and resumes the session correctly using `session_key`.

### 3.2 LangGraph Workflows
- **Posture:** OpenRouter is selectable but NOT the default (retains `openai:gpt-4o-mini` default).
- **Execution Syntax:**
  ```powershell
  python -m agentcore workflow start `
    --project D:\github\<target-project> `
    --goal-file D:\path\goal.md `
    --provider openrouter `
    --model minimax/minimax-m3
  ```
- **Constraints:** `--provider openrouter` requires an explicit `--model`. No silent fallback or auto-routing.
- **Model Catalog Command:**
  ```powershell
  python -m agentcore workflow models --provider openrouter
  ```
  This command displays sanitized model catalog details, context limits, and pricing.
- **Persistence:** Provider and model selections are persisted in the workflow's `WorkflowState` and stored in PostgreSQL 18 `wf_runs` checkpoints to survive restart recovery.

### 3.3 LangGraph Studio
- **Posture:** OpenRouter is selectable per thread/run but NOT the default.
- **Configuration:** Reads `OPENROUTER_API_KEY` from the Windows user environment. No `.env` files are created.
- **Topology Parity:** Fingerprint and schema remain identical to production; PostgreSQL 18 persistence is retained.

### 3.4 Cherry Studio
- **Posture:** OpenRouter is selectable but NOT the application-wide default.
- **Verification:**
  - Exactly one `agentcore-gateway` MCP client. No direct OpenRouter MCP client.
  - Cherry Global Memory remains disabled.
  - Assistants (`Cherry Claw` and `Cherry Assistant`) are preserved on their pre-rollout default: `cherryin:agent/deepseek-v4-pro`.
- **Model Enrollment:** The verified OpenRouter models (`minimax/minimax-m3`, `deepseek/deepseek-v4-pro`, `openai/gpt-5.6-sol`, `minimax/minimax-m2.7`) are visible and selectable immediately.

### 3.5 Agent Orchestrator (AO)
- **Posture:** Thin process/worktree orchestrator. Existing default behaviors and child agents (like Claude Code) are preserved on their defaults unless an explicit OpenRouter profile is selected.
- **Integration Route:** Supports spawning the `codex` harness (Open Interpreter) using our OpenRouter-backed profiles. The spawned child processes cleanly inherit `%OPENROUTER_API_KEY%` and connect to the system-wide `%BIFROST_MCP_VIRTUAL_KEY%` to discover memory tools.
- **Harness Placement:** Legitimate `ao` CLI (`C:\Program Files\agent-orchestrator\resources\daemon\ao.exe`) is registered on the user PATH for clean terminal execution.

---

## 4. Cost Controls and Secret Handling

1. **Secret Storage:** All API keys (`OPENROUTER_API_KEY`, `BIFROST_MCP_VIRTUAL_KEY`, `BIFROST_ENCRYPTION_KEY`) must reside exclusively in Windows User-scope environment variables. Never print, log, or commit secret values.
2. **Spending Caps:**
   - OpenRouter MCP OAuth is initiated with a deliberately low spending cap ($10 default) to prevent runaway costs during model discovery.
   - Run-level limits and token boundaries are recorded and enforced.
3. **No Unapproved Paid Calls:** Free models (e.g., `google/gemma-4-31b-it:free`) are utilized for automated verification. Paid inference is strictly blocked unless explicit operator cost approval is granted.

---

## 5. Rollback and Deactivation

### Deactivating OpenRouter API Selectability

1. **Open Interpreter:**
   Restore previous default profile by copying the backup:
   ```powershell
   Copy-Item "C:\Users\ynotf\AppData\Roaming\interpreter\profiles\autonomous-os.yaml.backup" "C:\Users\ynotf\AppData\Roaming\interpreter\profiles\default.yaml" -Force
   ```
2. **LangGraph:**
   Remove `--provider openrouter` from launcher parameters.
3. **Cherry Studio:**
   Deactivate or delete the OpenRouter provider in the settings UI. Ensure assistants are assigned to `cherryin:agent/deepseek-v4-pro`.
4. **Agent Orchestrator:**
   Kill any active `disposable-ao-project` sessions and clean up local scratch directories.
