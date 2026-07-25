# OpenRouter / OpenAI Provider Repair — DRIFT-06 (Phase 2)

**Date:** 2026-07-24  
**Canonical repo:** `D:\github\agentcore-control-plane`  
**Status:** SOURCE FIXED + OPERATOR ENV ACTION REQUIRED

---

## Fact-based root cause

Bifrost live config (`H:\AgentRuntime\bifrost\config.json`) had a single provider block:

```text
providers.openai.keys[0].value = env.OPENAI_API_KEY
```

Windows User-scope `OPENAI_API_KEY` currently holds an **OpenRouter-style** key (`sk-or-v1…`, length 73).  
`OPENROUTER_API_KEY` is also present and is likewise OpenRouter-style (same length/prefix family).

Bifrost startup therefore calls OpenAI `list-models` with an OpenRouter key and logs:

```text
failed to list models … Incorrect API key provided: sk-or-v1… 
You can find your API key at https://platform.openai.com/account/api-keys.
… falling back onto the static …
```

No secret values were printed or committed during this audit. Prefix/kind classification only.

---

## Assessment of prior assumption

The handoff claim that “an OpenRouter-style key is configured under an openai provider” is **correct**.  
The failure is env-value mismatch, not a missing Bifrost feature.

---

## Source-controlled fix (this phase)

1. `scripts/bifrost/render_bifrost_config.py` now renders **both**:
   - `providers.openai` → `env.OPENAI_API_KEY`
   - `providers.openrouter` → `env.OPENROUTER_API_KEY`
2. `OPENROUTER_API_KEY` added to `SECRET_ENV_NAMES`.
3. Comment in renderer documents the OpenAI-vs-OpenRouter key-shape rule.
4. Re-render + Bifrost restart applied after commit path.

OpenRouter **MCP** remains separate (`servers.openrouter`, registry `dormant`, lease-gated). This repair is the **LLM provider catalog** path only.

---

## Operator action required (Tier 4 — env secret)

Do **not** leave an OpenRouter key in `OPENAI_API_KEY`.

Recommended:

1. Set Windows User `OPENAI_API_KEY` to a real OpenAI platform key (`sk-…` from platform.openai.com), **or** clear it if OpenAI inference via Bifrost is unused.
2. Keep `OPENROUTER_API_KEY` as the OpenRouter key (`sk-or-…`).
3. Open a new PowerShell / restart Bifrost scheduled task so the process inherits updated User env.
4. Confirm startup logs no longer show `Incorrect API key provided: sk-or-v1` under provider `openai`.

This agent did **not** rotate or rewrite User env secrets without explicit operator approval.

---

## Rollback

```powershell
git checkout HEAD~1 -- scripts/bifrost/render_bifrost_config.py
python D:\github\agentcore-control-plane\scripts\bifrost\render_bifrost_config.py
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
```

---

## Related Phase 2 items

- Serena now launches via `ops/bifrost/wrappers/serena-prewarm.js` (startup friction).
- Stale registry `status: disabled` corrected to `active` for enabled foundation servers (arabold-docs, sequential-thinking, cursor-agent-mcp, serena).
- **Rejected** plan suggestion to set `enabled=false` on those servers — that would remove mandatory tools.
