# Cheap Workers v0.4.0 and Documentation Guard Acceptance — 2026-08-06

**Approval:** `AUTH-2026-08-06-DOCUMENTATION-GUARD`

**Scope:** production-harden the Codex cheap-worker stack, establish repository-owned deployment authority, and add a governed documentation guard/maintainer workflow across AgentCore-managed IDE policy without changing Bifrost, AgentCore memory, LangGraph, Swarm, IDE MCP entries, or secrets.

## Outcome

`tools/cheap-workers` is the canonical source for v0.4.0. It is deployed to `C:\Users\ynotf\.codex\mcp\cheap-workers`; the existing Codex MCP configuration remains unchanged. A fresh stdio client lists nine tools, including `documentation_guard_worker` and `documentation_maintainer_edit_worker`.

The documentation maintainer is the only ordinary cheap-worker documentation-write path. Ordinary edit workers reject documentation files. The maintainer rejects source targets and generated `.agentcore` projections, produces one bounded diff, submits that actual diff to its internal independent guard, and writes only on the directly returned `ACCEPT`. The MCP schema exposes no caller-supplied `guard_verdict` field. Protected anchor files additionally require live `authority_maintainer` capability and an approval reference exactly matching the live authority approval environment.

The policy is canonical at `docs/agent-policy/DOCUMENTATION_GOVERNANCE.md`, included in the project execution contract, the global agent policy, `AGENTS.md`, `CLAUDE.md`, `MASTER_CONFIG_AND_PROMPT.md`, and nine tracked IDE `GLOBAL_RULES.md` projections. IDEs without the Codex-owned workers must hand off documentation proposals; no second MCP entry or Bifrost exposure was added.

## Structural safety

- outbound task/context/source/lazy-edit/merged-diff content is checked for active Windows environment secrets of at least eight characters and high-confidence credential formats before external calls;
- target realpath must remain inside the explicit workspace; target must be an existing non-binary file no larger than 2 MiB by default;
- same-file operations are serialized in process;
- source hash is checked after generation and again immediately before replacement;
- write uses an exclusive same-directory temporary file, UTF-8 write, file flush, close, and rename over the target; no delete gap;
- every write receives an external rollback backup and post-write hash verification;
- installer deploys an exact managed-file allowlist, validates source and target, and restores prior managed files/dependencies on failure.

Live Node 24 Windows proof confirmed rename over an existing target succeeds and leaves no temporary file.

## Test and validation evidence

- TDD RED: size, secret, atomic-replacement, documentation-boundary, internal-guard, and protected-authorization tests failed before implementation for the intended reasons.
- Canonical package: `32/32` tests passed.
- Deployed package: `32/32` tests passed.
- `npm audit`: zero vulnerabilities.
- Canonical-to-installed comparison: 13 managed non-ignore files checked; zero hash mismatches.
- Fresh stdio schema: nine tools; documentation maintainer properties are `approval_reference`, `context`, `dry_run`, `instruction`, `max_tokens`, `path`, `temperature`, and `workspace_root`; `guardVerdictExposed=false`.
- `python scripts/validate_authority_lock.py`: PASS.
- `python scripts/bifrost/validate_contracts.py`: PASS.
- `python scripts/validate_cursor_prompt_format.py MASTER_CONFIG_AND_PROMPT.md`: PASS.
- Project execution policy/schema validation: PASS.
- Nine tracked IDE `GLOBAL_RULES.md` renderings: current. The pre-existing untracked `ide-profiles/reasonix` profile was restored from task backup and excluded from this checkpoint.
- Fresh `codex debug prompt-input`: documentation governance and both worker roles discovered.
- Scoped secret scan: clean across 33 intended files. The repository-wide scan separately identified 13 pre-existing out-of-scope secret-like artifacts by sanitized path only; no value was opened or printed, and remediation is recorded as `AC-TODO-010` pending explicit approval.

## Review history

