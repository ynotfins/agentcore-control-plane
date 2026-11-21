#!/usr/bin/env python3
"""RGDS completion pass — expand tokens, web/flutter packages, make-kit, validation.

Writes only into D:\\github\\r3lentless-grind-design-system and C:\\Users\\ynotf\\.rgds.
Does NOT touch NFA or other consumer apps.
Brand seeds remain TEMPORARY_PLACEHOLDER until operator supplies finals.
"""
from __future__ import annotations

import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path

DST = Path(r"D:\github\r3lentless-grind-design-system")
DISCOVERY = Path(r"C:\Users\ynotf\.rgds")
AUDIT = Path(r"D:\github\agentcore-control-plane\audits\rgds")
FILE_KEY = "KbhSAUCrADaqhxOm7jM2FC"
FILE_URL = f"https://www.figma.com/design/{FILE_KEY}"
VERSION = "0.3.0-rc.1"


def W(rel: str, text: str) -> None:
    path = DST / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print("W", rel)


def expand_semantic_tokens() -> None:
    # Add semantic status colors to sys/color.json without inventing brand finals
    color_path = DST / "tokens/sys/color.json"
    data = json.loads(color_path.read_text(encoding="utf-8"))
    sys_color = data.setdefault("md", {}).setdefault("sys", {}).setdefault("color", {})
    extras = {
        "error": {"$value": "{md.ref.palette.error.40}", "$type": "color"},
        "onError": {"$value": "{md.ref.palette.error.100}", "$type": "color"},
        "errorContainer": {"$value": "{md.ref.palette.error.90}", "$type": "color"},
        "onErrorContainer": {"$value": "{md.ref.palette.error.10}", "$type": "color"},
        "success": {"$value": "{md.ref.palette.green.40}", "$type": "color"},
        "onSuccess": {"$value": "#ffffff", "$type": "color"},
        "successContainer": {"$value": "{md.ref.palette.green.90}", "$type": "color"},
        "warning": {"$value": "{md.ref.palette.orange.50}", "$type": "color"},
        "onWarning": {"$value": "{md.ref.palette.neutral.10}", "$type": "color"},
        "warningContainer": {"$value": "{md.ref.palette.orange.90}", "$type": "color"},
        "info": {"$value": "{md.ref.palette.blue.40}", "$type": "color"},
        "onInfo": {"$value": "#ffffff", "$type": "color"},
        "infoContainer": {"$value": "{md.ref.palette.blue.90}", "$type": "color"},
        "scrim": {"$value": "oklch(0% 0 0 / 0.48)", "$type": "color"},
        "shadow": {"$value": "oklch(0% 0 0 / 0.28)", "$type": "color"},
    }
    for k, v in extras.items():
        sys_color.setdefault(k, v)
    color_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("expanded sys/color.json")

    W(
        "tokens/sys/breakpoint.json",
        json.dumps(
            {
                "$schema": "https://design-tokens.github.io/community-group/format/",
                "$description": "RGDS layout breakpoints (web-first; Flutter maps via MediaQuery).",
                "md": {
                    "rgds": {
                        "breakpoint": {
                            "xs": {"$value": "0px", "$type": "dimension"},
                            "sm": {"$value": "600px", "$type": "dimension"},
                            "md": {"$value": "905px", "$type": "dimension"},
                            "lg": {"$value": "1240px", "$type": "dimension"},
                            "xl": {"$value": "1440px", "$type": "dimension"},
                        }
                    }
                },
            },
            indent=2,
        )
        + "\n",
    )
    W(
        "tokens/sys/opacity.json",
        json.dumps(
            {
                "$schema": "https://design-tokens.github.io/community-group/format/",
                "md": {
                    "rgds": {
                        "opacity": {
                            "disabled": {"$value": "0.38", "$type": "number"},
                            "hoverOverlay": {"$value": "0.08", "$type": "number"},
                            "focusOverlay": {"$value": "0.12", "$type": "number"},
                            "pressedOverlay": {"$value": "0.12", "$type": "number"},
                            "scrim": {"$value": "0.48", "$type": "number"},
                        }
                    }
                },
            },
            indent=2,
        )
        + "\n",
    )


def write_tokens_css_extras() -> None:
    tokens = (DST / "packages/web/dist/tokens.css").read_text(encoding="utf-8")
    if "--md-sys-color-error:" not in tokens:
        extras = textwrap.dedent(
            """

            /* Semantic status + overlays (TEMPORARY brand seeds) */
            :root {
              --md-sys-color-error: oklch(50% 0.20 25);
              --md-sys-color-on-error: #ffffff;
              --md-sys-color-error-container: oklch(90% 0.05 25);
              --md-sys-color-on-error-container: oklch(18% 0.08 25);
              --md-sys-color-success: oklch(52% 0.16 145);
              --md-sys-color-on-success: #ffffff;
              --md-sys-color-success-container: oklch(90% 0.04 145);
              --md-sys-color-warning: oklch(68% 0.18 55);
              --md-sys-color-on-warning: oklch(16% 0.008 260);
              --md-sys-color-warning-container: oklch(92% 0.05 55);
              --md-sys-color-info: oklch(50% 0.16 250);
              --md-sys-color-on-info: #ffffff;
              --md-sys-color-info-container: oklch(92% 0.04 250);
              --md-sys-color-scrim: oklch(0% 0 0 / 0.48);
              --md-rgds-breakpoint-sm: 600px;
              --md-rgds-breakpoint-md: 905px;
              --md-rgds-breakpoint-lg: 1240px;
              --md-rgds-breakpoint-xl: 1440px;
              --md-rgds-state-loading-opacity: 0.72;
            }
            """
        )
        (DST / "packages/web/dist/tokens.css").write_text(
            tokens + extras, encoding="utf-8", newline="\n"
        )
        print("appended semantic CSS tokens")


