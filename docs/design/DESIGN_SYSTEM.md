# AgentCore Design System

> **Status:** Locked policy. Every AgentCore-managed project must follow this.
> **Source of truth:** `docs/design/tokens.json` (W3C Design Tokens format).
> **Consumed by:** every IDE via `AGENTS.md`; every project via `@`-reference; every UI surface via `data-theme`.
> **Aesthetic target:** Apple-grade polish + clarity; cards + 64px icons; rotating rainbow on dark; vibrant rainbow on light; instant theme switching with no JS build step.

This document is **tight on purpose**. The previous draft (25KB, single-product HTML + SillyTavern overrides + a duplicate "container class wrapper" CSS) has been replaced with a real design system: token format, three themes, component contract, anti-patterns, and the minimum CSS needed to enforce it.

---

## 1. Tech Baseline

| Layer | Choice | Why |
| --- | --- | --- |
| Token format | **W3C Design Tokens** (`$value` / `$type` / `$extensions`) | Stable spec; portable to CSS, iOS, Android, Tailwind; versionable in Git |
| Runtime | **CSS custom properties** on `:root[data-theme="..."]` | Zero-runtime theme switching; no flash on reload |
| Utility framework | **Tailwind CSS v4** with `@theme` directive | CSS-native tokens; no `tailwind.config.js` required |
| Color space | **OKLCH** for all generated palettes | Perceptually uniform; predictable contrast across hues |
| Typography | **Inter** (web) / **SF Pro Display + SF Pro Text** (Apple) | Apple-grade readability; wide weight range; free |
| Spacing | **8pt grid** + half-step (4pt) | Apple HIG convention |
| Radii | **Apple scale**: 4, 8, 12, 16, 20, 24, 32, 9999 (pill) | Matches iOS / iPadOS |
| Icons | **Lucide** (web) / **SF Symbols** (Apple) | 64px minimum on touch; consistent stroke |
| Reference look | morphllm.com (cards) · speakeasy.com (dark + rotating rainbow) · buildwithfern.com (clean Apple polish) | Visual targets, not source material |

**No** design system that depends on a JavaScript runtime for theme switching. **No** inline hex colors in components. **No** `tailwind.config.js` color overrides.

---

## 2. Themes

Three themes, all defined in the same token file, switched at runtime via `data-theme` on `<html>`.

| Theme | `data-theme` value | Default | Look |
| --- | --- | --- | --- |
| Light | `light` | `prefers-color-scheme: light` | White surface, vibrant Google-like accents, **rainbow static border** on primary cards/buttons |
| Dark | `dark` | `prefers-color-scheme: dark` | Onyx surface, speakeasy orange, **rotating rainbow border** on primary cards/buttons |
| High Contrast | `hc` | admin toggle only | Pure black/white, no gradients, WCAG AAA |

**Theme resolution order** (highest wins):

1. `localStorage['agentcore-theme']` (user explicit choice)
2. `?theme=` URL param (shareable link override)
3. `<meta name="theme" content="...">` (admin-set)
4. `prefers-color-scheme` (OS default)
5. `light`

Admin can lock any single theme or expose a 3-way toggle via the **Theme API** (`POST /api/theme { theme, scope }` with operator bearer).

```html
<!-- Set on every page before <body> renders -->
<html data-theme="dark">
```

```ts
// Theme switch — zero runtime cost
document.documentElement.setAttribute('data-theme', 'dark');
localStorage.setItem('agentcore-theme', 'dark');
```

---

## 3. Tokens (W3C Design Tokens format)

Full source: `docs/design/tokens.json`. Required fields per token: `$value`, `$type`, optional `$description`, optional `$extensions`.