1. Live documentation-guard smoke test returned `BLOCK` for an abbreviated “sole write path” statement that omitted protected-file approval and independent review. The canonical policy explicitly preserves both gates.
2. Independent policy review returned `ACCEPT`: no authority inversion, protected-gate weakening, generated-state ownership error, or unsafe cross-IDE route.
3. Independent implementation review initially returned `BLOCK` because a plain caller-supplied `guard_verdict=ACCEPT` could be forged.
4. Remediation removed that input from the schema and moved guard invocation inside the maintainer against the actual generated diff. Regression tests prove forged caller values cannot bypass the internal verdict.
5. Independent remediation review returned `ACCEPT` for controlled Codex-reviewed production use.

## Rollback and hashes

Authority/document backups: `C:\Users\ynotf\.codex\backups\documentation-governance-20260806-035833`.

Global Codex guidance backup: `C:\Users\ynotf\.codex\backups\documentation-guard-global-20260806-041714\AGENTS.md`.

Latest installed-package rollback: `C:\Users\ynotf\.codex\backups\cheap-workers-deploy\20260806-041750`.

| File | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| `AGENTS.md` | `9B47C6CCA0A5D57811585EDB3385F11F5C646003098444DE72A58074B54FB8B4` | `582467980CEA63A165AB9D9058B0C06D05468BD3419E2CCD2F504195C699B9AD` |
| `CLAUDE.md` | `1CA01A3FAFBA743A355DD927844A8B7A48B901E557B26F48BE4334F2953244DD` | `2F42454702AEEC7C01301E793F8EEB25E191F671D246CEC7F6974205F4406628` |
| `MASTER_CONFIG_AND_PROMPT.md` | `E82DF915BCEB68C4AFF448AE46A48595ACE827FF431FB63FFE0E373061ADCA79` | `43546BB509F02FF2272DAADF019E99BA324680190429F181C97659E9A217FA06` |
| `contracts/global-agent-policy.yaml` | `CF5BBFDA626F478B56907D880E67FF5CA4F5705B136731CA3925FE9A269DC88D` | `FD61D992BFA4060DE93D214E35EB2FE79852CC1B3F5EE14D0819EBE808E59A22` |
| `contracts/project-execution-policy.json` | `CE0325583C429A33158C73F88F69C9E423EA501CBCF8634B64AA6F64373DDE30` | `74E07840ADCDE5001CCE677F153C700714E2CF57F99D6F38B59CB1E27B37C64D` |
| `docs/agent-policy/DOCUMENTATION_READ_ORDER.md` | `167DCC3051D9382EF300CDF5C7CE9EDC940A37BFFA8268DEBFD2E39D307B1BBD` | `271B88C834EA6FBE54C8708BD3D2315D7AD41007EA24F5397D04775E1DF5EF46` |
| `docs/current/MASTER_TODO.md` | `B8BB095A8201687A51236EC3E6720871EF386A6F4680A41499A60EE7E8D3D351` | `88E3FFF41FF06C8A3917C2280DA4DEE88D4EB1A53B189E79532B9CB8227CC279` |

## Accepted residuals

- Values shorter than eight characters are ignored by environment-secret matching to avoid common-value false positives. Such short values are forbidden as secret material.
- Windows exposes no cross-process filesystem compare-and-swap for this path. The final external-process race is narrowed by double hash checks but cannot be eliminated; worktree discipline and Git review remain the final concurrency boundary.
- A process killed after temporary-file creation but before rename can leave an inert dot-prefixed temporary file; it cannot partially replace the target.
- Failed deployment can leave newly introduced unreferenced files because the project deletion policy forbids multi-file cleanup without explicit approval. Restored old server/package code does not import them.
- The currently running Codex task loaded the previous MCP process. The installed v0.4.0 tool surface is proven with a fresh stdio client and becomes native to Codex after a fresh task/restart.
- Canonical/rendered policy is complete for nine tracked IDE profiles. Product-specific live import remains subject to each IDE profile’s declared delivery mechanism and must not be falsely reported as native validation.

## Verdict

**PASS — controlled Codex-reviewed production use.**