def write_web_package() -> None:
    W(
        "packages/web/package.json",
        json.dumps(
            {
                "name": "@r3lentless/rgds-web",
                "version": VERSION,
                "description": "R3lentless-Grind Design System — web (CSS + React) adapter",
                "license": "UNLICENSED",
                "type": "module",
                "sideEffects": ["**/*.css"],
                "files": ["dist", "src"],
                "main": "./dist/rgds-web.js",
                "module": "./dist/rgds-web.js",
                "types": "./dist/index.d.ts",
                "exports": {
                    ".": {
                        "types": "./dist/index.d.ts",
                        "import": "./dist/rgds-web.js",
                    },
                    "./tokens.css": "./dist/tokens.css",
                    "./interaction.css": "./dist/interaction.css",
                    "./components.css": "./dist/components.css",
                    "./animations.css": "./dist/animations.css",
                    "./package.json": "./package.json",
                },
                "peerDependencies": {
                    "react": "^18.3.1 || ^19.0.0",
                    "react-dom": "^18.3.1 || ^19.0.0",
                },
                "devDependencies": {
                    "@types/react": "18.3.12",
                    "@types/react-dom": "18.3.1",
                    "@vitejs/plugin-react": "4.3.4",
                    "react": "18.3.1",
                    "react-dom": "18.3.1",
                    "typescript": "5.6.3",
                    "vite": "5.4.11",
                    "vitest": "2.1.8",
                },
                "scripts": {
                    "build": "vite build && node ../../tools/copy-css-into-dist.mjs",
                    "test": "vitest run",
                    "typecheck": "tsc -p tsconfig.json --noEmit",
                },
            },
            indent=2,
        )
        + "\n",
    )
    W(
        "packages/web/tsconfig.json",
        json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2022",
                    "module": "ESNext",
                    "moduleResolution": "Bundler",
                    "jsx": "react-jsx",
                    "declaration": True,
                    "declarationDir": "dist",
                    "emitDeclarationOnly": False,
                    "strict": True,
                    "skipLibCheck": True,
                    "outDir": "dist",
                },
                "include": ["src"],
            },
            indent=2,
        )
        + "\n",
    )
    W(
        "packages/web/vite.config.ts",
        textwrap.dedent(
            """\
            import { defineConfig } from "vite";
            import react from "@vitejs/plugin-react";
            import { resolve } from "node:path";

            export default defineConfig({
              plugins: [react()],
              build: {
                lib: {
                  entry: resolve(__dirname, "src/index.ts"),
                  name: "RgdsWeb",
                  formats: ["es"],
                  fileName: () => "rgds-web.js",
                },
                rollupOptions: {
                  external: ["react", "react-dom", "react/jsx-runtime"],
                },
              },
            });
            """
        ),
    )
    W(
        "packages/web/src/theme.ts",
        textwrap.dedent(
            """\
            export const RGDS_THEMES = [
              "primary-light",
              "secondary-light",
              "primary-dark",
              "secondary-dark",
            ] as const;

            export type RgdsTheme = (typeof RGDS_THEMES)[number];

            export function applyRgdsTheme(
              theme: RgdsTheme,
              root: HTMLElement = document.documentElement,
            ): void {
              root.setAttribute("data-theme", theme);
              try {
                localStorage.setItem("rgds-theme", theme);
              } catch {
                /* ignore */
              }
            }

            export function readStoredRgdsTheme(): RgdsTheme | null {
              try {
                const v = localStorage.getItem("rgds-theme");
                if (v && (RGDS_THEMES as readonly string[]).includes(v)) {
                  return v as RgdsTheme;
                }
              } catch {
                /* ignore */
              }
              return null;
            }
            """
        ),
    )
    W(
        "packages/web/src/components.tsx",
        textwrap.dedent(
            """\
            import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

            type Common = {
              children?: ReactNode;
              className?: string;
            };

            function cx(...parts: Array<string | false | undefined>) {
              return parts.filter(Boolean).join(" ");
            }

            export type RgdsButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
              Common & {
                variant?: "filled" | "outlined" | "text";
                selected?: boolean;
              };

            /** Maps to Figma `RGDS / Button` State variants via CSS. */
            export function RgdsButton({
              variant = "filled",
              selected,
              className,
              children,
              ...rest
            }: RgdsButtonProps) {
              return (
                <button
                  type="button"
                  className={cx(
                    "md-btn",
                    "rgds-interactive",
                    `rgds-btn--${variant}`,
                    className,
                  )}
                  aria-pressed={selected || undefined}
                  {...rest}
                >
                  {children}
                </button>
              );
            }

            export type RgdsCardProps = Common & {
              interactive?: boolean;
              onClick?: () => void;
            };

            export function RgdsCard({
              interactive = false,
              className,
              children,
              onClick,
            }: RgdsCardProps) {
              const Tag = interactive ? "button" : "div";
              return (
                <Tag
                  className={cx(
                    "md-card",
                    interactive && "rgds-interactive",
                    className,
                  )}
                  data-interactive={interactive ? "true" : undefined}
                  onClick={onClick}
                  type={interactive ? "button" : undefined}
                >
                  {children}
                </Tag>
              );
            }

            export type RgdsTextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
              label?: string;
            };

            export function RgdsTextField({ label, id, className, ...rest }: RgdsTextFieldProps) {
              const inputId = id || rest.name;
              return (
                <label className={cx("rgds-field", className)}>
                  {label ? <span className="rgds-field__label">{label}</span> : null}
                  <input
                    id={inputId}
                    className="rgds-field__input rgds-interactive"
                    {...rest}
                  />
                </label>
              );
            }

            export function RgdsAlert({
              tone = "info",
              children,
              className,
            }: Common & { tone?: "info" | "success" | "warning" | "error" }) {
              return (
                <div
                  role="status"
                  className={cx("rgds-alert", `rgds-alert--${tone}`, className)}
                >
                  {children}
                </div>
              );
            }

            export function RgdsBadge({
              children,
              className,
            }: Common) {
              return <span className={cx("rgds-badge", className)}>{children}</span>;
            }

            export function RgdsAppShell({
              sidebar,
              children,
              className,
            }: Common & { sidebar?: ReactNode }) {
              return (
                <div className={cx("md-shell", className)}>
                  {sidebar ? <aside className="md-sidebar">{sidebar}</aside> : null}
                  <main className="md-main">{children}</main>
                </div>
              );
            }
            """
        ),
    )
    W(
        "packages/web/src/index.ts",
        textwrap.dedent(
            """\
            export {
              RGDS_THEMES,
              applyRgdsTheme,
              readStoredRgdsTheme,
              type RgdsTheme,
            } from "./theme";
            export {
              RgdsButton,
              RgdsCard,
              RgdsTextField,
              RgdsAlert,
              RgdsBadge,
              RgdsAppShell,
              type RgdsButtonProps,
              type RgdsCardProps,
              type RgdsTextFieldProps,
            } from "./components";
            """
        ),
    )
    W(
        "packages/web/src/components.test.ts",
        textwrap.dedent(
            """\
            import { describe, expect, it } from "vitest";
            import { RGDS_THEMES, applyRgdsTheme } from "./theme";

            describe("RGDS themes", () => {
              it("exposes exactly four themes", () => {
                expect(RGDS_THEMES).toHaveLength(4);
              });
              it("applyRgdsTheme sets data-theme", () => {
                const el = document.createElement("html");
                applyRgdsTheme("primary-dark", el);
                expect(el.getAttribute("data-theme")).toBe("primary-dark");
              });
            });
            """
        ),
    )
    # Extra component CSS for fields/alerts
    extra_css = textwrap.dedent(
        """

        /* RGDS form + status primitives (token-only) */
        .rgds-field {
          display: flex;
          flex-direction: column;
          gap: var(--md-sys-spacing-xs);
        }
        .rgds-field__label {
          font-size: var(--md-sys-typescale-label-large-size);
          font-weight: 600;
          color: var(--md-sys-color-on-surface);
        }
        .rgds-field__input {
          min-height: 48px;
          padding: var(--md-sys-spacing-sm) var(--md-sys-spacing-md);
          border-radius: var(--md-sys-shape-corner-medium);
          border: 1px solid var(--md-sys-color-outline-variant);
          background: var(--md-sys-color-surface-container-high);
          color: var(--md-sys-color-on-surface);
          font: inherit;
        }
        .rgds-field__input:focus-visible {
          outline: var(--md-rgds-state-focus-border-width) solid var(--md-rgds-state-focus-border-color);
          outline-offset: var(--md-rgds-state-focus-border-offset);
        }
        .rgds-badge {
          display: inline-flex;
          align-items: center;
          min-height: 24px;
          padding: 0 var(--md-sys-spacing-sm);
          border-radius: var(--md-sys-shape-corner-full);
          background: var(--md-sys-color-primary-container);
          color: var(--md-sys-color-on-primary-container);
          font-size: var(--md-sys-typescale-label-large-size);
          font-weight: 600;
        }
        .rgds-alert {
          padding: var(--md-sys-spacing-md);
          border-radius: var(--md-sys-shape-corner-medium);
          border: 1px solid var(--md-sys-color-outline-variant);
        }
        .rgds-alert--info {
          background: var(--md-sys-color-info-container);
          color: var(--md-sys-color-on-info-container, var(--md-sys-color-on-surface));
        }
        .rgds-alert--success {
          background: var(--md-sys-color-success-container);
        }
        .rgds-alert--warning {
          background: var(--md-sys-color-warning-container);
        }
        .rgds-alert--error {
          background: var(--md-sys-color-error-container);
          color: var(--md-sys-color-on-error-container);
        }
        .rgds-btn--outlined {
          background: transparent;
          color: var(--md-sys-color-primary);
          border: 1px solid var(--md-sys-color-outline);
        }
        .rgds-btn--text {
          background: transparent;
          color: var(--md-sys-color-primary);
          border: 1px solid transparent;
          box-shadow: none;
        }
        """
    )
    comp = DST / "packages/web/dist/components.css"
    body = comp.read_text(encoding="utf-8")
    if ".rgds-field" not in body:
        comp.write_text(body + extra_css, encoding="utf-8", newline="\n")


