# Codex Cheap Workers MCP

Repository-owned MCP server for bounded delegation from Codex to fixed OpenRouter model routes. This directory is the canonical source. The installed runtime is a generated deployment at `C:\Users\ynotf\.codex\mcp\cheap-workers`.

## Roles and routes

- DeepSeek V4 Pro: hard reasoning, independent critique, documentation guard, and documentation maintenance.
- MiniMax M3: long-context synthesis and bounded code edits.
- DeepSeek V4 Flash Latest: fast scouting and triage.
- Morph Fast Apply: merges lazy edits returned by edit workers.
- `documentation_guard_worker`: read-only drift review with a `BLOCK`, `REVISE`, or `ACCEPT` verdict.
- `documentation_maintainer_edit_worker`: the only cheap-worker documentation write path; defaults to dry-run.

Codex remains the architect, authority owner, and final verifier. Model identity is never authorization.

## Structural safety

- Read-only worker content and edit payloads are checked for active Windows environment secrets of at least 8 characters and high-confidence credential formats before any external request. Shorter environment values are intentionally ignored to avoid common-value false positives and must never be used as secrets.
- Edit targets must be one existing, non-binary file under an explicit absolute workspace root and no larger than 2 MiB by default.
- Same-file edits are serialized in process. A content hash is rechecked before backup and immediately before replacement.
- Writes use a same-directory exclusive temporary file, flush it, then rename it over the target. Node 24 on Windows was live-proven to replace an existing target without a delete gap.
- Every write has a rollback backup and a post-write hash check. A process killed before rename can leave an inert dot-prefixed temporary file; it never replaces the target partially.
- Ordinary code-edit workers reject documentation files. The documentation maintainer rejects source files and generated `.agentcore` projections.
- The documentation maintainer internally sends the actual proposed diff to the guard and writes only on the directly returned `ACCEPT`; a caller cannot supply the verdict. Protected anchor documentation additionally requires live `authority_maintainer` capability and a matching `AUTH-YYYY-MM-DD-*` approval environment.

Cross-process compare-and-swap is not available through the Windows filesystem API. The double hash check narrows that race, while the repository's worktree discipline and Git review remain the final concurrency boundary.

## Validate and deploy

```powershell
cd D:\github\agentcore-control-plane\tools\cheap-workers
.\install.ps1 -ValidateOnly
.\install.ps1
```

The installer validates canonical source, creates a timestamped deployment backup, copies an exact managed-file allowlist, installs pinned dependencies, and reruns all tests in the deployed target. It does not edit Codex configuration or secrets. Open a fresh Codex task after deployment so the MCP process loads the new version.

Use edit workers with `dry_run: true` first. Codex must inspect every diff and run the repository's narrow validators before accepting it.
