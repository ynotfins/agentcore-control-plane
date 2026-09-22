# R3lentless-Grind Design System (RGDS)

PC-global / organizational UI authority. Built on a Material 3 token engine. Individual products (AgentCore, NFA, etc.) consume RGDS — they are not the system name.

| Layer | Path | Role |
| --- | --- | --- |
| Tier 1 primitives | `tokens/ref/` | `md.ref.*` — palette, type, spacing, shape, elevation, motion |
| Tier 2 system | `tokens/sys/` | `md.sys.*` — semantic roles (components bind here only) |
| Themes | `tokens/themes/` | Four `data-theme` modes |
| Custom | `tokens/custom/` | `md.custom.rainbowPulse` (Theme 4 featured only) |
| Compiled CSS | `css/` | Runtime custom properties + components + animations |
| Gallery | `preview.html` | Interactive 4-theme visual proof |
| Pins | `package-pins.json` | Exact frontend dependency versions for bootstrap |
| Enforcement | repo `.cursorrules` + `.cursor/rules/design-system-m3.mdc` | AI must use RGDS tokens; no hardcoded styles |

## Themes

| Mode | `data-theme` | Character |
| --- | --- | --- |
| 1 Primary Light | `primary-light` | Multi-color: blue primary, red secondary, green/orange/pink/yellow accents |
| 2 Secondary Light | `secondary-light` | Light/dark orange, blue+green accents, yellow strokes |
| 3 Primary Dark | `primary-dark` | ngrok-like slate/charcoal, sharp premium borders |
| 4 Secondary Dark | `secondary-dark` | Speakeasy-like deep black + `md.custom.rainbowPulse` |

## Brand swap

Seed values in `tokens/ref/palette.json` are **TEMPORARY placeholders**. Replace brand hex there only, then regenerate CSS. Never put brand hex in components.

## Bifrost

Bifrost does **not** host RGDS tokens. Use Bifrost Figma MCP (`search_design_system`, `get_design_context`) to validate UI against the published design library. Token truth stays in this Git tree.