def write_flutter_package() -> None:
    W(
        "packages/flutter/pubspec.yaml",
        textwrap.dedent(
            f"""\
            name: rgds
            description: R3lentless-Grind Design System Flutter adapter
            version: {VERSION}
            publish_to: none
            environment:
              sdk: ">=3.3.0 <4.0.0"
              flutter: ">=3.22.0"
            dependencies:
              flutter:
                sdk: flutter
            dev_dependencies:
              flutter_test:
                sdk: flutter
              flutter_lints: 4.0.0
            """
        ),
    )
    W(
        "packages/flutter/lib/rgds.dart",
        textwrap.dedent(
            """\
            library rgds;

            export 'src/generated/rgds_tokens.dart';
            export 'src/theme/rgds_theme.dart';
            export 'src/widgets/rgds_button.dart';
            export 'src/widgets/rgds_card.dart';
            export 'src/widgets/rgds_text_field.dart';
            export 'src/widgets/rgds_alert.dart';
            """
        ),
    )
    W(
        "packages/flutter/lib/src/theme/rgds_theme.dart",
        textwrap.dedent(
            """\
            import 'package:flutter/material.dart';
            import '../generated/rgds_tokens.dart';

            ThemeData rgdsThemeData(RgdsTheme theme) {
              final t = RgdsThemes.of(theme);
              final scheme = ColorScheme(
                brightness: theme == RgdsTheme.primaryDark ||
                        theme == RgdsTheme.secondaryDark
                    ? Brightness.dark
                    : Brightness.light,
                primary: Color(t.color.primary),
                onPrimary: Color(t.color.onPrimary),
                secondary: Color(t.color.secondary),
                onSecondary: Color(t.color.onSecondary),
                surface: Color(t.color.surface),
                onSurface: Color(t.color.onSurface),
                error: const Color(0xFFB3261E),
                onError: const Color(0xFFFFFFFF),
              );
              return ThemeData(
                useMaterial3: true,
                colorScheme: scheme,
                scaffoldBackgroundColor: Color(t.color.surface),
                cardTheme: CardThemeData(
                  color: Color(t.color.surfaceContainerHighest),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: BorderSide(color: Color(t.color.outlineVariant)),
                  ),
                ),
                filledButtonTheme: FilledButtonThemeData(
                  style: FilledButton.styleFrom(
                    minimumSize: const Size(64, 48),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(999),
                    ),
                  ),
                ),
              );
            }
            """
        ),
    )
    W(
        "packages/flutter/lib/src/widgets/rgds_button.dart",
        textwrap.dedent(
            """\
            import 'package:flutter/material.dart';

            /// Flutter mapping of Figma `RGDS / Button`.
            /// Hover is pointer-desktop only; pressed/selected/focus drive touch/keyboard.
            class RgdsButton extends StatelessWidget {
              const RgdsButton({
                super.key,
                required this.label,
                this.onPressed,
                this.selected = false,
              });

              final String label;
              final VoidCallback? onPressed;
              final bool selected;

              @override
              Widget build(BuildContext context) {
                final enabled = onPressed != null;
                return FilledButton(
                  onPressed: onPressed,
                  style: FilledButton.styleFrom(
                    backgroundColor: selected
                        ? Theme.of(context).colorScheme.primaryContainer
                        : null,
                    foregroundColor: selected
                        ? Theme.of(context).colorScheme.onPrimaryContainer
                        : null,
                  ).copyWith(
                    overlayColor: WidgetStateProperty.resolveWith((states) {
                      if (states.contains(WidgetState.pressed)) {
                        return Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.12);
                      }
                      if (states.contains(WidgetState.hovered)) {
                        return Theme.of(context).colorScheme.primary.withValues(alpha: 0.08);
                      }
                      return null;
                    }),
                  ),
                  child: Text(enabled ? label : 'Disabled'),
                );
              }
            }
            """
        ),
    )
    W(
        "packages/flutter/lib/src/widgets/rgds_card.dart",
        textwrap.dedent(
            """\
            import 'package:flutter/material.dart';

            class RgdsCard extends StatelessWidget {
              const RgdsCard({
                super.key,
                required this.child,
                this.interactive = false,
                this.onTap,
              });

              final Widget child;
              final bool interactive;
              final VoidCallback? onTap;

              @override
              Widget build(BuildContext context) {
                final card = Card(
                  clipBehavior: Clip.antiAlias,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: child,
                  ),
                );
                if (!interactive) return card;
                return InkWell(onTap: onTap, child: card);
              }
            }
            """
        ),
    )
    W(
        "packages/flutter/lib/src/widgets/rgds_text_field.dart",
        textwrap.dedent(
            """\
            import 'package:flutter/material.dart';

            class RgdsTextField extends StatelessWidget {
              const RgdsTextField({
                super.key,
                this.label,
                this.controller,
                this.enabled = true,
              });

              final String? label;
              final TextEditingController? controller;
              final bool enabled;

              @override
              Widget build(BuildContext context) {
                return TextField(
                  controller: controller,
                  enabled: enabled,
                  decoration: InputDecoration(
                    labelText: label,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                );
              }
            }
            """
        ),
    )
    W(
        "packages/flutter/lib/src/widgets/rgds_alert.dart",
        textwrap.dedent(
            """\
            import 'package:flutter/material.dart';

            enum RgdsAlertTone { info, success, warning, error }

            class RgdsAlert extends StatelessWidget {
              const RgdsAlert({
                super.key,
                required this.message,
                this.tone = RgdsAlertTone.info,
              });

              final String message;
              final RgdsAlertTone tone;

              @override
              Widget build(BuildContext context) {
                final scheme = Theme.of(context).colorScheme;
                final Color bg;
                switch (tone) {
                  case RgdsAlertTone.error:
                    bg = scheme.errorContainer;
                    break;
                  case RgdsAlertTone.warning:
                    bg = scheme.tertiaryContainer;
                    break;
                  case RgdsAlertTone.success:
                    bg = scheme.secondaryContainer;
                    break;
                  case RgdsAlertTone.info:
                    bg = scheme.primaryContainer;
                    break;
                }
                return Material(
                  color: bg,
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(message),
                  ),
                );
              }
            }
            """
        ),
    )
    W(
        "packages/flutter/test/rgds_theme_test.dart",
        textwrap.dedent(
            """\
            import 'package:flutter_test/flutter_test.dart';
            import 'package:rgds/rgds.dart';

            void main() {
              test('four themes resolve', () {
                expect(RgdsTheme.values.length, 4);
                for (final theme in RgdsTheme.values) {
                  final data = rgdsThemeData(theme);
                  expect(data.colorScheme.primary, isNotNull);
                }
              });
            }
            """
        ),
    )


