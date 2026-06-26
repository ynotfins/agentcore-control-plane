# AgentCore Env Policy Audit

Run this audit daily and after any config, renderer, validator, gateway, or schema change.

## Objective

Verify that AgentCore still enforces the Windows Environment Variable policy and that no `.env` fallback, dotenv dependency, or literal credential has entered the control-plane repo.

## Required Steps

1. Run:

```powershell
git status --short --untracked-files=all
powershell -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreEnvPolicy.ps1
powershell -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\validators\validate-control-plane.ps1
```

Use `-WriteReport` when the audit is intentionally updating tracked report artifacts; otherwise these validators run in dry-run mode and report to stdout only.

2. If `scripts/mcp_control_plane.py`, `renderers/`, `registry/`, `supervisor/`, `contracts/`, or schema-adjacent files changed, rerun the control-plane generator before validating.
3. If a gateway auth failure appears, verify Windows environment variable presence and restart IDE/MCP processes before changing database auth.
4. Never print, log, or persist secret values.

## Findings File

Write findings to `docs/memory/env-policy-audit.md`.

- Create the file if it does not exist.
- Record date, files checked, commands run, pass/fail status, and non-secret remediation notes.
- List variable names only when needed.
- Never write password values, tokens, keys, certificates, fingerprints derived from secret values, or incident payloads.

## Failure Handling

- If any `.env` file exists, any dotenv usage appears, or any literal credential is detected, stop and report the exact file path and rule violation.
- If a required environment variable is missing, report the variable name only.
- If the gateway config uses a literal password, fail the audit immediately.
