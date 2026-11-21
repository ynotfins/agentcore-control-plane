"""Restore RGDS web CSS into packages/web/css + dist; fix vite emptyOutDir."""
from __future__ import annotations

from pathlib import Path

SRC = Path(r"D:\github\agentcore-control-plane\docs\design\m3\css")
WEB = Path(r"D:\github\r3lentless-grind-design-system\packages\web")
CSS = WEB / "css"
DIST = WEB / "dist"
DST = Path(r"D:\github\r3lentless-grind-design-system")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print("W", path)


def transform_components(raw: str) -> str:
    raw = raw.replace(
        "filter: saturate(var(--md-sys-state-hover-saturate));",
        "/* chroma via color-mix tint tokens */",
    )
    raw = raw.replace("--md-sys-state-hover-tint-amount", "--md-rgds-state-hover-surface-tint-amount")
    raw = raw.replace("--md-sys-state-hover-tint", "--md-rgds-state-hover-surface-tint")
    raw = raw.replace("--md-sys-state-hover-border", "--md-rgds-state-hover-border-color")
    raw = raw.replace("--md-sys-state-hover-elevation", "--md-rgds-state-hover-elevation")
    raw = raw.replace(
        ".md-card:hover,\n.md-card:focus-within {",
        '.md-card[data-interactive="true"]:hover,\n.md-card[data-interactive="true"]:focus-within {',
    )
    extra = """
.rgds-field { display: flex; flex-direction: column; gap: var(--md-sys-spacing-xs); }
.rgds-field__label { font-size: var(--md-sys-typescale-label-large-size); font-weight: 600; }
.rgds-field__input {
  min-height: 48px; padding: var(--md-sys-spacing-sm) var(--md-sys-spacing-md);
  border-radius: var(--md-sys-shape-corner-medium);
  border: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface); font: inherit;
}
.rgds-field__input:focus-visible {
  outline: var(--md-rgds-state-focus-border-width) solid var(--md-rgds-state-focus-border-color);
  outline-offset: var(--md-rgds-state-focus-border-offset);
}
.rgds-badge {
  display: inline-flex; align-items: center; min-height: 24px;
  padding: 0 var(--md-sys-spacing-sm); border-radius: var(--md-sys-shape-corner-full);
  background: var(--md-sys-color-primary-container); color: var(--md-sys-color-on-primary-container);
  font-size: var(--md-sys-typescale-label-large-size); font-weight: 600;
}
.rgds-alert { padding: var(--md-sys-spacing-md); border-radius: var(--md-sys-shape-corner-medium);
  border: 1px solid var(--md-sys-color-outline-variant); }
.rgds-alert--info { background: var(--md-sys-color-info-container, var(--md-sys-color-primary-container)); }
.rgds-alert--success { background: var(--md-sys-color-success-container, var(--md-sys-color-secondary-container)); }
.rgds-alert--warning { background: var(--md-sys-color-warning-container, var(--md-sys-color-tertiary-container)); }
.rgds-alert--error { background: var(--md-sys-color-error-container); color: var(--md-sys-color-on-error-container); }
.rgds-btn--outlined { background: transparent; color: var(--md-sys-color-primary); border: 1px solid var(--md-sys-color-outline); }
.rgds-btn--text { background: transparent; color: var(--md-sys-color-primary); border: 1px solid transparent; box-shadow: none; }
"""
    return raw + "\n" + extra


