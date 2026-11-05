# Proposal: record AUTH-2026-11-05-EXECUTE-ALL standing execution authorization

**Date:** 2026-11-05  
**Status:** applied under `AUTH-2026-11-05-EXECUTE-ALL`  
**Approval:** `AUTH-2026-11-05-EXECUTE-ALL`

## Source statement

Tony Valentine own words (Nov 5, 2026, 12:54 AM ET, via Chief Of Staff):

> "execute all your other recommendations and in the future execute all recommendations and if it is questionable start another branch so we can undo it. We will save a ton of time by you not waiting for me... execute and complete the plan in Goal mode."

## What this AUTH covers

- Authorizes merging PR #10: MCP admissions harden follow-up (`cursor/harden-mcp-admissions-dd1a`)
  - Windows-safe node launcher form for Depwire and Tentra
  - pinned exact Tentra and GitHub MCP tool inventories
  - Depwire scoped to builder + ide virtual keys
- Authorizes merging PR #11: bifrost always-on follow-up
- Establishes a standing direction that questionable future changes should land on a separate undo branch so they can be reverted cleanly without blocking forward execution

## Recording intent

- This AUTH is the current standing execute-all authorization and should remain visible in `DOC_AUTHORITY.md` alongside the prior AUTH entries.
- This proposal records authorization only. It does not itself merge PR #10 or PR #11.
- Runtime guardrails remain unchanged: no Bifrost restart or live ChaosCentral mutation is implied by this record alone.