```jsonc
{
  "color": {
    "surface": {
      "page":    { "$value": "oklch(99% 0.005 250)", "$type": "color", "$description": "Page background" },
      "card":    { "$value": "oklch(100% 0 0)",      "$type": "color" },
      "elevated":{ "$value": "oklch(98% 0.005 250)", "$type": "color" }
    },
    "ink": {
      "primary": { "$value": "oklch(20% 0.02 250)",  "$type": "color" },
      "muted":   { "$value": "oklch(50% 0.02 250)",  "$type": "color" },
      "inverse": { "$value": "oklch(98% 0 0)",       "$type": "color" }
    },
    "brand": {
      "orange":  { "$value": "oklch(68% 0.22 35)",   "$type": "color", "$description": "Speakeasy primary" },
      "blue":    { "$value": "oklch(70% 0.15 230)",  "$type": "color" },
      "green":   { "$value": "oklch(72% 0.18 145)",  "$type": "color" },
      "pink":    { "$value": "oklch(70% 0.20 0)",    "$type": "color" }
    },
    "rainbow": {
      "$value": "linear-gradient(90deg, oklch(65% 0.25 25), oklch(75% 0.20 60), oklch(85% 0.20 95), oklch(72% 0.20 145), oklch(75% 0.15 230), oklch(60% 0.20 290), oklch(65% 0.25 0))",
      "$type": "gradient"
    }
  },
  "radius": {
    "xs": { "$value": "4px",   "$type": "dimension" },
    "sm": { "$value": "8px",   "$type": "dimension" },
    "md": { "$value": "12px",  "$type": "dimension" },
    "lg": { "$value": "16px",  "$type": "dimension" },
    "xl": { "$value": "20px",  "$type": "dimension" },
    "2xl":{ "$value": "24px",  "$type": "dimension" },
    "3xl":{ "$value": "32px",  "$type": "dimension" },
    "pill":{"$value": "9999px","$type": "dimension" }
  },
  "space": {
    "0":  { "$value": "0",     "$type": "dimension" },
    "1":  { "$value": "4px",   "$type": "dimension" },
    "2":  { "$value": "8px",   "$type": "dimension" },
    "3":  { "$value": "12px",  "$type": "dimension" },
    "4":  { "$value": "16px",  "$type": "dimension" },
    "5":  { "$value": "20px",  "$type": "dimension" },
    "6":  { "$value": "24px",  "$type": "dimension" },
    "8":  { "$value": "32px",  "$type": "dimension" },
    "10": { "$value": "40px",  "$type": "dimension" },
    "12": { "$value": "48px",  "$type": "dimension" },
    "16": { "$value": "64px",  "$type": "dimension" },
    "24": { "$value": "96px",  "$type": "dimension" }
  },
  "shadow": {
    "sm":  { "$value": "0 1px 2px oklch(0% 0 0 / 0.06)",  "$type": "shadow" },
    "md":  { "$value": "0 4px 12px oklch(0% 0 0 / 0.10)", "$type": "shadow" },
    "lg":  { "$value": "0 12px 32px oklch(0% 0 0 / 0.18)","$type": "shadow" },
    "xl":  { "$value": "0 24px 60px oklch(0% 0 0 / 0.28)","$type": "shadow" },
    "glow":{ "$value": "0 0 24px oklch(68% 0.22 35 / 0.35)","$type": "shadow" }
  },
  "duration": {
    "fast":    { "$value": "120ms", "$type": "duration" },
    "default": { "$value": "280ms", "$type": "duration" },
    "slow":    { "$value": "600ms", "$type": "duration" },
    "tracer":  { "$value": "3500ms","$type": "duration", "$description": "Rotating rainbow loop" }
  },
  "easing": {
    "smooth": { "$value": "cubic-bezier(0.16, 1, 0.3, 1)", "$type": "cubic-bezier" },
    "snap":   { "$value": "cubic-bezier(0.2, 0, 0, 1)",    "$type": "cubic-bezier" }
  }
}
```

**Theme overrides** (light / dark / hc) live in the same file under the `$themes` key and are applied via `data-theme` selectors. They are **derivatives** of the base OKLCH values — never freehand hex.

---

## 4. CSS: Compiled `@theme` Block (Tailwind v4)

Generated from `tokens.json` by the build step (`scripts/design/build-tokens.mjs`). Pasted here so every project starts from the same source.