def transform_tokens(raw: str) -> str:
    # Upgrade legacy hover vars to rgds namespace if present
    raw = raw.replace("--md-sys-state-hover-tint-amount", "--md-rgds-state-hover-surface-tint-amount")
    raw = raw.replace("--md-sys-state-hover-tint", "--md-rgds-state-hover-surface-tint")
    raw = raw.replace("--md-sys-state-hover-border", "--md-rgds-state-hover-border-color")
    raw = raw.replace("--md-sys-state-hover-elevation", "--md-rgds-state-hover-elevation")
    raw = raw.replace("--md-sys-state-hover-saturate", "--md-rgds-state-hover-chroma")
    if "--md-rgds-state-hover-surface-tint:" not in raw:
        raw += """
:root {
  --md-rgds-state-hover-surface-tint: var(--md-sys-color-primary);
  --md-rgds-state-hover-surface-tint-amount: 10%;
  --md-rgds-state-hover-border-color: var(--md-sys-color-outline);
  --md-rgds-state-hover-elevation: var(--md-sys-elevation-level3);
  --md-rgds-state-hover-icon-accent: var(--md-sys-color-primary);
  --md-rgds-state-focus-border-color: var(--md-sys-color-primary);
  --md-rgds-state-focus-border-width: 2px;
  --md-rgds-state-focus-border-offset: 2px;
  --md-rgds-state-pressed-surface-tint: var(--md-sys-color-on-surface);
  --md-rgds-state-pressed-surface-tint-amount: 8%;
  --md-rgds-state-pressed-scale: 0.98;
  --md-rgds-state-pressed-elevation: var(--md-sys-elevation-level1);
  --md-rgds-state-selected-surface: var(--md-sys-color-primary-container);
  --md-rgds-state-selected-on-surface: var(--md-sys-color-on-primary-container);
  --md-rgds-state-selected-border-color: var(--md-sys-color-primary);
  --md-rgds-state-disabled-opacity: 0.38;
  --md-sys-color-error: oklch(50% 0.20 25);
  --md-sys-color-on-error: #ffffff;
  --md-sys-color-error-container: oklch(90% 0.05 25);
  --md-sys-color-on-error-container: oklch(18% 0.08 25);
  --md-sys-color-success: oklch(52% 0.16 145);
  --md-sys-color-success-container: oklch(90% 0.04 145);
  --md-sys-color-warning: oklch(68% 0.18 55);
  --md-sys-color-warning-container: oklch(92% 0.05 55);
  --md-sys-color-info: oklch(50% 0.16 250);
  --md-sys-color-info-container: oklch(92% 0.04 250);
  --md-rgds-breakpoint-sm: 600px;
  --md-rgds-breakpoint-md: 905px;
  --md-rgds-breakpoint-lg: 1240px;
}
"""
    # Ensure theme blocks set hover tokens (AgentCore CSS already has hover vars under old names - rewritten above)
    return raw


INTERACTION = r"""
.rgds-interactive, .md-btn, .md-theme-btn, .md-nav-item, .md-list-tile, .md-tab, .md-menu-item,
.md-card[data-interactive="true"], button.rgds-interactive, a.rgds-interactive, [role="button"].rgds-interactive {
  transition:
    background-color var(--md-sys-motion-duration-medium) var(--md-sys-motion-easing-emphasized),
    border-color var(--md-sys-motion-duration-medium) var(--md-sys-motion-easing-emphasized),
    box-shadow var(--md-sys-motion-duration-medium) var(--md-sys-motion-easing-emphasized),
    color var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-emphasized),
    transform var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-emphasized);
}
.rgds-interactive:hover:not(:disabled):not([aria-disabled="true"]),
.md-btn:hover:not(:disabled), .md-theme-btn:hover:not(:disabled),
.md-card[data-interactive="true"]:hover {
  background: color-mix(in oklch, var(--rgds-surface-base, var(--md-sys-color-surface-container-high)) calc(100% - var(--md-rgds-state-hover-surface-tint-amount)), var(--md-rgds-state-hover-surface-tint) var(--md-rgds-state-hover-surface-tint-amount));
  border-color: var(--md-rgds-state-hover-border-color);
  box-shadow: var(--md-rgds-state-hover-elevation, var(--md-sys-elevation-level3));
}
.rgds-interactive:focus-visible, .md-btn:focus-visible, .md-theme-btn:focus-visible,
.md-card[data-interactive="true"]:focus-visible {
  outline: var(--md-rgds-state-focus-border-width) solid var(--md-rgds-state-focus-border-color);
  outline-offset: var(--md-rgds-state-focus-border-offset);
}
.rgds-interactive:active:not(:disabled), .md-btn:active:not(:disabled) {
  background: color-mix(in oklch, var(--rgds-surface-base, var(--md-sys-color-surface-container-high)) calc(100% - var(--md-rgds-state-pressed-surface-tint-amount)), var(--md-rgds-state-pressed-surface-tint) var(--md-rgds-state-pressed-surface-tint-amount));
  box-shadow: var(--md-rgds-state-pressed-elevation);
  transform: scale(var(--md-rgds-state-pressed-scale));
}
.rgds-interactive[aria-pressed="true"], .rgds-interactive[aria-selected="true"],
.md-theme-btn[aria-pressed="true"] {
  background: var(--md-rgds-state-selected-surface);
  color: var(--md-rgds-state-selected-on-surface, var(--md-sys-color-on-primary-container));
  border-color: var(--md-rgds-state-selected-border-color);
}
.rgds-interactive:disabled, .rgds-interactive[aria-disabled="true"], .md-btn:disabled {
  opacity: var(--md-rgds-state-disabled-opacity); cursor: not-allowed; box-shadow: none; transform: none; pointer-events: none;
}
.rgds-state-hover {
  background: color-mix(in oklch, var(--rgds-surface-base, var(--md-sys-color-surface-container-high)) calc(100% - var(--md-rgds-state-hover-surface-tint-amount)), var(--md-rgds-state-hover-surface-tint) var(--md-rgds-state-hover-surface-tint-amount)) !important;
  border-color: var(--md-rgds-state-hover-border-color) !important;
  box-shadow: var(--md-rgds-state-hover-elevation, var(--md-sys-elevation-level3)) !important;
}
.rgds-state-focus { outline: var(--md-rgds-state-focus-border-width) solid var(--md-rgds-state-focus-border-color) !important; outline-offset: var(--md-rgds-state-focus-border-offset) !important; }
.rgds-state-pressed {
  background: color-mix(in oklch, var(--rgds-surface-base, var(--md-sys-color-surface-container-high)) calc(100% - var(--md-rgds-state-pressed-surface-tint-amount)), var(--md-rgds-state-pressed-surface-tint) var(--md-rgds-state-pressed-surface-tint-amount)) !important;
  transform: scale(var(--md-rgds-state-pressed-scale)) !important;
}
.rgds-state-selected { background: var(--md-rgds-state-selected-surface) !important; border-color: var(--md-rgds-state-selected-border-color) !important; }
.rgds-state-disabled { opacity: var(--md-rgds-state-disabled-opacity) !important; box-shadow: none !important; }
@media (prefers-reduced-motion: reduce) {
  .rgds-interactive, .md-btn, .md-theme-btn, .md-card[data-interactive="true"], .md-rainbow-pulse {
    transition: none !important; animation: none !important; transform: none !important;
  }
}
"""