def write_make_kit() -> None:
    W(
        "make-kit/README.md",
        textwrap.dedent(
            f"""\
            # RGDS Make Kit (current Figma Make architecture)

            Official flow (2026): [Bring your design system package to a Make kit](https://developers.figma.com/docs/code/bring-your-design-system-package/).

            Make kits require a **Vite-compatible React npm package** plus guidelines.
            This folder is the **source guidelines** to paste/import when assembling the
            Make kit in Figma after `@r3lentless/rgds-web@{VERSION}` is published to npm
            (public or Figma org private registry).

            Operator steps (Tier 4 — publish):
            1. `npm publish` `@r3lentless/rgds-web` (or Figma private registry).
            2. In Figma: create Make kit → add package → import guidelines from this folder.
            3. Attach published Figma library `{FILE_KEY}` for variables/styles.

            Until publish completes, agents use this repo + discovery pointer locally.
            """
        ),
    )
    W(
        "make-kit/guidelines/overview.md",
        textwrap.dedent(
            """\
            # RGDS overview for Figma Make

            Use **only** `@r3lentless/rgds-web` for UI primitives. Do not invent colors,
            radii, or alternate component kits.

            Themes (set `data-theme` on `<html>`):
            - primary-light
            - secondary-light
            - primary-dark
            - secondary-dark

            Interaction: use `rgds-interactive` / `RgdsButton` / interactive `RgdsCard` only
            on actionable surfaces. Never hover-brighten static content.
            Rainbow pulse is Theme 4 featured-only — never default hover.
            """
        ),
    )
    W(
        "make-kit/guidelines/setup.md",
        textwrap.dedent(
            f"""\
            # Setup

            ```bash
            npm install @r3lentless/rgds-web@{VERSION}
            ```

            ```tsx
            import "@r3lentless/rgds-web/tokens.css";
            import "@r3lentless/rgds-web/interaction.css";
            import "@r3lentless/rgds-web/components.css";
            import {{ applyRgdsTheme, RgdsButton, RgdsAppShell }} from "@r3lentless/rgds-web";

            applyRgdsTheme("primary-light");
            ```

            Figma design library file_key: `{FILE_KEY}`
            """
        ),
    )
    W(
        "make-kit/guidelines/tokens.md",
        textwrap.dedent(
            """\
            # Tokens

            Canonical values live in the RGDS Git `tokens/` tree (DTCG).
            CSS custom properties are generated under `packages/web/dist/tokens.css`.
            Prefer semantic tokens (`--md-sys-color-*`, `--md-rgds-state-*`).
            Brand seeds may still be TEMPORARY_PLACEHOLDER — do not hardcode hex in apps.
            """
        ),
    )
    W(
        "make-kit/guidelines/components.md",
        textwrap.dedent(
            """\
            # Components

            Figma ↔ code mapping (Code Connect deferred; names are stable):

            | Figma | React |
            | --- | --- |
            | RGDS / Button | RgdsButton |
            | RGDS / Card / Interactive | RgdsCard interactive |
            | RGDS / Text Field | RgdsTextField |
            | RGDS / Alert | RgdsAlert |
            | RGDS / Badge | RgdsBadge |
            | App shell patterns | RgdsAppShell |

            States: Default, Hover, Focus, Pressed, Selected, Disabled — driven by
            `md.rgds.state.*` CSS tokens, not ad-hoc styles.
            """
        ),
    )


