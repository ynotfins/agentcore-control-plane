# Research Plan: FakeYou / Evermind Ecosystem — Paid vs Free/Local Tooling

**Task type:** Verification-Focused Task (specific claims to confirm/refute)
**Date:** 2026-10-28
**Author:** Matrix Agent

## Working hypothesis (to test)
H1: `evermind.ai` is a rebrand of `fakeyou.com` (same company/service).
H2: `fakeyou.com` now redirects to `evermind.ai`.
H3: Official FakeYou ecosystem tools can be enumerated from an official apps listing page.
H4: `fakeyou.ts` (archived Aug 18 2024) still functions against the current API.
H5: A free (non-paid) FakeYou account + `FAKEYOU_COOKIE` is the minimum for local TTS use.

## Preliminary signal (2026-10-28)
- `evermind.ai` homepage = "Memory OS for AI Agents" (EverOS / EverMe / EverCore / EverMemOS / HyperMem). **No mention of FakeYou, voice cloning, or TTS.** H1 looks doubtful.
- `fakeyou.com` homepage + `/pricing` + `/tts` + `/voice-conversion` return live search-indexed titles; direct scraper fetch is Cloudflare-blocked (our IP), so must use alternate retrieval.
- `github.com/jack3898/fakeyou.ts` confirmed: **archived, read-only since Aug 18, 2024**, GPL-3.0, ESM-only, `FAKEYOU_COOKIE` env var, login optional (anonymous = higher rate limits/slower).

## Steps
- [ ] 1.1 Verify evermind.ai identity, ownership, and any FakeYou linkage (primary: evermind.ai pages, GitHub org, LinkedIn, Crunchbase)
- [ ] 1.2 Verify fakeyou.com domain status: redirect chain, HTTP headers, domain of record
- [ ] 1.3 Enumerate official FakeYou app/tool listing page and every listed app
- [ ] 2.1 Retrieve current fakeyou.com/pricing (primary, alternate retrieval path)
- [ ] 2.2 Retrieve official API docs (docs.fakeyou.com) — auth, rate limits, endpoints
- [ ] 2.3 Retrieve fakeyou.ts source to extract exact REST endpoints + base hosts
- [ ] 3.1 Verify endpoint survival on current evermind/fakeyou API (breaking-change check)
- [ ] 3.2 Determine account/premium gating per app/tool
- [ ] 3.3 Free-tier limits: queue, rate limits, model access, character caps
- [ ] 4.1 Enumerate fully-free local voice-cloning alternatives (primary GitHub repos)
- [ ] 5.1 Cross-check with >=3 independent sources per critical fact; assign confidence
- [ ] 5.2 Write final report (table, pricing, limits, bottom line, alternatives, open questions)
- [ ] 6.1 Final review: plan checkboxes complete, list-density audit, source count/domain diversity

## Verification standard
Critical fact = 3 independent credible sources. Primary preferred (official site/GitHub/repo). Contradictions recorded explicitly. Every number gets URL + observation date (2026-10-28).