def main() -> None:
    tokens = transform_tokens((SRC / "tokens.css").read_text(encoding="utf-8"))
    components = transform_components((SRC / "components.css").read_text(encoding="utf-8"))
    animations = (SRC / "animations.css").read_text(encoding="utf-8")

    for folder in (CSS, DIST):
        write(folder / "tokens.css", tokens)
        write(folder / "components.css", components)
        write(folder / "animations.css", animations)
        write(folder / "interaction.css", INTERACTION)

    # vite: do not wipe css
    vite = (WEB / "vite.config.ts").read_text(encoding="utf-8")
    if "emptyOutDir" not in vite:
        vite = vite.replace(
            "build: {",
            "build: {\n    emptyOutDir: false,",
        )
        write(WEB / "vite.config.ts", vite)

    write(
        WEB / "src/components.test.ts",
        """import { describe, expect, it } from "vitest";
import { RGDS_THEMES, applyRgdsTheme } from "./theme";

describe("RGDS themes", () => {
  it("exposes exactly four themes", () => {
    expect(RGDS_THEMES).toHaveLength(4);
  });
  it("applyRgdsTheme sets data-theme on element", () => {
    const el = { attrs: {} as Record<string, string>, setAttribute(k: string, v: string) { this.attrs[k] = v; }, getAttribute(k: string) { return this.attrs[k] ?? null; } };
    applyRgdsTheme("primary-dark", el as unknown as HTMLElement);
    expect(el.getAttribute("data-theme")).toBe("primary-dark");
  });
});
""",
    )

    pkg = (WEB / "package.json").read_text(encoding="utf-8")
    if '"test": "vitest run"' in pkg and "happy-dom" not in pkg:
        pkg = pkg.replace(
            '"test": "vitest run"',
            '"test": "vitest run --environment node"',
        )
        write(WEB / "package.json", pkg)

    write(
        DST / "tools/copy-css-into-dist.mjs",
        """import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const cssDir = join(root, "packages", "web", "css");
const dist = join(root, "packages", "web", "dist");
mkdirSync(dist, { recursive: true });
for (const f of ["tokens.css", "interaction.css", "components.css", "animations.css"]) {
  const src = join(cssDir, f);
  if (!existsSync(src)) { console.error("missing", src); process.exit(1); }
  writeFileSync(join(dist, f), readFileSync(src));
}
console.log("css synced css/ -> dist/");
""",
    )
    print("css restore complete")


if __name__ == "__main__":
    main()