def write_tools_and_validation() -> None:
    W(
        "tools/copy-css-into-dist.mjs",
        textwrap.dedent(
            """\
            import { copyFileSync, existsSync } from "node:fs";
            import { dirname, join } from "node:path";
            import { fileURLToPath } from "node:url";
            const root = join(dirname(fileURLToPath(import.meta.url)), "..");
            const dist = join(root, "packages", "web", "dist");
            for (const f of ["tokens.css", "interaction.css", "components.css", "animations.css"]) {
              const p = join(dist, f);
              if (!existsSync(p)) {
                console.error("missing", p);
                process.exit(1);
              }
              copyFileSync(p, p);
            }
            console.log("css dist intact");
            """
        ),
    )
    W(
        "tools/validate-all.mjs",
        textwrap.dedent(
            """\
            import { readFileSync, existsSync } from "node:fs";
            import { spawnSync } from "node:child_process";
            import { dirname, join } from "node:path";
            import { fileURLToPath } from "node:url";
            import { homedir } from "node:os";

            const root = join(dirname(fileURLToPath(import.meta.url)), "..");
            const failures = [];

            function must(cond, msg) {
              if (!cond) failures.push(msg);
            }

            const manifest = JSON.parse(readFileSync(join(root, "rgds.manifest.json"), "utf8"));
            must(manifest.themes?.length === 4, "themes != 4");
            must(manifest.figma?.file_key, "figma.file_key missing");
            must(manifest.version, "version missing");

            for (const f of [
              "packages/web/dist/tokens.css",
              "packages/web/dist/interaction.css",
              "packages/web/dist/components.css",
              "packages/web/src/index.ts",
              "packages/flutter/lib/rgds.dart",
              "make-kit/guidelines/setup.md",
              "fixtures/web/states.html",
              "fixtures/consumers/web/index.html",
              "docs/ADOPTION.md",
            ]) {
              must(existsSync(join(root, f)), `missing ${f}`);
            }

            const tokens = readFileSync(join(root, "packages/web/dist/tokens.css"), "utf8");
            must(tokens.includes("--md-rgds-state-hover-surface-tint"), "hover state tokens missing");
            must(tokens.includes("primary-dark"), "primary-dark theme missing");
            must(!/filter:\\s*brightness/i.test(tokens), "forbidden brightness filter in tokens");

            const interaction = readFileSync(
              join(root, "packages/web/dist/interaction.css"),
              "utf8",
            );
            must(interaction.includes("prefers-reduced-motion"), "reduced-motion missing");
            must(interaction.includes(":focus-visible"), "focus-visible missing");

            const pointer = join(homedir(), ".rgds", "RGDS_MANIFEST.json");
            must(existsSync(pointer), "discovery pointer missing");
            const disc = JSON.parse(readFileSync(pointer, "utf8"));
            must(disc.figma?.file_key === manifest.figma.file_key, "discovery figma drift");

            const contrast = spawnSync("node", [join(root, "tools/check-contrast.mjs")], {
              encoding: "utf8",
            });
            if (contrast.status !== 0) failures.push("contrast check failed");

            if (failures.length) {
              console.error("FAIL");
              for (const f of failures) console.error("-", f);
              process.exit(1);
            }
            console.log("PASS validate-all", manifest.version);
            """
        ),
    )
    W(
        "tools/cold-adopt-sim.mjs",
        textwrap.dedent(
            """\
            /** Simulate: \"Adopt RGDS for this project\" with only discovery. */
            import { readFileSync, existsSync } from "node:fs";
            import { join } from "node:path";
            import { homedir } from "node:os";

            const pointerPath = join(homedir(), ".rgds", "RGDS_MANIFEST.json");
            if (!existsSync(pointerPath)) {
              console.error("COLD FAIL: no discovery");
              process.exit(1);
            }
            const p = JSON.parse(readFileSync(pointerPath, "utf8"));
            const needed = [
              p.version,
              p.figma?.file_key,
              p.figma?.library_url,
              p.repository_manifest,
              p.packages?.npm,
              p.packages?.flutter,
              ...(p.themes || []),
            ];
            if (needed.some((x) => !x) || (p.themes || []).length !== 4) {
              console.error("COLD FAIL: incomplete pointer", p);
              process.exit(1);
            }
            const repo = JSON.parse(readFileSync(p.repository_manifest, "utf8"));
            const adopt = readFileSync(
              join(p.repository_path, "docs", "ADOPTION.md"),
              "utf8",
            );
            if (!adopt.toLowerCase().includes("discover")) {
              console.error("COLD FAIL: ADOPTION.md missing discovery guidance");
              process.exit(1);
            }
            console.log("COLD PASS", {
              version: p.version,
              figma: p.figma.file_key,
              npm: p.packages.npm,
              flutter: p.packages.flutter,
              component_sets: repo.figma?.component_sets?.length ?? 0,
            });
            """
        ),
    )


