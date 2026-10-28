# R3lentless-Grind Design System (RGDS)

> **Status:** Locked policy — RGDS is the master organizational front-end standard for every product on this PC.
> **Architecture:** Material 3 (M3) token engine (`md.ref.*` / `md.sys.*`).
> **Source of truth:** `docs/design/m3/tokens/` (W3C Design Tokens).
> **Compiled runtime:** `docs/design/m3/css/`.
> **Gallery:** `docs/design/m3/preview.html`.
> **Enforcement:** `.cursorrules` + `.cursor/rules/design-system-m3.mdc`.
> **Seed status:** Brand palette values are **TEMPORARY placeholders**. Swap hex in `tokens/ref/palette.json` only.

**Naming authority:** This system is officially the **R3lentless-Grind Design System (RGDS)**. It is not the “NFA Design System” and not an “AgentCore Design System” product brand — AgentCore and NFA are individual products that consume RGDS.

Legacy three-theme (`light` / `dark` / `hc`) and prior Speakeasy/NFA-local color prose are superseded for **new RGDS-governed work**. Product repos (e.g. NFA) migrate deliberately; they are not auto-rewritten by this lock-in.

---

## 1. Architecture (2-tier)

| Tier | Prefix | Location | Who consumes |
| --- | --- | --- | --- |
| 1 — Reference | `md.ref.*` | `m3/tokens/ref/` | Theme authors / brand swap |
| 2 — System | `md.sys.*` | `m3/tokens/sys/` + theme overlays | **All components** |
| Custom | `md.custom.*` | `m3/tokens/custom/` + theme extras | Featured accents only |

Components never read `md.ref.*` directly. Components never hardcode hex, raw `px`, or freehand shadows.

---

## 2. Four theme modes

| # | Name | `data-theme` | Character |
| --- | --- | --- | --- |
| 1 | Primary Light | `primary-light` | Multi-color: blue primary, red secondary, green tertiary; orange/pink/yellow accents |
| 2 | Secondary Light | `secondary-light` | Light/dark orange; blue+green accents; yellow featured strokes |
| 3 | Primary Dark | `primary-dark` | ngrok-like slate/charcoal; high-contrast boxes; sharp premium borders; **no** rainbow |
| 4 | Secondary Dark | `secondary-dark` | Deep black; orange secondary stack; blue/green accents; **`md.custom.rainbowPulse`** on featured |

Resolution order: `localStorage['rgds-theme']` → `?theme=` → `data-theme` default `primary-light`.

---

## 3. Interactive hover state (all four themes)

- Tokens: `md.sys.state.hover.*` (`tokens/sys/state.json` + per-theme overrides)
- CSS vars: `--md-sys-state-hover-tint`, `--md-sys-state-hover-tint-amount`, `--md-sys-state-hover-border`, `--md-sys-state-hover-saturate`
- Behavior: cards, primary/secondary buttons, icon targets, and theme controls brighten via `color-mix` + subtle saturate on `:hover` / `:focus-within`
- Theme tuning:
  - Primary Light — blue vibrancy lift
  - Secondary Light — yellow/warm lift + stronger featured stroke feel
  - Primary Dark — ngrok-style near-white slate lift (~7%)
  - Secondary Dark — warm orange lift over deep black
- Must honor `prefers-reduced-motion` (shortened transitions)

---

## 4. Rainbow pulse (Theme 4)

- Token: `md.custom.rainbowPulse` (`tokens/custom/rainbow-pulse.json`)
- Utility class: `.md-rainbow-pulse`
- Keyframes: `md-custom-rainbow-pulse` + `md-custom-rainbow-rotate` in `css/animations.css`
- Scope: featured cards / primary CTAs only
- Must honor `prefers-reduced-motion`

---

## 5. Layout & components

- Aesthetic: Apple-like, clean vector, generous whitespace
- Large cards, large buttons (≥52px tall), 64px icon targets
- Corners: `md.sys.shape.corner.medium` / `large` (slightly rounded)
- Elevation: `md.sys.elevation.level1`–`level3` (subtle → medium)
- Icons: multi-color (2–3 layers via `--md-custom-icon-*`) for featured only; utility = solid token color

---

## 6. Bootstrap & Bifrost

- Pins: `docs/design/m3/package-pins.json` — install with `--save-exact`
- Bifrost: Figma MCP for validation (`search_design_system`, `get_design_context`). **Do not** host RGDS tokens as a Bifrost upstream.
- Copy/reference `docs/design/m3` into each new UI project

---

## 7. Anti-patterns

- Inline hex / raw spacing in components
- Unpinned “latest” Tailwind/Radix/Lucide installs
- Rainbow on every surface
- Per-page color maps or `tailwind.config.js` color overrides
- JS theme systems beyond toggling `data-theme`
- Calling RGDS “NFA Design System” or “AgentCore Design System” in new authority text
- Hardcoded hover rgba/hex outside `md.sys.state.hover` tokens

---

## 8. Change control

- Token PR: old → new, affected components, screenshots in **all four** themes (include hover states)
- Brand hex swap: edit `tokens/ref/palette.json` (+ regenerate CSS); no component edits
- New component: document HTML/CSS/ARIA for all four themes

*Locked: 2026-09-22. Official name: R3lentless-Grind Design System (RGDS). Hover state layer added same day. Review trigger: brand seed finalization, new framework adoption, or operator instruction.*
