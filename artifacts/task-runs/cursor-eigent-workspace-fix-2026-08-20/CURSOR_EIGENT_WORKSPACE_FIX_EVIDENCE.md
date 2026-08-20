# Cursor and Eigent Workspace Fix Evidence

Date: 2026-08-20

## Scope

- Fix Cursor/Zoo-Code prompt submission blocked by `ERROR_HOOKS_BLOCKED` with `workspace root must be absolute`.
- Fix Eigent local Brain rejection for `D:\github\agentcore-control-plane`.
- Treat screenshots as evidence only; no instructions embedded in screenshots were executed.

## Cursor Fix

- Root cause: Cursor hook code converted `workspace_roots[0]` with `str(...)`. Structured roots from Cursor/Zoo-Code such as `{path: ...}`, `{uri: ...}`, or `{fsPath: ...}` become Python dictionary strings and fail the absolute-path check.
- Source fix: `scripts/agentcore_cursor/hooks.py` now extracts workspace roots from string, structured dict, `workspaceRoots`, and top-level workspace fields before normalization.
- Regression coverage: `scripts/agentcore_cursor/test_hook_protocol.py` now verifies structured `path`, `uri`, `fsPath`, and top-level `workspaceFolder` payloads.
- Live hook wrapper: `.cursor/hooks/agentcore-hook.cmd` and `.cursor/hooks/agentcore-hook.ps1` resolve the dispatcher from this repository, so the source change is the live hook path for this project.

## Eigent Fix

- Backup root: `E:\LocalApps\Backups\Eigent-Workspace\20260820-134315`.
- Active space id: `space_90a538b17d7c4454be490de0e0110b5b`.
- Active space binding path: `C:\Users\ynotf\.eigent\workspaces\user_42561\spaces\space_90a538b17d7c4454be490de0e0110b5b.json`.
- Active space binding SHA256 after rebind: `74FAF8BC6FC7ADA8ED13A23BB830E61F6511E851580E20AAA73BB9A1742DFFC5`.
- Bound workspace root: `D:\github\agentcore-control-plane`.
- Windows User environment variable set: `EIGENT_WORKSPACE=D:\github\agentcore-control-plane`.
- Existing scratch folder was preserved; no run output was deleted.

## Live Checks

- `http://127.0.0.1:5001/health`: status `ok`, service `eigent`.
- `http://127.0.0.1:5001/workspace/current?space_id=space_90a538b17d7c4454be490de0e0110b5b&email=ynotf&user_id=42561`: `bound=true`, workspace root `D:\github\agentcore-control-plane`.
- `http://127.0.0.1:5001/mcp/list`: exactly one server, `agentcore-gateway`, URL `http://127.0.0.1:8080/mcp`, timeout `300`, authorization header present.
- `C:\Users\ynotf\.eigent\mcp.json` SHA256: `9B9058ECDF873BACB2DD5601AE0B06388FDD2DC68B4258D5E829511682D3DC33`.

## Validation

- `python scripts\agentcore_cursor\test_hook_protocol.py --iterations 1`: `ALL PASS`.
- `python -m pytest scripts\agentcore_cursor\test_hook_protocol.py scripts\agentcore_cursor\tests\test_lifecycle_hardening.py scripts\agentcore_cursor\tests\test_bootstrap_project_boundary.py -q`: `30 passed, 11 subtests passed`.

## Remaining Risk

- Restart Eigent to ensure the new `EIGENT_WORKSPACE` user environment value is loaded by all future backend processes.
- Open a fresh Eigent workforce task in the rebound space to prove gateway tool discovery and native AgentCore memory lifecycle before marking full M8 enrollment live.