```css
@import "tailwindcss";

@theme {
  --color-surface-page:   oklch(99% 0.005 250);
  --color-surface-card:   oklch(100% 0 0);
  --color-surface-raised: oklch(98% 0.005 250);
  --color-ink-primary:    oklch(20% 0.02 250);
  --color-ink-muted:      oklch(50% 0.02 250);
  --color-ink-inverse:    oklch(98% 0 0);
  --color-brand-orange:   oklch(68% 0.22 35);
  --color-brand-blue:     oklch(70% 0.15 230);
  --color-brand-green:    oklch(72% 0.18 145);
  --color-brand-pink:     oklch(70% 0.20 0);

  --radius-xs:  4px;  --radius-sm:  8px;  --radius-md: 12px;
  --radius-lg: 16px;  --radius-xl: 20px;  --radius-2xl: 24px;
  --radius-3xl: 32px; --radius-pill: 9999px;

  --space-1: 4px;  --space-2: 8px;  --space-3: 12px;
  --space-4: 16px; --space-5: 20px; --space-6: 24px;
  --space-8: 32px; --space-10: 40px;--space-12: 48px;
  --space-16: 64px;--space-24: 96px;

  --shadow-sm: 0 1px 2px oklch(0% 0 0 / 0.06);
  --shadow-md: 0 4px 12px oklch(0% 0 0 / 0.10);
  --shadow-lg: 0 12px 32px oklch(0% 0 0 / 0.18);
  --shadow-xl: 0 24px 60px oklch(0% 0 0 / 0.28);
  --shadow-glow: 0 0 24px oklch(68% 0.22 35 / 0.35);

  --duration-fast: 120ms; --duration-default: 280ms;
  --duration-slow: 600ms; --duration-tracer: 3500ms;
  --easing-smooth: cubic-bezier(0.16, 1, 0.3, 1);
}

/* ─────────── DARK THEME ─────────── */
:root[data-theme="dark"] {
  --color-surface-page:   oklch(8% 0 0);
  --color-surface-card:   oklch(11% 0 0);
  --color-surface-raised: oklch(14% 0 0);
  --color-ink-primary:    oklch(98% 0 0);
  --color-ink-muted:      oklch(65% 0.01 250);
  --color-ink-inverse:    oklch(15% 0 0);
  --color-brand-orange:   oklch(72% 0.20 35);
  --color-brand-blue:     oklch(75% 0.13 230);
  --color-brand-green:    oklch(75% 0.16 145);
  --color-brand-pink:     oklch(72% 0.20 0);
}

/* ─────────── HIGH-CONTRAST THEME ─────────── */
:root[data-theme="hc"] {
  --color-surface-page:   #000;
  --color-surface-card:   #000;
  --color-ink-primary:    #fff;
  --color-ink-muted:      #d0d0d0;
  --color-brand-orange:   #ff8a4a;  /* brighter for AAA */
  /* no gradients, no shadows beyond shadow-sm */
  --shadow-glow: none;
}
```

---

## 5. Components

Every component is a contract, not a one-off. Three rules: **same markup, same classes, same ARIA**. No exceptions per page.

### 5.1 Global App Shell (every page)

A header (top nav) and a footer (action surface) appear on **every** page identically. Implement once, include everywhere.

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#000000">  /* matches data-theme */
  <link rel="stylesheet" href="/styles/theme.css">
</head>
<body class="bg-surface-page text-ink-primary antialiased font-sans">

  <header class="h-16 px-6 flex items-center justify-between
                 bg-surface-card border-b border-white/5
                 shadow-md sticky top-0 z-40">
    <a class="brand-title text-xl font-extrabold tracking-tight">
      MIA'S <span class="text-brand-orange">SPACE</span> COACH
    </a>
    <nav class="flex items-center gap-2">…</nav>
  </header>

  <main class="max-w-screen-xl mx-auto px-6 py-8">{slot}</main>

  <footer class="sticky bottom-0 bg-surface-card border-t border-white/5
                 shadow-md p-4 flex flex-col gap-3 z-40">
    {slot}
  </footer>

  <script type="module" src="/scripts/theme-sync.js"></script>
