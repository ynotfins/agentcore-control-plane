# Locked-doc hardening + OmniRoute acceptance (2026-11-04)

Approval: `AUTH-2026-11-04-LOCKED-DOC-HARDENING-OMNIROUTE`
Branch: `feat/locked-doc-hardening-omniroute-2026-11-04`

## Gates

| Gate | Result |
| --- | --- |
| Strip live `AUTH-2026-09-05-UNIVERSAL-IDE-BIFROST-SKILLS-ALIGNMENT` from current alignment surfaces | PASS (historical audits/rollback untouched) |
| Re-land Open Design enrollment (`D:\open-design`) + audits/proposal/test | PASS |
| Re-land ADR Phase-2 `:18082` wording from `27d1ab4` | PASS |
| OmniRoute Job-B ADR + CONTEXT status | PASS |
| Enroll `paperclip` in `ops/Backup-AgentCorePostgres.ps1` (PG18 `:55433`) | PASS |
| IDE rules re-render / contract validate | (see CI / local validate) |
| No merge to main in this change | PASS (PR only) |

## Live evidence (ChaosCentral, 2026-11-04 ET)

- NFA `:3000/health` 200; NFA-Platform-* Running (before/after Bifrost work)
- Bifrost Raven VK removed; semantic_cache dim 1536 cache-hit proven
- VKs (names only): `omniroute` → User env `BIFROST_MCP_VK_OMNIROUTE`; `ide` → `BIFROST_MCP_VK_IDE`
- OmniRoute `127.0.0.1:20128` BelowNormal

## Culprit evidence (locked-doc drift commits)

- `27d1ab4` — Cursor `cheap-implementer` subagent (transcript `28996834-891c-4118-9d04-c5f2453a5f15` → subagent `666db283-46b8-4b7b-99dd-8759910a7a06`) committed "Checkpoint inherited dirty tracked tree before workstation restart."
- `729ff79` — Cursor agent session `0f26420c-331a-4980-b47b-3e8d962820fd` implemented/pushed Pi parallel host-companion policy ("feat(policy): govern Pi parallel subagent host companion"). No separate agent file named Pi-plan-implementer; attribution is that Cursor session executing the Pi plan.
