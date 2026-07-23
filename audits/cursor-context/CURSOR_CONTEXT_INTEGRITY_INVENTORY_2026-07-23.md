# Cursor Context Integrity Repair — Phase 0 Inventory

**Generated:** 2026-07-23T05:15:30Z  
**Repository:** `D:\github\agentcore-control-plane`  
**Branch/HEAD:** `main` / `1bf84a1ab2c440f4a00f0fec822bc9f8e34c5268`  
**Repair plan:** `@C:\Users\ynotf\.cursor\plans\cursor_context_integrity_repair_8ca1fe62.plan.md`

This inventory captures the active rule stack, hook state, and the phantom workspace tree immediately before the repair begins. It is the rollback baseline for the Cursor Context Integrity Repair.

## Active Cursor rules loaded by the current session

| Path | Size | SHA-256 | mtime | Notes |
|------|------|---------|-------|-------|
| `D:\github\agentcore-control-plane\.cursor\rules\agentcore-active-bootstrap.mdc` | 4691 | `D710D5CCEA571BC6C5931EB7CB2E57E1CC99D30A3FD022C440EC2A7E91CFB521` | 2026-07-21T05:47:32Z | Stale generated alwaysApply packet; will be removed (Phase 3) |
| `D:\github\agentcore-control-plane\.cursor\rules\agentcore-env-policy.mdc` | 2254 | `56F26580E8C9019834A6BB60D29419C2B372DFE9FA8AF4D114E0AFEC37AFA34D` | 2026-07-17T17:36:30Z | Missing valid frontmatter; will be repaired (Phase 6) |
| `D:\github\.cursor\rules\00-memory-autopilot.mdc` | 1398 | `CB5F25696DEABAEFD912330774EE5334CAED6D54B0BA07450A1BAB2D1CA80540` | 2026-02-19T00:58:33Z | Contradicts AgentCore `agentcore-memory` policy; quarantine (Phase 6) |
| `D:\.cursor\rules\openmemory.mdc` | 12980 | `F865D7F9650A87FFC1EC00D2E7243B4D157AE1568B6865FCEA3EA5A7159843F5` | 2026-05-07T02:44:13Z | Contradicts AgentCore `agentcore-memory` policy; quarantine (Phase 6) |
| `C:\Users\ynotf\.cursor\rules\30-memory-usage.mdc` | 3030 | `DD69907AC075BBC98AADD6966F78E547069F601608A45D6EB3FAF0DDA18002E5` | 2026-06-30T01:27:25Z | Retired `global-memory-gateway` baseline; quarantine (Phase 6) |

## Hook state

| Path | Size | SHA-256 | mtime | Notes |
|------|------|---------|-------|-------|
| `D:\github\agentcore-control-plane\.cursor\hooks.json` | 453 | `1C658608CAD545D3A45692D5E6A29E5F4F177F10FEAC479C855DE3382C8FE363` | 2026-07-21T05:47:54Z | `sessionStart` + `beforeSubmitPrompt` only; no `preToolUse` |
| `D:\github\agentcore-control-plane\.cursor\hooks\agentcore-hook.cmd` | 803 | `7ADA9D07699C3346B73DC2B042C753463F58D3D3BC4CF53247A3D5E872BDB115` | 2026-07-21T05:47:54Z | Untouched by repair (dispatcher/bootstrap only) |
| `D:\github\agentcore-control-plane\.cursor\hooks\agentcore-hook.ps1` | 1887 | `EAEA02D2F63873764E2BC60A9FDEBB5D4874286CA072E243812AA461F7BD3F03` | 2026-07-21T05:47:54Z | Untouched by repair (dispatcher/bootstrap only) |

## Phantom workspace tree (drive-relative root bug artifact)

| Path | Size | SHA-256 |
|------|------|---------|
| `github\agentcore-control-plane\.agentcore\runtime\cursor-bootstrap.json` | 2806 | `707C33BCE3A72CB051B73D1EF2AC63F2C79E23A8399C7CB5F78AA82B61409993` |
| `github\agentcore-control-plane\.agentcore\runtime\cursor-bootstrap.md` | 2501 | `14568AA4F98BEB93A582B00C307947C88AC59C7506EB8942184E030EDBC8D787` |
| `github\agentcore-control-plane\.cursor\rules\agentcore-active-bootstrap.mdc` | 2609 | `023F90DE6AECAC39499277658C92781C39DE513C155A45FD3CDE1FD7F2CEB261` |

## Known contradictions to be repaired

1. **Stale generated alwaysApply rule.** `.cursor\rules\agentcore-active-bootstrap.mdc` is produced by `bootstrap.py` on every session and is not meant to be committed. It should be delivered only as an ephemeral `sessionStart` `additional_context` packet.
2. **Drive-relative workspace root resolution.** The phantom tree under `github\agentcore-control-plane` proves that `resolve_workspace()` accepted a drive-relative path (`d:github\agentcore-control-plane`) as absolute and wrote artifacts under the wrong root.
3. **Malformed `beforeSubmitPrompt` stdin.** Hook logs showed `malformed stdin JSON`; `_parse_hook_json` must capture a bounded hex preview and tolerate the defect.
4. **Contradictory memory rules.** The three quarantined rules above route memory through `global-memory-gateway`, `mem0`, and OpenMemory patterns that conflict with the locked `agentcore-gateway` → `agentcore-memory` architecture.
5. **Missing IDE status dimensions.** `IDE_CAPABILITY_MATRIX.yaml` collapses multiple acceptance gates into a single `m8_enrollment` value; per-dimension status with evidence timestamps is required.
6. **Unclassified July 22 handoff.** `docs\handoffs\AGENTCORE_FULL_CHAT_HANDOFF_2026-07-22.md` exists but is not yet admitted into `DOC_AUTHORITY.md` as a current handoff.

## Raw inventory file

Full machine-readable inventory: `cursor_context_integrity_inventory_2026-07-23.json` (same directory).
