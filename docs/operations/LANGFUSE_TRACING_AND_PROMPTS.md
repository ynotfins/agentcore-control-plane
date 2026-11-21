# Langfuse Tracing & Prompt Management

**Status:** READY — operator opt-in for M6 workflow + Deep Agents workers.

**Authority:** Langfuse docs ([tracing](https://langfuse.com/docs/observability/get-started), [prompts](https://langfuse.com/docs/prompt-management/get-started)), [Langfuse agent skill](https://github.com/langfuse/skills) (installed at `.agents/skills/langfuse`).

Langfuse is **separate from LangSmith**. Studio still forces `LANGSMITH_TRACING=false` by default. Langfuse export requires an explicit operator flag.

---

## 1. Prerequisites

1. Create a [Langfuse Cloud](https://langfuse.com/cloud) project (or self-host Langfuse).
2. Create a project API key pair in **Settings → API Keys**.
3. Set Windows **User-scope** environment variables (never commit `.env` files):

| Variable | Required | Example value (region-specific) |
|---|---|---|
| `LANGFUSE_PUBLIC_KEY` | yes | `pk-lf-...` |
| `LANGFUSE_SECRET_KEY` | yes | `sk-lf-...` |
| `LANGFUSE_BASE_URL` | yes | `https://cloud.langfuse.com` (EU), `https://us.cloud.langfuse.com` (US) |
| `AGENTCORE_LANGFUSE_TRACING` | for tracing | `true` |
| `AGENTCORE_LANGFUSE_PROMPTS` | for remote prompts | `true` |

PowerShell (User scope):

```powershell
[Environment]::SetEnvironmentVariable("LANGFUSE_PUBLIC_KEY", "pk-lf-...", "User")
[Environment]::SetEnvironmentVariable("LANGFUSE_SECRET_KEY", "sk-lf-...", "User")
[Environment]::SetEnvironmentVariable("LANGFUSE_BASE_URL", "https://cloud.langfuse.com", "User")
[Environment]::SetEnvironmentVariable("AGENTCORE_LANGFUSE_TRACING", "true", "User")
[Environment]::SetEnvironmentVariable("AGENTCORE_LANGFUSE_PROMPTS", "true", "User")
```

Restart terminals/IDEs after setting User env vars.

---

## 2. Install dependency

From `D:\github\agentcore-control-plane`:

```powershell
pip install -r scripts\agentcore_workflow\requirements.txt
```

Package: `langfuse==4.14.2` (LangChain/LangGraph `CallbackHandler` integration).

---

## 3. Tracing (observability)

**Integration:** `scripts/agentcore_workflow/langfuse_integration.py` + `workflow.py` + `deepagents_worker.py`.

When `AGENTCORE_LANGFUSE_TRACING=true` and Langfuse credentials are present:

- M6 `run_workflow()` wraps each run in an `agentcore-workflow-run` span.
- LangGraph `graph.invoke()` receives a Langfuse `CallbackHandler`.
- Deep Agents builder/critic invocations are traced as nested runs (`agentcore-da-builder`, `agentcore-da-critic`).
- Trace attributes: `session_id=thread_uuid`, `user_id=project_id`, tags `agentcore`, `m6-workflow`, milestone key.

**Verify:** run a workflow, then open the Langfuse **Traces** view for the project.

```powershell
python -m agentcore workflow start --project-key <key> --goal "langfuse tracing smoke"
```

---

## 4. Prompt management

### Bootstrap prompts (one-time per Langfuse project)

Uploads `agentcore-da-builder` and `agentcore-da-critic` text prompts with `production` label:

```powershell
python scripts\agentcore_workflow\langfuse_bootstrap_prompts.py
python scripts\agentcore_workflow\langfuse_bootstrap_prompts.py --dry-run
```

### Runtime behavior

When `AGENTCORE_LANGFUSE_PROMPTS=true`:

- Builder/critic system prompts are fetched from Langfuse (`label=production`) and compiled with `{{worktree}}`, `{{agentcore_context}}`, `{{task}}`, `{{rubric_section}}`.
- If fetch fails, embedded fallback templates in `langfuse_integration.py` are used (behavior unchanged).

When prompts + tracing are both enabled, `propagate_attributes(prompt=...)` links prompt versions to generations.

**Prompts:**

| Name | Type | Variables |
|---|---|---|
| `agentcore-da-builder` | text | `worktree`, `agentcore_context`, `task` |
| `agentcore-da-critic` | text | `worktree`, `agentcore_context`, `task`, `rubric_section` |

Edit prompts in the Langfuse UI; promote versions with the `production` label to roll out changes without redeploying code.

---

## 5. Langfuse agent skill

Installed for Cursor via:

```powershell
npx skills add langfuse/skills --skill "langfuse" --agent "cursor"
```

Local copy: `.agents/skills/langfuse/`. Use for CLI access (`npx langfuse-cli api ...`), doc lookup, and prompt migration guidance.

---

## 6. Privacy posture

| System | Default | Override |
|---|---|---|
| LangSmith (Studio) | `LANGSMITH_TRACING=false` | `--allow-dangerous-langsmith-tracing` |
| Langfuse (M6) | off (`AGENTCORE_LANGFUSE_TRACING` unset) | set flag + credentials |

Langfuse traces may contain prompts, tool I/O, and file paths from worker runs. Enable only when the operator accepts export to the configured Langfuse project/region.

---

## 7. Files

| File | Role |
|---|---|
| `scripts/agentcore_workflow/langfuse_integration.py` | Credentials gate, callbacks, prompt compile, bootstrap |
| `scripts/agentcore_workflow/langfuse_bootstrap_prompts.py` | Upload prompts to Langfuse |
| `scripts/agentcore_workflow/workflow.py` | Workflow-level tracing wrapper |
| `scripts/agentcore_workflow/deepagents_worker.py` | Worker prompts + nested tracing |
| `.agents/skills/langfuse/` | Langfuse agent skill (Cursor) |
