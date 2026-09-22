# Design: R3lentless-Grind Design System (RGDS) — Material 3 token engine

Date: 2026-09-22  
Status: Implemented in `docs/design/m3/`  
Authority: `docs/design/DESIGN_SYSTEM.md`

## Decision

Adopt the **R3lentless-Grind Design System (RGDS)** as the master organizational front-end standard, implemented with Google Material 3 naming (`md.ref.*` / `md.sys.*`), four `data-theme` modes, and Theme-4 `md.custom.rainbowPulse`. Brand seeds are temporary placeholders.

RGDS is not product-branded as NFA or AgentCore; those products consume RGDS.

## Non-goals

- Auto-migrate NFA Flutter tokens in this change
- Host tokens as a Bifrost MCP upstream
- Unpinned “install latest” frontend deps

## Distribution

Git tree under agentcore-control-plane; projects copy/reference `docs/design/m3`. Bifrost provides Figma validation tools only. Cursor enforcement via `.cursorrules` + `.cursor/rules/design-system-m3.mdc`.

## Acceptance

- [x] Token sheets + CSS + preview.html
- [x] Four theme switcher; Theme 4 rainbow pulse
- [x] Contract `contracts/agentcore-design-system.json` (display name RGDS)
- [x] AGENTS.md Learned Fact aligned to RGDS four-mode M3
- [ ] Operator brand hex finalization
- [ ] Optional Figma RGDS library publish
