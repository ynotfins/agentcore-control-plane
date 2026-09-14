# Devin signed memory Approach A (2026-09-14)

Evidence only. Not an authority document. device_assertion, replay, and exact-path enrollment are unchanged.

## What shipped

Host-owned signer/client at `scripts/agentcore_devin/signed_memory.py` reuses the Cursor `DeviceIdentityManager` enrollment (`device.json` + keyring). Devin stays Trust Class A on `http://127.0.0.1:18082/mcp` with no stored builder bearer.

## Invoke

From repo root:

```text
scripts\.venv\Scripts\python.exe scripts\devin_signed_memory.py sign --tool session_open --project-key nfa-platform --project-root "D:\agentcore-worktrees\nfa-platform\goal-staging-001"
```

`sign` prints short-lived signed tool arguments for Devin to pass through headerless `:18082`. `call` runs on the host (in-process memory server, or `--via-gateway` on `:8080` with User-env VK). Host call refuses `:18082` plus a helper-owned bearer.

## Proof

See `scripts/agentcore_devin/tests/test_signed_memory.py`.

| Case | Expected |
| --- | --- |
| Unsigned `session_open` | `device_assertion_required` |
| Signed Approach A + enrolled goal-staging-001 | verify accepts / call_tool reaches session_open |
| Replay same assertion | `device_assertion_replay` |
| Assertion `project_key` mismatch | `device_assertion_project_mismatch` |

## Not changed

- `match_enrolled_path` remains exact equality. New Goal Mode worktrees still need a separate Cursor enroll (Task 2).
- Devin MCP JSON was not edited.
- No operator, project-router, or enrollment-edit rights were granted.

## Rollback

`.agentcore/rollback/20260914-003000-devin-signed-memory/`