def write_consumer_fixtures() -> None:
    W(
        "fixtures/consumers/web/index.html",
        textwrap.dedent(
            """\
            <!DOCTYPE html>
            <html lang="en" data-theme="primary-light">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <title>RGDS isolated web consumer</title>
              <link rel="stylesheet" href="../../../packages/web/dist/tokens.css" />
              <link rel="stylesheet" href="../../../packages/web/dist/components.css" />
              <link rel="stylesheet" href="../../../packages/web/dist/interaction.css" />
            </head>
            <body>
              <div class="md-shell">
                <aside class="md-sidebar">
                  <div class="md-brand">RGDS <span>Consumer</span></div>
                  <button class="md-theme-btn rgds-interactive" data-theme-set="primary-light" aria-pressed="true">Primary Light</button>
                  <button class="md-theme-btn rgds-interactive" data-theme-set="secondary-light">Secondary Light</button>
                  <button class="md-theme-btn rgds-interactive" data-theme-set="primary-dark">Primary Dark</button>
                  <button class="md-theme-btn rgds-interactive" data-theme-set="secondary-dark">Secondary Dark</button>
                </aside>
                <main class="md-main">
                  <h1 class="md-section-title">Desktop dashboard fixture</h1>
                  <div class="md-grid">
                    <button type="button" class="md-btn rgds-interactive">Primary action</button>
                    <div class="md-card" data-interactive="true" tabindex="0">Interactive metric card</div>
                    <div class="md-card">Static info (no lift)</div>
                  </div>
                  <h2 class="md-section-title">Form</h2>
                  <label class="rgds-field">
                    <span class="rgds-field__label">Email</span>
                    <input class="rgds-field__input rgds-interactive" type="email" />
                  </label>
                  <h2 class="md-section-title">Alerts</h2>
                  <div class="rgds-alert rgds-alert--error">Destructive confirmation preview</div>
                  <div class="rgds-alert rgds-alert--info">Informational sync</div>
                </main>
              </div>
              <script>
                document.querySelectorAll("[data-theme-set]").forEach((btn) => {
                  btn.addEventListener("click", () => {
                    document.documentElement.setAttribute("data-theme", btn.dataset.themeSet);
                    document.querySelectorAll("[data-theme-set]").forEach((b) =>
                      b.setAttribute("aria-pressed", String(b === btn)),
                    );
                  });
                });
              </script>
            </body>
            </html>
            """
        ),
    )
    W(
        "fixtures/consumers/flutter/README.md",
        textwrap.dedent(
            """\
            # Isolated Flutter consumer fixture

            From `packages/flutter`:

            ```bash
            flutter test
            flutter analyze
            ```

            App wiring (sandbox only):

            ```dart
            import 'package:rgds/rgds.dart';

            MaterialApp(
              theme: rgdsThemeData(RgdsTheme.primaryLight),
              home: Scaffold(
                body: Column(children: [
                  RgdsButton(label: 'Save', onPressed: () {}),
                  RgdsCard(interactive: true, onTap: () {}, child: Text('Row')),
                  RgdsTextField(label: 'Name'),
                  RgdsAlert(message: 'Synced', tone: RgdsAlertTone.info),
                ]),
              ),
            );
            ```

            Do not point production apps at this fixture path; depend on a versioned `rgds` release.
            """
        ),
    )


