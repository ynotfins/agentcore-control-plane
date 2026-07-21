# Continual-Learning Automation Trace (2026-07-20)

## Mystery prompt (operator did not type)

```text
Run the `continual-learning` skill now. Use the `agents-memory-updater` subagent...
```

## Exact source

| Field | Value |
| --- | --- |
| Product | Cursor official plugin **continual-learning** v1.0.0 |
| Cache path | `C:\Users\ynotf\.cursor\plugins\cache\cursor-public\continual-learning\3fe2823ce17c1656c222d4b7c59d3f82fbf20143\` |
| Hook config | `hooks/hooks.json` → event **`stop`** |
| Hook script | `hooks/continual-learning-stop.ts` |
| Mechanism | On cadence match, prints JSON `{ "followup_message": "<prompt>" }` which Cursor injects as a **user-role** follow-up |
| Skill | `skills/continual-learning/SKILL.md` (`disable-model-invocation: true`) |
| Subagent | `agents/agents-memory-updater.md` |
| Index file | `.cursor/hooks/state/continual-learning-index.json` |
| Cadence state | `.cursor/hooks/state/continual-learning.json` |
| Project hooks.json | **Absent** (plugin hooks, not project hooks) |
| Global hooks.json | **Absent** |

### Original hashes (pre-disable)

| File | SHA-256 |
| --- | --- |
| `continual-learning-stop.ts` | `39DAE32343BB752DC045668592B02576A90A38FD526DC48DB97C857CC31BBBCA` |
| `hooks.json` | `844C6BD8C5AA28D6E28068BE1F17CDE4DDE4ABFC368C201305DC967E67AD7154` |

Preserved copies:

- `E:\AgentCore-Backups\cherry-runtime-repair-20260720-202353\continual-learning-plugin-original\`
- `audits/_preserved/continual-learning-plugin-20260720/`

### Provenance

- Author: Cursor (`plugins@cursor.com`), MIT, homepage `https://github.com/cursor/plugins`
- Not introduced by an AgentCore commit; installed as a Cursor marketplace/plugin cache artifact
- Observed auto-injection in transcripts e.g. `7b7c8766-...` (2026-07-20 ~19:39) and earlier `7fd962ba-...` (2026-07-19)

### Behavior summary

| Question | Answer |
| --- | --- |
| Can it create a user-role message? | **Yes** — via `followup_message` |
| Cadence | Default ≥10 completed turns AND ≥120 minutes since last run AND transcript mtime advanced; trial mode tighter |
| Recursive? | Partially guarded by `lastProcessedGenerationId`; follow-up itself can count as a turn |
| Writes | Intended: `AGENTS.md` Learned sections + index/state under `.cursor/hooks/state/` |
| Network/model | Indirect — parent agent + `agents-memory-updater` subagent may call models |
| Secrets | Skill text says exclude secrets; still scans transcripts (risk if secrets present) |
| Source-controlled? | Index/state partially; plugin lives in Cursor cache (not this repo) |

## Temporary disable (2026-07-20)

- Replaced live `continual-learning-stop.ts` with a no-op that always emits `{}` (never `followup_message`).
- Marker: `.cursor/hooks/CONTINUAL_LEARNING_AUTO_TRIGGER_DISABLED.md`
- Originals preserved (not deleted).

## AgentCore alignment disposition

**Action: disable automatic trigger; adapt useful capture later under AgentCore memory.**

Approved target flow is documented in `docs/operations/AGENTCORE_CONTINUAL_LEARNING.md`:

- No silent user-role impersonation
- No automatic AGENTS.md personal-fact edits
- Durable facts → `agentcore-memory` (`append_event` / `propose_fact`) with trust review
- AGENTS.md only for explicit operating-contract / operator-approved governance

Project helper retained (manual / evidence-only):

- `.cursor/hooks/update-continual-learning-index.ps1` — rebuilds index metadata; does not inject prompts
