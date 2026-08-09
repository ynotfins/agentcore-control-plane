# Bifrost Rollout Ready — 2026-08-09 18:01 EDT

## Summary

The governed Bifrost rollout succeeded after the readiness checker was corrected to compare the live runtime config against a fresh source-rendered runtime candidate instead of the Git sanitized sidecar.

Live installation evidence from the approved rollout:

- `AgentCore-Bifrost-Gateway` registered.
- `AgentCore-Bifrost-Watchdog` registered.
- Task Scheduler Operational logging enabled.
- Authenticated gateway readiness confirmed on `127.0.0.1:8080`.
- `Get-BifrostStatus.ps1` returned `BIFROST_STATUS_OK`.
- `Test-AgentCoreBifrostGateway.ps1` returned `RESULT: PASSED`.

## Readiness result

Command:

```powershell
.\ops\bifrost\Test-AgentCoreMorningReadiness.ps1
```

Result:

```text
SUMMARY status=READY pass=23 warn=0 fail=0
```

Important checks:

- Cursor global MCP: exactly one server, `agentcore-gateway`.
- Bifrost status: `BIFROST_STATUS_OK`.
- Bifrost health: HTTP 200.
- Config drift: source-rendered candidate/live/projection match `41BB78234E659472C7A88AC1746E87A3E673460E3FCF5B0D4C470F19CD3B2106`.
- `AgentCore-Bifrost-Gateway`: running.
- `AgentCore-Bifrost-Watchdog`: ready, last result `0`.
- SwarmRecall API, Meilisearch, SwarmClaw, and Swarm web health: HTTP 200.
- Required Swarm and AgentCore roots exist.
- Required loopback ports are listening.
- LangGraph topology fingerprint matches `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32` with 15 nodes.

## Source correction

Readiness validation now treats `renderers\bifrost\config.json` as the sanitized Git sidecar, not the byte-identical runtime source. Runtime readiness is determined by rendering a fresh OAuth-aware candidate through:

```powershell
python scripts\bifrost\render_bifrost_config.py --out <temp> --no-also-config-dir --skip-renderer
```

and comparing that candidate hash with:

1. `F:\AgentCore\runtime\bifrost\config.json`
2. `F:\AgentCore\runtime\bifrost\config\config.json`

The temporary candidate is deleted after hashing.

## Validation

```text
python -m pytest scripts\bifrost\test_morning_readiness_script.py -q
5 passed
```

## Next milestone

M3 Bifrost live rollout is complete. Continue to M4: Sally full Swarm acceptance using:

`@D:\github\agentcore-control-plane\docs\prompts\SALLY_FULL_SWARM_ACCEPTANCE_PROMPT_2026-08-09.md`