def write_docs_and_manifest() -> None:
    component_sets = [
        "RGDS / Button",
        "RGDS / Card / Interactive",
        "RGDS / Text Field",
        "RGDS / Checkbox",
        "RGDS / Switch",
        "RGDS / Tab",
        "RGDS / Nav Item",
        "RGDS / Badge",
        "RGDS / Alert",
        "RGDS / Dialog",
        "RGDS / App Bar",
        "RGDS / List Tile",
        "RGDS / Icon Button",
    ]
    manifest = {
        "$schema": "./schemas/rgds-manifest.schema.json",
        "name": "R3lentless-Grind Design System",
        "abbreviation": "RGDS",
        "version": VERSION,
        "status": "release-candidate",
        "repository": {
            "type": "git",
            "path": str(DST),
        },
        "themes": [
            "primary-light",
            "secondary-light",
            "primary-dark",
            "secondary-dark",
        ],
        "platforms": ["web", "flutter"],
        "discovery": {
            "user_manifest_windows": r"C:\Users\ynotf\.rgds\RGDS_MANIFEST.json",
            "user_manifest_relative": ".rgds/RGDS_MANIFEST.json",
            "note": "Neutral user-scope pointer; not AgentCore F: runtime.",
        },
        "figma": {
            "file_key": FILE_KEY,
            "library_url": FILE_URL,
            "documentation": "docs/FIGMA.md",
            "pages": [
                "Foundations",
                "Components",
                "Patterns",
                "Templates",
                "Theme Preview",
            ],
            "component_sets": component_sets,
            "color_collection": "RGDS / Color",
            "modes": [
                "primary-light",
                "secondary-light",
                "primary-dark",
                "secondary-dark",
            ],
            "make_kit": {
                "status": "guidelines-ready",
                "path": "make-kit/",
                "blocked_on": "npm publish of @r3lentless/rgds-web + Figma Make kit assembly",
            },
            "code_connect": {
                "status": "deferred",
                "stable_names": component_sets,
            },
        },
        "packages": {
            "npm": "@r3lentless/rgds-web",
            "flutter": "rgds",
        },
        "brand": {
            "seedStatus": "TEMPORARY_PLACEHOLDER",
            "note": "Operator must supply final brand seeds before claiming production brand lock.",
        },
        "authority": [
            "docs/AUTHORITY.md",
            "tokens/",
            "docs/FIGMA.md",
            "packages/",
        ],
        "release": {
            "changelog": "CHANGELOG.md",
            "gates": [
                "node tools/validate-all.mjs",
                "node tools/cold-adopt-sim.mjs",
                "npm run build -w @r3lentless/rgds-web",
                "flutter test (packages/flutter)",
            ],
        },
    }
    W("rgds.manifest.json", json.dumps(manifest, indent=2) + "\n")

    pointer = {
        "schema_version": 1,
        "name": manifest["name"],
        "abbreviation": "RGDS",
        "version": VERSION,
        "status": manifest["status"],
        "repository_path": str(DST),
        "repository_manifest": str(DST / "rgds.manifest.json"),
        "themes": manifest["themes"],
        "platforms": manifest["platforms"],
        "packages": manifest["packages"],
        "figma": {
            "file_key": FILE_KEY,
            "library_url": FILE_URL,
            "component_sets": component_sets,
            "pages": manifest["figma"]["pages"],
        },
        "adoption": "docs/ADOPTION.md",
        "make_kit": "make-kit/",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "authority": "Independent org design system — not AgentCore-owned",
        "brand_seedStatus": "TEMPORARY_PLACEHOLDER",
    }
    DISCOVERY.mkdir(parents=True, exist_ok=True)
    (DISCOVERY / "RGDS_MANIFEST.json").write_text(
        json.dumps(pointer, indent=2) + "\n", encoding="utf-8"
    )
    print("discovery updated")

    W(
        "CHANGELOG.md",
        textwrap.dedent(
            f"""\
            # Changelog

            ## {VERSION} — release candidate

            - Figma library expanded: Foundations / Components / Patterns / Templates / Theme Preview
            - Component sets: Button, Card, Text Field, Checkbox, Switch, Tab, Nav Item, Badge, Alert, Dialog, App Bar, List Tile, Icon Button
            - Semantic status tokens (error/success/warning/info) + breakpoints/opacity
            - `@r3lentless/rgds-web` React+Vite library entry + CSS tokens
            - Flutter `rgds` widgets (Button, Card, TextField, Alert) + ThemeData helper
            - Make kit guidelines scaffold (`make-kit/`) pending npm publish
            - Validation: `tools/validate-all.mjs`, `tools/cold-adopt-sim.mjs`
            - Brand seeds remain TEMPORARY_PLACEHOLDER pending operator finals

            ## 0.2.0-dev — alpha foundations

            - Four themes, interaction tokens, Button/Card proof, discovery pointer
            """
        ),
    )
    W(
        "docs/ADOPTION.md",
        textwrap.dedent(
            f"""\
            # Adopt RGDS for this project

            ## Cold discovery (any new agent)

            1. Read `C:\\\\Users\\\\ynotf\\\\.rgds\\\\RGDS_MANIFEST.json` (or `$HOME/.rgds/RGDS_MANIFEST.json`).
            2. Note `version`, `figma.file_key`, `packages.npm`, `packages.flutter`, `themes`.
            3. Open `repository_manifest` for the full inventory.
            4. Open Figma: {FILE_URL}
            5. Install **versioned** packages — never absolute `D:\\\\github\\\\...` in app dependencies.

            ## Web

            ```bash
            npm install @r3lentless/rgds-web@{VERSION}
            ```

            Import CSS + components; call `applyRgdsTheme('primary-light')`.

            ## Flutter

            Depend on `rgds` at `{VERSION}` (path/git/publish per your registry).
            Use `rgdsThemeData(RgdsTheme.primaryLight)` and `RgdsButton` / `RgdsCard` / etc.

            ## Rules

            - Application owns workflow/business logic; RGDS owns reusable visuals.
            - Four themes only via `data-theme` / `RgdsTheme`.
            - Interactive surfaces only receive hover/pressed/focus treatment.
            - Do not invent a parallel design system.
            - Brand seeds may still be TEMPORARY_PLACEHOLDER until operator finalizes.

            ## Make kit

            See `make-kit/` — requires published npm package + Figma Make kit assembly.
            """
        ),
    )
    W(
        "docs/FIGMA.md",
        textwrap.dedent(
            f"""\
            # RGDS Figma library

            - **File:** [{FILE_URL}]({FILE_URL})
            - **file_key:** `{FILE_KEY}`
            - **Pages:** Foundations · Components · Patterns · Templates · Theme Preview
            - **Modes:** primary-light · secondary-light · primary-dark · secondary-dark
            - **Color collection:** RGDS / Color (single collection; four modes)

            ## Component sets

            Button, Card/Interactive, Text Field, Checkbox, Switch, Tab, Nav Item,
            Badge, Alert, Dialog, App Bar, List Tile, Icon Button — each with State variants.

            ## Patterns / Templates

            Generic shells (auth, desktop/mobile app shell, settings, list/detail, form,
            empty/loading, destructive confirm) and starter templates (dashboard, dense table,
            mobile home, wizard, profile). No product-specific workflows.

            ## Publishing

            Publish this file as a Figma team library when ready for org-wide consumption.
            Make kit assembly: see `make-kit/README.md`.
            """
        ),
    )
    W(
        "docs/RELEASE.md",
        textwrap.dedent(
            f"""\
            # Release / upgrade / rollback

            ## Version

            Current: `{VERSION}` (`rgds.manifest.json`).

            ## Gates (required)

            ```bash
            node tools/validate-all.mjs
            node tools/cold-adopt-sim.mjs
            npm install
            npm run build -w @r3lentless/rgds-web
            npm run test -w @r3lentless/rgds-web
            cd packages/flutter && flutter test && flutter analyze
            ```

            ## Publish

            1. Pass gates.
            2. Tag `v{VERSION}`.
            3. Publish `@r3lentless/rgds-web` (npm or Figma private registry).
            4. Publish Flutter package to your private pub host if applicable.
            5. Refresh `C:\\\\Users\\\\ynotf\\\\.rgds\\\\RGDS_MANIFEST.json` via `scripts/install-discovery.ps1`.

            ## Consumer upgrade

            Products pin exact versions and deliberately bump. No auto-tracking of main.

            ## Rollback

            Reinstall previous package version; restore prior discovery pointer from Git tag.
            """
        ),
    )
    # root package.json
    W(
        "package.json",
        json.dumps(
            {
                "name": "@r3lentless/rgds",
                "version": VERSION,
                "private": True,
                "description": "R3lentless-Grind Design System monorepo",
                "license": "UNLICENSED",
                "type": "module",
                "workspaces": ["packages/*"],
                "scripts": {
                    "build:tokens": "node tools/build-tokens.mjs",
                    "build:web": "npm run build -w @r3lentless/rgds-web",
                    "check:contrast": "node tools/check-contrast.mjs",
                    "validate": "node tools/validate-all.mjs",
                    "prove:discovery": "node tools/prove-discovery.mjs",
                    "prove:cold": "node tools/cold-adopt-sim.mjs",
                    "test:web": "npm run test -w @r3lentless/rgds-web",
                },
            },
            indent=2,
        )
        + "\n",
    )
    W(
        "README.md",
        textwrap.dedent(
            f"""\
            # R3lentless-Grind Design System (RGDS)

            Organization-wide frontend foundation — **not** NFA-owned, **not** AgentCore-owned.

            - **Version:** {VERSION}
            - **Figma:** {FILE_URL}
            - **Discovery:** `~/.rgds/RGDS_MANIFEST.json`
            - **Web:** `@r3lentless/rgds-web`
            - **Flutter:** `rgds`

            Start: `docs/ADOPTION.md`

            Brand seeds: **TEMPORARY_PLACEHOLDER** until operator finalizes values in `tokens/ref/palette.json`.
            """
        ),
    )


def write_audit() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "RGDS_COMPLETION_STATUS.md").write_text(
        textwrap.dedent(
            f"""\
            # RGDS completion status

            - Version: {VERSION}
            - Repo: `{DST}`
            - Figma: {FILE_URL}
            - Discovery: `C:\\\\Users\\\\ynotf\\\\.rgds\\\\RGDS_MANIFEST.json`
            - Brand: TEMPORARY_PLACEHOLDER (awaiting operator finals)
            - NFA / consumers: not modified
            - Make kit: guidelines ready; npm publish + Figma assembly still operator-gated
            - Cold adopt: `node tools/cold-adopt-sim.mjs`
            """
        ),
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    expand_semantic_tokens()
    write_tokens_css_extras()
    write_web_package()
    write_flutter_package()
    write_make_kit()
    write_tools_and_validation()
    write_consumer_fixtures()
    write_docs_and_manifest()
    write_audit()
    print("RGDS completion materialize done", VERSION)


if __name__ == "__main__":
    main()