</body>
</html>
```

### 5.2 Card (with rainbow border)

Light theme: **static** rainbow border. Dark theme: **rotating** rainbow + cyan tracer. HC theme: no rainbow, plain 2px solid border.

```html
<div class="card-rainbow rounded-2xl bg-surface-card p-5 shadow-md">
  <div class="card-content">{slot}</div>
</div>
```

```css
/* Light: static rainbow stroke */
:root[data-theme="light"] .card-rainbow {
  background:
    linear-gradient(var(--color-surface-card), var(--color-surface-card)) padding-box,
    var(--gradient-rainbow) border-box;
  border: 1.5px solid transparent;
}

/* Dark: rotating rainbow + cyan tracer (speakeasy.com style) */
:root[data-theme="dark"] .card-rainbow {
  position: relative;
  background: var(--color-surface-card);
  border-radius: 16px;
  overflow: hidden;
}
:root[data-theme="dark"] .card-rainbow::before {
  content: ''; position: absolute; inset: 0; padding: 1.5px; border-radius: inherit;
  background: var(--gradient-rainbow);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  z-index: 2; pointer-events: none;
}
:root[data-theme="dark"] .card-rainbow::after {
  content: ''; position: absolute; inset: -50%;
  background: conic-gradient(from 0deg, transparent 65%, #00F0FF 90%, transparent 100%);
  animation: rotate-tracer var(--duration-tracer) linear infinite;
  z-index: 1; pointer-events: none;
}
@keyframes rotate-tracer { to { transform: rotate(360deg); } }

/* HC: flat border, no animation, no gradient */
:root[data-theme="hc"] .card-rainbow {
  border: 2px solid var(--color-ink-primary);
  background: var(--color-surface-card);
}
```

### 5.3 Button (3 variants × 3 themes)

| Variant | Light | Dark | HC |
| --- | --- | --- | --- |
| `btn-primary` | Orange fill, white text, static rainbow border on hover | Onyx fill, orange text, rotating rainbow border, cyan glow | Black fill, white text, 2px orange border |
| `btn-secondary` | Onyx text, transparent fill, 1px ink border | White text, transparent fill, 1px white/20 border | White text, 2px white border |
| `btn-ghost` | Text only, hover shows subtle surface tint | Text only, hover shows white/5 surface tint | Text only |

Touch target: **min 58×58** for icon-only buttons; **min 44px height** for text buttons.

### 5.4 Icon Button (64px large-icon variant)

```html
<button class="icon-target-btn" aria-label="Transmit">
  <span class="icon-lucide-send" style="color: var(--color-brand-orange)"></span>
</button>
```

```css
.icon-target-btn {
  min-width: 64px; min-height: 64px;
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: var(--radius-lg);
  background: var(--color-surface-raised);
  border: 1px solid oklch(0% 0 0 / 0.08);
  transition: transform var(--duration-fast) var(--easing-smooth),
              background var(--duration-default) var(--easing-smooth);
}
.icon-target-btn:active { transform: scale(0.96); }
```

### 5.5 Input

- Single line of padding-4, radius-lg, surface-raised fill, 1px ink/15 border.
- Focus: brand-orange border, shadow-glow.
- Always associated with a `<label>` (visually hidden if needed).

### 5.6 Toast

- Bottom-right, 4 from edge, max-width 360px.
- Auto-dismiss after 4s. Dismissible.
- Variants: `info`, `success`, `warning`, `error` — each maps to a brand color.

---

## 6. Animation Rules

| Use | Token | Notes |
| --- | --- | --- |
| Hover / focus | `duration-default` + `easing-smooth` | 280ms cubic-bezier(0.16, 1, 0.3, 1) |
| Press | `duration-fast` | transform: scale(0.96) |
| Rotating rainbow | `duration-tracer` (3500ms) | Dark theme only. **Honor `prefers-reduced-motion`** |
| Modal open | `duration-slow` | fade + 8px translateY |
| Theme switch | `duration-fast` | color transitions only, no layout shift |

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 7. Accessibility Baseline

- **Contrast:** all body text ≥ 4.5:1 against its surface; large text ≥ 3:1. Enforced via OKLCH lightness floors.
- **Focus visible:** 2px brand-orange outline, 2px offset, never `outline: none` without a replacement.
- **Touch targets:** ≥ 44×44 minimum, 64×64 for primary icon buttons.
- **Hit area:** extends 8px beyond visible icon for icon-only buttons.
- **Motion:** respects `prefers-reduced-motion` (see §6).
- **Color independence:** state never communicated by color alone — pair with icon or text.
- **Form labels:** every input has a programmatic label.

---

## 8. Anti-Patterns (do not do)

- **No inline hex.** Use tokens. The only acceptable hex is `#000` and `#fff` in the HC theme.
- **No hardcoded spacing.** `padding: 24px` is a smell; use `--space-6`.
- **No per-page color overrides.** If a token is wrong, change the token. Don't hardcode in a component.
- **No light shadow on dark surface, dark shadow on light surface.** Use `shadow-md` (universal) or define a `--shadow-md-dark` token.
- **No rainbow on decoration.** Rainbow is reserved for **primary CTAs, key cards, active states**. Not dividers, not icons, not text.
- **No "tracer" outside dark theme.** The rotating conic-gradient is the dark theme signature; light and HC do not animate.
- **No raw `<style>` blocks per page.** All styles live in `theme.css` and are token-driven.
- **No mixed theme per page.** One `data-theme` per page, set on `<html>`.
- **No JS for theme switching** beyond toggling the `data-theme` attribute. No class-based dark mode.
- **No `tailwind.config.js` color extension.** Tailwind v4 reads `@theme` from CSS — keep the source there.

---

## 9. Project Adoption Checklist

When starting a new project, copy **only** these three things:

1. `docs/design/tokens.json` — the token source.
2. `docs/design/theme.css` — the generated `@theme` block (§4 above).
3. `docs/design/components/` — header, footer, card, button, input, toast, theme-sync script.

Then:

- [ ] `<html data-theme="…">` is set on every page.
- [ ] `localStorage['agentcore-theme']` is read on first paint (inline script in `<head>`, before CSS, to prevent flash).
- [ ] Header and footer are identical markup on every page (rendered by the app shell, not by hand).
- [ ] All colors come from tokens (grep for `#[0-9a-f]{3,8}` in components returns only `#000` / `#fff`).
- [ ] All interactive elements have focus-visible styles.
- [ ] `prefers-reduced-motion` is respected.
- [ ] `axe-core` or equivalent a11y audit passes 0 critical issues.

---

## 10. Reference Look (visual targets, not source material)

These three sites are the visual benchmark — study them, do not copy them.

- **morphllm.com** — clean cards, generous spacing, calm typography. This is the "feels professional" target.
- **speakeasy.com** — the dark theme reference. Black + orange + rotating rainbow on primary CTAs. The "feels alive" target.
- **buildwithfern.com** — Apple-grade polish. Type scale, generous whitespace, frictionless interactions. The "feels premium" target.

The light theme leans Morph + Fern. The dark theme leans Speakeasy. The HC theme leans Apple Accessibility (Settings → Display → Increase Contrast).

---

## 11. Change Control

- Tokens are **locked**. To change a token value, open a PR with: old value, new value, affected components, before/after screenshots in **all three themes**.
- New theme = new section in `tokens.json` under `$themes`, new section here, new `@theme` block in `theme.css`. No exceptions.
- New component = new section in §5 with: HTML, CSS, all three theme variants, ARIA, a11y notes, anti-pattern callouts.
- Removing a component is a breaking change; deprecate for one Milestone, then remove.

---

*Last reviewed: 2026-08-20. Review trigger: any new framework adoption, any operator instruction, or any site whose aesthetic we cite that materially changes its design.*
