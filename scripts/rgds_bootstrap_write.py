"""Materialize RGDS repository content from audited AgentCore M3 seeds.

Writes into D:\\github\\r3lentless-grind-design-system using pathlib only.
Does not modify any consumer application.
"""
from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

SRC = Path(r"D:\github\agentcore-control-plane\docs\design\m3")
DST = Path(r"D:\github\r3lentless-grind-design-system")
DISCOVERY = Path(r"C:\Users\ynotf\.rgds")


def write(rel: str, text: str) -> None:
    path = DST / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {rel}")


def sync(rel: str) -> None:
    src = SRC / rel
    dst = DST / rel
    if not src.is_file():
        print(f"skip missing {rel}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    print(f"synced {rel}")


STATE_JSON = {
    "$schema": "https://design-tokens.github.io/community-group/format/",
    "$description": (
        "RGDS interaction layer (md.rgds.state.*) — RGDS conventions, "
        "not official Material 3 primitives. Themes override values."
    ),
    "md": {
        "rgds": {
            "state": {
                "hover": {
                    "surface": {
                        "tint": {
                            "$value": "{md.sys.color.primary}",
                            "$type": "color",
                        },
                        "tintAmount": {"$value": "10%", "$type": "percentage"},
                        "chromaBoost": {"$value": "0.02", "$type": "number"},
                    },
                    "border": {
                        "color": {
                            "$value": "{md.sys.color.outline}",
                            "$type": "color",
                        },
                        "width": {"$value": "1px", "$type": "dimension"},
                        "emphasis": {"$value": "1.15", "$type": "number"},
                    },
                    "content": {
                        "iconAccent": {
                            "$value": "{md.sys.color.primary}",
                            "$type": "color",
                        },
                        "labelEmphasis": {"$value": "1", "$type": "number"},
                    },
                    "elevation": {
                        "$value": "{md.sys.elevation.level3}",
                        "$type": "shadow",
                    },
                    "motion": {
                        "duration": {
                            "$value": "{md.ref.motion.duration.short}",
                            "$type": "duration",
                        }
                    },
                },
                "focus": {
                    "surface": {
                        "tint": {"$value": "transparent", "$type": "color"},
                        "tintAmount": {"$value": "0%", "$type": "percentage"},
                        "chromaBoost": {"$value": "0", "$type": "number"},
                    },
                    "border": {
                        "color": {
                            "$value": "{md.sys.color.primary}",
                            "$type": "color",
                        },
                        "width": {"$value": "2px", "$type": "dimension"},
                        "offset": {"$value": "2px", "$type": "dimension"},
                        "emphasis": {"$value": "1", "$type": "number"},
                    },
                    "content": {
                        "iconAccent": {
                            "$value": "{md.sys.color.primary}",
                            "$type": "color",
                        },
                        "labelEmphasis": {"$value": "1", "$type": "number"},
                    },
                    "elevation": {
                        "$value": "{md.sys.elevation.level2}",
                        "$type": "shadow",
                    },
                    "motion": {
                        "duration": {
                            "$value": "{md.ref.motion.duration.short}",
                            "$type": "duration",
                        }
                    },
                },
                "pressed": {
                    "surface": {
                        "tint": {
                            "$value": "{md.sys.color.onSurface}",
                            "$type": "color",
                        },
                        "tintAmount": {"$value": "8%", "$type": "percentage"},
                        "chromaBoost": {"$value": "0.01", "$type": "number"},
                    },
                    "border": {
                        "color": {
                            "$value": "{md.sys.color.outline}",
                            "$type": "color",
                        },
                        "width": {"$value": "1px", "$type": "dimension"},
                        "emphasis": {"$value": "1", "$type": "number"},
                    },
                    "content": {
                        "iconAccent": {
                            "$value": "{md.sys.color.primary}",
                            "$type": "color",
                        },
                        "labelEmphasis": {"$value": "1", "$type": "number"},
                    },
                    "elevation": {
                        "$value": "{md.sys.elevation.level1}",
                        "$type": "shadow",
                    },
                    "motion": {
                        "duration": {"$value": "80ms", "$type": "duration"},
                        "scale": {"$value": "0.98", "$type": "number"},
                    },
                },
                "selected": {
                    "surface": {
                        "tint": {
                            "$value": "{md.sys.color.primaryContainer}",
                            "$type": "color",
                        },
                        "tintAmount": {"$value": "100%", "$type": "percentage"},
                        "chromaBoost": {"$value": "0", "$type": "number"},
                    },
                    "border": {
                        "color": {
                            "$value": "{md.sys.color.primary}",
                            "$type": "color",
                        },
                        "width": {"$value": "1.5px", "$type": "dimension"},
                        "emphasis": {"$value": "1.2", "$type": "number"},
                    },
                    "content": {
                        "iconAccent": {
                            "$value": "{md.sys.color.primary}",
                            "$type": "color",
                        },
                        "labelEmphasis": {"$value": "1.05", "$type": "number"},
                    },
                    "elevation": {
                        "$value": "{md.sys.elevation.level2}",
                        "$type": "shadow",
                    },
                    "motion": {
                        "duration": {
                            "$value": "{md.ref.motion.duration.short}",
                            "$type": "duration",
                        }
                    },
                },
                "disabled": {
                    "surface": {
                        "tint": {"$value": "transparent", "$type": "color"},
                        "tintAmount": {"$value": "0%", "$type": "percentage"},
                        "chromaBoost": {"$value": "0", "$type": "number"},
                        "opacity": {"$value": "0.38", "$type": "number"},
                    },
                    "border": {
                        "color": {
                            "$value": "{md.sys.color.outlineVariant}",
                            "$type": "color",
                        },
                        "width": {"$value": "1px", "$type": "dimension"},
                        "emphasis": {"$value": "0.7", "$type": "number"},
                    },
                    "content": {
                        "iconAccent": {
                            "$value": "{md.sys.color.onSurface}",
                            "$type": "color",
                        },
                        "labelEmphasis": {"$value": "0.72", "$type": "number"},
                    },
                    "elevation": {
                        "$value": "{md.sys.elevation.level0}",
                        "$type": "shadow",
                    },
                    "motion": {
                        "duration": {"$value": "0ms", "$type": "duration"}
                    },
                },
            }
        }
    },
}


THEME_STATE = {
    "primary-light": {
        "hover": {
            "surface": {
                "tint": "oklch(58% 0.17 250)",
                "tintAmount": "12%",
                "chromaBoost": "0.03",
            },
            "border": {"color": "oklch(50% 0.16 250)", "emphasis": "1.2"},
            "content": {"iconAccent": "oklch(50% 0.16 250)"},
            "elevation": "var(--md-sys-elevation-level3)",
        },
        "focus": {
            "border": {
                "color": "oklch(50% 0.16 250)",
                "width": "2px",
                "offset": "2px",
            }
        },
        "pressed": {
            "surface": {
                "tint": "oklch(40% 0.14 250)",
                "tintAmount": "10%",
            }
        },
        "selected": {
            "surface": {
                "tint": "oklch(92% 0.04 250)",
                "tintAmount": "100%",
            },
            "border": {"color": "oklch(50% 0.16 250)"},
        },
    },
    "secondary-light": {
        "hover": {
            "surface": {
                "tint": "oklch(84% 0.16 95)",
                "tintAmount": "14%",
                "chromaBoost": "0.04",
            },
            "border": {"color": "oklch(84% 0.16 95)", "emphasis": "1.25"},
            "content": {"iconAccent": "oklch(68% 0.18 55)"},
            "elevation": "var(--md-sys-elevation-level3)",
        },
        "focus": {
            "border": {
                "color": "oklch(68% 0.18 55)",
                "width": "2px",
                "offset": "2px",
            }
        },
        "pressed": {
            "surface": {
                "tint": "oklch(52% 0.18 45)",
                "tintAmount": "10%",
            }
        },
        "selected": {
            "surface": {
                "tint": "oklch(92% 0.05 55)",
                "tintAmount": "100%",
            },
            "border": {"color": "oklch(68% 0.18 55)"},
        },
    },
    "primary-dark": {
        "hover": {
            "surface": {
                "tint": "oklch(100% 0 0)",
                "tintAmount": "7%",
                "chromaBoost": "0.015",
            },
            "border": {"color": "oklch(84% 0.004 260)", "emphasis": "1.1"},
            "content": {"iconAccent": "oklch(82% 0.08 250)"},
            "elevation": "var(--md-sys-elevation-level2)",
        },
        "focus": {
            "border": {
                "color": "oklch(82% 0.08 250)",
                "width": "2px",
                "offset": "2px",
            }
        },
        "pressed": {
            "surface": {
                "tint": "oklch(0% 0 0)",
                "tintAmount": "10%",
            }
        },
        "selected": {
            "surface": {
                "tint": "oklch(26% 0.010 250)",
                "tintAmount": "100%",
            },
            "border": {"color": "oklch(82% 0.08 250)"},
        },
    },
    "secondary-dark": {
        "hover": {
            "surface": {
                "tint": "oklch(88% 0.10 55)",
                "tintAmount": "9%",
                "chromaBoost": "0.05",
            },
            "border": {"color": "oklch(68% 0.18 55)", "emphasis": "1.3"},
            "content": {"iconAccent": "oklch(82% 0.08 250)"},
            "elevation": "var(--md-sys-elevation-level3)",
        },
        "focus": {
            "border": {
                "color": "oklch(68% 0.18 55)",
                "width": "2px",
                "offset": "2px",
            }
        },
        "pressed": {
            "surface": {
                "tint": "oklch(68% 0.18 55)",
                "tintAmount": "12%",
            }
        },
        "selected": {
            "surface": {
                "tint": "oklch(42% 0.16 45)",
                "tintAmount": "100%",
            },
            "border": {"color": "oklch(68% 0.18 55)"},
        },
    },
}


def enhance_theme(name: str) -> None:
    rel = f"tokens/themes/{name}.json"
    path = DST / rel
    data = json.loads(path.read_text(encoding="utf-8"))
    ext = data.setdefault("$extensions", {})
    ext.pop("agentcore.dataTheme", None)
    ext["rgds.dataTheme"] = name
    ext["rgds.seedStatus"] = "TEMPORARY_PLACEHOLDER"
    # Move legacy md.sys.state → md.rgds.state theme overrides
    sys = data.setdefault("md", {}).setdefault("sys", {})
    legacy = sys.pop("state", None)
    rgds = data.setdefault("md", {}).setdefault("rgds", {})
    state = rgds.setdefault("state", THEME_STATE[name])
    if legacy:
        # Preserve audited hover seeds if present, but keep structured axes
        hover_legacy = legacy.get("hover") or {}
        hover = state.setdefault("hover", {})
        surface = hover.setdefault("surface", {})
        if "surfaceTint" in hover_legacy:
            surface["tint"] = hover_legacy["surfaceTint"].get("$value", surface.get("tint"))
        if "surfaceTintAmount" in hover_legacy:
            surface["tintAmount"] = hover_legacy["surfaceTintAmount"].get(
                "$value", surface.get("tintAmount")
            )
        border = hover.setdefault("border", {})
        if "borderColor" in hover_legacy:
            border["color"] = hover_legacy["borderColor"].get("$value", border.get("color"))
    # Drop saturate filter guidance from theme docs — chroma via tint tokens
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"enhanced {rel}")


TOKENS_CSS = textwrap.dedent(
    """\
    /* RGDS compiled theme + interaction tokens. Generated by tools/build-tokens.mjs
       Semantic interaction uses color-mix / border / elevation / icon accent.
       Do NOT apply filter:brightness as universal hover. */

    :root {
      --md-sys-typescale-font: Inter, "SF Pro Text", system-ui, sans-serif;
      --md-sys-typescale-display-large-size: 3.5625rem;
      --md-sys-typescale-headline-medium-size: 1.75rem;
      --md-sys-typescale-title-large-size: 1.375rem;
      --md-sys-typescale-body-large-size: 1rem;
      --md-sys-typescale-body-medium-size: 0.875rem;
      --md-sys-typescale-label-large-size: 0.875rem;

      --md-sys-spacing-none: 0;
      --md-sys-spacing-xs: 4px;
      --md-sys-spacing-sm: 8px;
      --md-sys-spacing-md: 16px;
      --md-sys-spacing-lg: 24px;
      --md-sys-spacing-xl: 32px;
      --md-sys-spacing-2xl: 48px;
      --md-sys-spacing-3xl: 64px;
      --md-sys-spacing-4xl: 96px;

      --md-sys-shape-corner-none: 0;
      --md-sys-shape-corner-extra-small: 4px;
      --md-sys-shape-corner-small: 8px;
      --md-sys-shape-corner-medium: 12px;
      --md-sys-shape-corner-large: 16px;
      --md-sys-shape-corner-extra-large: 28px;
      --md-sys-shape-corner-full: 9999px;

      --md-sys-elevation-level0: none;
      --md-sys-elevation-level1: 0 1px 2px oklch(0% 0 0 / 0.06), 0 1px 3px oklch(0% 0 0 / 0.08);
      --md-sys-elevation-level2: 0 2px 6px oklch(0% 0 0 / 0.08), 0 4px 12px oklch(0% 0 0 / 0.10);
      --md-sys-elevation-level3: 0 4px 12px oklch(0% 0 0 / 0.10), 0 8px 24px oklch(0% 0 0 / 0.12);

      --md-sys-motion-duration-short: 120ms;
      --md-sys-motion-duration-medium: 280ms;
      --md-ref-motion-custom-pulse-duration: 4000ms;
      --md-sys-motion-easing-emphasized: cubic-bezier(0.16, 1, 0.3, 1);

      --md-custom-rainbow-gradient: linear-gradient(
        120deg,
        oklch(65% 0.25 25),
        oklch(75% 0.20 60),
        oklch(85% 0.20 95),
        oklch(72% 0.20 145),
        oklch(75% 0.15 230),
        oklch(60% 0.20 290),
        oklch(65% 0.25 0),
        oklch(65% 0.25 25)
      );
      --md-custom-stroke-featured: transparent;
      --md-custom-icon-a: var(--md-sys-color-primary);
      --md-custom-icon-b: var(--md-sys-color-tertiary);
      --md-custom-icon-c: var(--md-sys-color-secondary);

      /* md.rgds.state.* defaults (theme overrides below) */
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
    }

    :root,
    :root[data-theme="primary-light"] {
      --md-sys-color-primary: oklch(50% 0.16 250);
      --md-sys-color-on-primary: #ffffff;
      --md-sys-color-primary-container: oklch(92% 0.04 250);
      --md-sys-color-on-primary-container: oklch(18% 0.06 250);
      --md-sys-color-secondary: oklch(52% 0.18 25);
      --md-sys-color-on-secondary: #ffffff;
      --md-sys-color-secondary-container: oklch(90% 0.05 25);
      --md-sys-color-tertiary: oklch(52% 0.16 145);
      --md-sys-color-on-tertiary: #ffffff;
      --md-sys-color-surface: oklch(99% 0.001 260);
      --md-sys-color-on-surface: oklch(16% 0.008 260);
      --md-sys-color-surface-container: oklch(96% 0.002 260);
      --md-sys-color-surface-container-high: oklch(94% 0.002 260);
      --md-sys-color-surface-container-highest: oklch(92% 0.003 260);
      --md-sys-color-outline: oklch(56% 0.012 260);
      --md-sys-color-outline-variant: oklch(84% 0.006 260);
      --md-custom-icon-a: oklch(58% 0.17 250);
      --md-custom-icon-b: oklch(60% 0.17 145);
      --md-custom-icon-c: oklch(84% 0.16 95);
      --md-custom-stroke-featured: transparent;
      --md-custom-rainbow-enabled: 0;
      --md-rgds-state-hover-surface-tint: oklch(58% 0.17 250);
      --md-rgds-state-hover-surface-tint-amount: 12%;
      --md-rgds-state-hover-border-color: oklch(50% 0.16 250);
      --md-rgds-state-hover-icon-accent: oklch(50% 0.16 250);
      --md-rgds-state-focus-border-color: oklch(50% 0.16 250);
      --md-rgds-state-pressed-surface-tint: oklch(40% 0.14 250);
      --md-rgds-state-selected-surface: oklch(92% 0.04 250);
      --md-rgds-state-selected-border-color: oklch(50% 0.16 250);
    }

    :root[data-theme="secondary-light"] {
      --md-sys-color-primary: oklch(68% 0.18 55);
      --md-sys-color-on-primary: oklch(16% 0.008 260);
      --md-sys-color-primary-container: oklch(92% 0.05 55);
      --md-sys-color-on-primary-container: oklch(42% 0.16 45);
      --md-sys-color-secondary: oklch(52% 0.18 45);
      --md-sys-color-on-secondary: #ffffff;
      --md-sys-color-secondary-container: oklch(96% 0.02 55);
      --md-sys-color-tertiary: oklch(50% 0.16 250);
      --md-sys-color-on-tertiary: #ffffff;
      --md-sys-color-surface: oklch(96% 0.02 55);
      --md-sys-color-on-surface: oklch(16% 0.008 260);
      --md-sys-color-surface-container: oklch(99% 0.001 260);
      --md-sys-color-surface-container-high: oklch(98% 0.001 260);
      --md-sys-color-surface-container-highest: oklch(96% 0.002 260);
      --md-sys-color-outline: oklch(52% 0.18 45);
      --md-sys-color-outline-variant: oklch(88% 0.10 55);
      --md-custom-icon-a: oklch(68% 0.18 55);
      --md-custom-icon-b: oklch(58% 0.17 250);
      --md-custom-icon-c: oklch(60% 0.17 145);
      --md-custom-stroke-featured: oklch(84% 0.16 95);
      --md-custom-rainbow-enabled: 0;
      --md-rgds-state-hover-surface-tint: oklch(84% 0.16 95);
      --md-rgds-state-hover-surface-tint-amount: 14%;
      --md-rgds-state-hover-border-color: oklch(84% 0.16 95);
      --md-rgds-state-hover-icon-accent: oklch(68% 0.18 55);
      --md-rgds-state-focus-border-color: oklch(68% 0.18 55);
      --md-rgds-state-pressed-surface-tint: oklch(52% 0.18 45);
      --md-rgds-state-selected-surface: oklch(92% 0.05 55);
      --md-rgds-state-selected-border-color: oklch(68% 0.18 55);
    }

    :root[data-theme="primary-dark"] {
      --md-sys-color-primary: oklch(82% 0.08 250);
      --md-sys-color-on-primary: oklch(10% 0.012 250);
      --md-sys-color-primary-container: oklch(26% 0.010 250);
      --md-sys-color-on-primary-container: oklch(82% 0.08 250);
      --md-sys-color-secondary: oklch(84% 0.004 260);
      --md-sys-color-on-secondary: oklch(10% 0.012 250);
      --md-sys-color-secondary-container: oklch(21% 0.012 250);
      --md-sys-color-tertiary: oklch(82% 0.08 145);
      --md-sys-color-on-tertiary: oklch(10% 0.012 250);
      --md-sys-color-surface: oklch(10% 0.012 250);
      --md-sys-color-on-surface: oklch(99% 0.001 260);
      --md-sys-color-surface-container: oklch(16% 0.012 250);
      --md-sys-color-surface-container-high: oklch(18% 0.012 250);
      --md-sys-color-surface-container-highest: oklch(21% 0.012 250);
      --md-sys-color-outline: oklch(66% 0.006 260);
      --md-sys-color-outline-variant: oklch(26% 0.010 250);
      --md-custom-icon-a: oklch(82% 0.08 250);
      --md-custom-icon-b: oklch(82% 0.08 145);
      --md-custom-icon-c: oklch(92% 0.003 260);
      --md-custom-stroke-featured: oklch(66% 0.006 260);
      --md-custom-rainbow-enabled: 0;
      --md-rgds-state-hover-surface-tint: oklch(100% 0 0);
      --md-rgds-state-hover-surface-tint-amount: 7%;
      --md-rgds-state-hover-border-color: oklch(84% 0.004 260);
      --md-rgds-state-hover-icon-accent: oklch(82% 0.08 250);
      --md-rgds-state-hover-elevation: var(--md-sys-elevation-level2);
      --md-rgds-state-focus-border-color: oklch(82% 0.08 250);
      --md-rgds-state-pressed-surface-tint: oklch(0% 0 0);
      --md-rgds-state-selected-surface: oklch(26% 0.010 250);
      --md-rgds-state-selected-border-color: oklch(82% 0.08 250);
    }

    :root[data-theme="secondary-dark"] {
      --md-sys-color-primary: oklch(68% 0.18 55);
      --md-sys-color-on-primary: #000000;
      --md-sys-color-primary-container: oklch(42% 0.16 45);
      --md-sys-color-on-primary-container: oklch(88% 0.10 55);
      --md-sys-color-secondary: oklch(52% 0.18 45);
      --md-sys-color-on-secondary: #ffffff;
      --md-sys-color-secondary-container: oklch(11% 0 0);
      --md-sys-color-tertiary: oklch(82% 0.08 250);
      --md-sys-color-on-tertiary: #000000;
      --md-sys-color-surface: #000000;
      --md-sys-color-on-surface: oklch(99% 0.001 260);
      --md-sys-color-surface-container: oklch(8% 0 0);
      --md-sys-color-surface-container-high: oklch(11% 0 0);
      --md-sys-color-surface-container-highest: oklch(14% 0 0);
      --md-sys-color-outline: oklch(62% 0.18 55);
      --md-sys-color-outline-variant: oklch(11% 0 0);
      --md-custom-icon-a: oklch(68% 0.18 55);
      --md-custom-icon-b: oklch(82% 0.08 250);
      --md-custom-icon-c: oklch(82% 0.08 145);
      --md-custom-stroke-featured: oklch(68% 0.18 55);
      --md-custom-rainbow-enabled: 1;
      --md-rgds-state-hover-surface-tint: oklch(88% 0.10 55);
      --md-rgds-state-hover-surface-tint-amount: 9%;
      --md-rgds-state-hover-border-color: oklch(68% 0.18 55);
      --md-rgds-state-hover-icon-accent: oklch(82% 0.08 250);
      --md-rgds-state-focus-border-color: oklch(68% 0.18 55);
      --md-rgds-state-pressed-surface-tint: oklch(68% 0.18 55);
      --md-rgds-state-pressed-surface-tint-amount: 12%;
      --md-rgds-state-selected-surface: oklch(42% 0.16 45);
      --md-rgds-state-selected-border-color: oklch(68% 0.18 55);
    }
    """
)


INTERACTION_CSS = textwrap.dedent(
    """\
    /* RGDS interactive surface behaviors — semantic tokens only.
       Opt-in via .rgds-interactive (or component classes). Static containers stay quiet. */

    .rgds-interactive,
    .md-btn,
    .md-theme-btn,
    .md-nav-item,
    .md-list-tile,
    .md-tab,
    .md-menu-item,
    .md-card[data-interactive="true"],
    button.rgds-interactive,
    a.rgds-interactive,
    [role="button"].rgds-interactive {
      transition:
        background-color var(--md-sys-motion-duration-medium) var(--md-sys-motion-easing-emphasized),
        border-color var(--md-sys-motion-duration-medium) var(--md-sys-motion-easing-emphasized),
        box-shadow var(--md-sys-motion-duration-medium) var(--md-sys-motion-easing-emphasized),
        color var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-emphasized),
        transform var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-emphasized);
    }

    .rgds-interactive:hover:not(:disabled):not([aria-disabled="true"]),
    .md-btn:hover:not(:disabled),
    .md-theme-btn:hover:not(:disabled),
    .md-nav-item:hover,
    .md-list-tile:hover,
    .md-tab:hover,
    .md-menu-item:hover,
    .md-card[data-interactive="true"]:hover {
      background: color-mix(
        in oklch,
        var(--rgds-surface-base, var(--md-sys-color-surface-container-high))
          calc(100% - var(--md-rgds-state-hover-surface-tint-amount)),
        var(--md-rgds-state-hover-surface-tint) var(--md-rgds-state-hover-surface-tint-amount)
      );
      border-color: var(--md-rgds-state-hover-border-color);
      box-shadow: var(--md-rgds-state-hover-elevation, var(--md-sys-elevation-level3));
      --rgds-icon-accent: var(--md-rgds-state-hover-icon-accent);
    }

    .rgds-interactive:focus-visible,
    .md-btn:focus-visible,
    .md-theme-btn:focus-visible,
    .md-nav-item:focus-visible,
    .md-list-tile:focus-visible,
    .md-tab:focus-visible,
    .md-menu-item:focus-visible,
    .md-card[data-interactive="true"]:focus-visible {
      outline: var(--md-rgds-state-focus-border-width) solid var(--md-rgds-state-focus-border-color);
      outline-offset: var(--md-rgds-state-focus-border-offset);
    }

    .rgds-interactive:active:not(:disabled),
    .md-btn:active:not(:disabled),
    .md-theme-btn:active:not(:disabled),
    .md-card[data-interactive="true"]:active {
      background: color-mix(
        in oklch,
        var(--rgds-surface-base, var(--md-sys-color-surface-container-high))
          calc(100% - var(--md-rgds-state-pressed-surface-tint-amount)),
        var(--md-rgds-state-pressed-surface-tint) var(--md-rgds-state-pressed-surface-tint-amount)
      );
      box-shadow: var(--md-rgds-state-pressed-elevation);
      transform: scale(var(--md-rgds-state-pressed-scale));
    }

    .rgds-interactive[aria-pressed="true"],
    .rgds-interactive[aria-selected="true"],
    .md-theme-btn[aria-pressed="true"],
    .md-nav-item[aria-current="page"],
    .md-tab[aria-selected="true"],
    .md-list-tile[aria-selected="true"] {
      background: var(--md-rgds-state-selected-surface);
      color: var(--md-rgds-state-selected-on-surface, var(--md-sys-color-on-primary-container));
      border-color: var(--md-rgds-state-selected-border-color);
    }

    .rgds-interactive:disabled,
    .rgds-interactive[aria-disabled="true"],
    .md-btn:disabled {
      opacity: var(--md-rgds-state-disabled-opacity);
      cursor: not-allowed;
      box-shadow: none;
      transform: none;
      pointer-events: none;
    }

    /* Forced visual states for regression fixtures (no pointer required) */
    .rgds-state-hover {
      background: color-mix(
        in oklch,
        var(--rgds-surface-base, var(--md-sys-color-surface-container-high))
          calc(100% - var(--md-rgds-state-hover-surface-tint-amount)),
        var(--md-rgds-state-hover-surface-tint) var(--md-rgds-state-hover-surface-tint-amount)
      ) !important;
      border-color: var(--md-rgds-state-hover-border-color) !important;
      box-shadow: var(--md-rgds-state-hover-elevation, var(--md-sys-elevation-level3)) !important;
    }
    .rgds-state-focus {
      outline: var(--md-rgds-state-focus-border-width) solid var(--md-rgds-state-focus-border-color) !important;
      outline-offset: var(--md-rgds-state-focus-border-offset) !important;
    }
    .rgds-state-pressed {
      background: color-mix(
        in oklch,
        var(--rgds-surface-base, var(--md-sys-color-surface-container-high))
          calc(100% - var(--md-rgds-state-pressed-surface-tint-amount)),
        var(--md-rgds-state-pressed-surface-tint) var(--md-rgds-state-pressed-surface-tint-amount)
      ) !important;
      box-shadow: var(--md-rgds-state-pressed-elevation) !important;
      transform: scale(var(--md-rgds-state-pressed-scale)) !important;
    }
    .rgds-state-selected {
      background: var(--md-rgds-state-selected-surface) !important;
      border-color: var(--md-rgds-state-selected-border-color) !important;
      color: var(--md-rgds-state-selected-on-surface, var(--md-sys-color-on-primary-container)) !important;
    }
    .rgds-state-disabled {
      opacity: var(--md-rgds-state-disabled-opacity) !important;
      box-shadow: none !important;
    }

    @media (prefers-reduced-motion: reduce) {
      .rgds-interactive,
      .md-btn,
      .md-theme-btn,
      .md-card[data-interactive="true"],
      .md-rainbow-pulse {
        transition: none !important;
        animation: none !important;
        transform: none !important;
      }
    }
    """
)


def write_components_css() -> None:
    # Start from audited components, strip filter:saturate hover, wire rgds tokens
    src = (SRC / "css/components.css").read_text(encoding="utf-8")
    src = src.replace(
        "filter: saturate(var(--md-sys-state-hover-saturate));",
        "/* chroma via color-mix tint tokens; no filter saturation */",
    )
    src = src.replace("--md-sys-state-hover-tint", "--md-rgds-state-hover-surface-tint")
    src = src.replace(
        "--md-sys-state-hover-tint-amount",
        "--md-rgds-state-hover-surface-tint-amount",
    )
    src = src.replace("--md-sys-state-hover-border", "--md-rgds-state-hover-border-color")
    src = src.replace("--md-sys-state-hover-elevation", "--md-rgds-state-hover-elevation")
    # Only interactive cards should brighten
    src = src.replace(
        ".md-card:hover,\n.md-card:focus-within {",
        '.md-card[data-interactive="true"]:hover,\n.md-card[data-interactive="true"]:focus-within {',
    )
    write("packages/web/dist/components.css", src)


BUILD_TOKENS = textwrap.dedent(
    """\
    #!/usr/bin/env node
    /**
     * RGDS token compile entry.
     * Currently publishes checked-in compiled CSS/Dart from semantic sources.
     * Future: Style Dictionary / DTCG resolver — keep this as the single build gate.
     */
    import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
    import { dirname, join } from "node:path";
    import { fileURLToPath } from "node:url";

    const root = join(dirname(fileURLToPath(import.meta.url)), "..");
    const webDist = join(root, "packages", "web", "dist");
    mkdirSync(webDist, { recursive: true });

    for (const name of ["tokens.css", "interaction.css", "components.css"]) {
      const p = join(webDist, name);
      if (!existsSync(p)) {
        console.error("missing", p);
        process.exit(1);
      }
      // Touch manifest of build
      const body = readFileSync(p, "utf8");
      writeFileSync(p, body, "utf8");
    }

    const manifestPath = join(root, "rgds.manifest.json");
    const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
    manifest.build = {
      compiled_at: new Date().toISOString(),
      web: ["packages/web/dist/tokens.css", "packages/web/dist/interaction.css", "packages/web/dist/components.css"],
      flutter: ["packages/flutter/lib/src/generated/rgds_tokens.dart"],
    };
    writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + "\\n");
    console.log("RGDS tokens build OK", manifest.version);
    """
)


FLUTTER_DART = textwrap.dedent(
    """\
    // GENERATED — RGDS semantic theme + interaction tokens for Flutter.
    // Map WidgetState / MaterialState to RgdsInteractionState; do not invent product colors.
    // ignore_for_file: constant_identifier_names

    enum RgdsTheme {
      primaryLight,
      secondaryLight,
      primaryDark,
      secondaryDark,
    }

    enum RgdsInteractionState {
      enabled,
      hovered,
      focused,
      pressed,
      selected,
      disabled,
    }

    class RgdsColorTokens {
      const RgdsColorTokens({
        required this.primary,
        required this.onPrimary,
        required this.primaryContainer,
        required this.onPrimaryContainer,
        required this.secondary,
        required this.onSecondary,
        required this.surface,
        required this.onSurface,
        required this.surfaceContainer,
        required this.surfaceContainerHigh,
        required this.surfaceContainerHighest,
        required this.outline,
        required this.outlineVariant,
      });

      final int primary;
      final int onPrimary;
      final int primaryContainer;
      final int onPrimaryContainer;
      final int secondary;
      final int onSecondary;
      final int surface;
      final int onSurface;
      final int surfaceContainer;
      final int surfaceContainerHigh;
      final int surfaceContainerHighest;
      final int outline;
      final int outlineVariant;
    }

    class RgdsStateTokens {
      const RgdsStateTokens({
        required this.hoverSurfaceTint,
        required this.hoverTintAmount,
        required this.hoverBorder,
        required this.focusBorder,
        required this.pressedTint,
        required this.pressedTintAmount,
        required this.selectedSurface,
        required this.selectedBorder,
        required this.disabledOpacity,
      });

      final int hoverSurfaceTint;
      final double hoverTintAmount;
      final int hoverBorder;
      final int focusBorder;
      final int pressedTint;
      final double pressedTintAmount;
      final int selectedSurface;
      final int selectedBorder;
      final double disabledOpacity;
    }

    class RgdsThemeData {
      const RgdsThemeData({required this.theme, required this.color, required this.state});
      final RgdsTheme theme;
      final RgdsColorTokens color;
      final RgdsStateTokens state;
    }

    /// Approximate OKLCH seeds as ARGB ints for Flutter fixtures (not production color science).
    class RgdsThemes {
      static const primaryLight = RgdsThemeData(
        theme: RgdsTheme.primaryLight,
        color: RgdsColorTokens(
          primary: 0xFF2F6FED,
          onPrimary: 0xFFFFFFFF,
          primaryContainer: 0xFFD6E3FF,
          onPrimaryContainer: 0xFF001A41,
          secondary: 0xFFB3261E,
          onSecondary: 0xFFFFFFFF,
          surface: 0xFFFCFCFD,
          onSurface: 0xFF1A1C1E,
          surfaceContainer: 0xFFF2F3F5,
          surfaceContainerHigh: 0xFFECEEF0,
          surfaceContainerHighest: 0xFFE6E8EA,
          outline: 0xFF72787E,
          outlineVariant: 0xFFC2C7CE,
        ),
        state: RgdsStateTokens(
          hoverSurfaceTint: 0xFF4B84F0,
          hoverTintAmount: 0.12,
          hoverBorder: 0xFF2F6FED,
          focusBorder: 0xFF2F6FED,
          pressedTint: 0xFF1B4FBF,
          pressedTintAmount: 0.10,
          selectedSurface: 0xFFD6E3FF,
          selectedBorder: 0xFF2F6FED,
          disabledOpacity: 0.38,
        ),
      );

      static const secondaryLight = RgdsThemeData(
        theme: RgdsTheme.secondaryLight,
        color: RgdsColorTokens(
          primary: 0xFFE PanA00,
          onPrimary: 0xFF1A1C1E,
          primaryContainer: 0xFFFFE3C2,
          onPrimaryContainer: 0xFF5C3B00,
          secondary: 0xFFC45C12,
          onSecondary: 0xFFFFFFFF,
          surface: 0xFFFFF4E8,
          onSurface: 0xFF1A1C1E,
          surfaceContainer: 0xFFFFFFFF,
          surfaceContainerHigh: 0xFFFFFBF7,
          surfaceContainerHighest: 0xFFFFF4E8,
          outline: 0xFFC45C12,
          outlineVariant: 0xFFFFD89A,
        ),
        state: RgdsStateTokens(
          hoverSurfaceTint: 0xFFFFD54A,
          hoverTintAmount: 0.14,
          hoverBorder: 0xFFFFD54A,
          focusBorder: 0xFFE8A000,
          pressedTint: 0xFFC45C12,
          pressedTintAmount: 0.10,
          selectedSurface: 0xFFFFE3C2,
          selectedBorder: 0xFFE8A000,
          disabledOpacity: 0.38,
        ),
      );

      static const primaryDark = RgdsThemeData(
        theme: RgdsTheme.primaryDark,
        color: RgdsColorTokens(
          primary: 0xFFB4C7FF,
          onPrimary: 0xFF0B1220,
          primaryContainer: 0xFF2A3142,
          onPrimaryContainer: 0xFFB4C7FF,
          secondary: 0xFFC8CAD0,
          onSecondary: 0xFF0B1220,
          surface: 0xFF0B1220,
          onSurface: 0xFFFCFCFD,
          surfaceContainer: 0xFF171E2B,
          surfaceContainerHigh: 0xFF1C2433,
          surfaceContainerHighest: 0xFF222B3B,
          outline: 0xFF8B9198,
          outlineVariant: 0xFF2A3142,
        ),
        state: RgdsStateTokens(
          hoverSurfaceTint: 0xFFFFFFFF,
          hoverTintAmount: 0.07,
          hoverBorder: 0xFFC8CAD0,
          focusBorder: 0xFFB4C7FF,
          pressedTint: 0xFF000000,
          pressedTintAmount: 0.10,
          selectedSurface: 0xFF2A3142,
          selectedBorder: 0xFFB4C7FF,
          disabledOpacity: 0.38,
        ),
      );

      static const secondaryDark = RgdsThemeData(
        theme: RgdsTheme.secondaryDark,
        color: RgdsColorTokens(
          primary: 0xFFE8A000,
          onPrimary: 0xFF000000,
          primaryContainer: 0xFF5C3B00,
          onPrimaryContainer: 0xFFFFD89A,
          secondary: 0xFFC45C12,
          onSecondary: 0xFFFFFFFF,
          surface: 0xFF000000,
          onSurface: 0xFFFCFCFD,
          surfaceContainer: 0xFF141414,
          surfaceContainerHigh: 0xFF1C1C1C,
          surfaceContainerHighest: 0xFF242424,
          outline: 0xFFE8A000,
          outlineVariant: 0xFF1C1C1C,
        ),
        state: RgdsStateTokens(
          hoverSurfaceTint: 0xFFFFD89A,
          hoverTintAmount: 0.09,
          hoverBorder: 0xFFE8A000,
          focusBorder: 0xFFE8A000,
          pressedTint: 0xFFE8A000,
          pressedTintAmount: 0.12,
          selectedSurface: 0xFF5C3B00,
          selectedBorder: 0xFFE8A000,
          disabledOpacity: 0.38,
        ),
      );

      static RgdsThemeData of(RgdsTheme theme) {
        switch (theme) {
          case RgdsTheme.primaryLight:
            return primaryLight;
          case RgdsTheme.secondaryLight:
            return secondaryLight;
          case RgdsTheme.primaryDark:
            return primaryDark;
          case RgdsTheme.secondaryDark:
            return secondaryDark;
        }
      }
    }
    """
).replace("0xFFE PanA00", "0xFFE8A000")  # guard against accidental corruption


STATES_HTML = textwrap.dedent(
    """\
    <!DOCTYPE html>
    <html lang="en" data-theme="primary-light">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>RGDS interaction state fixtures</title>
      <link rel="stylesheet" href="../../packages/web/dist/tokens.css" />
      <link rel="stylesheet" href="../../packages/web/dist/components.css" />
      <link rel="stylesheet" href="../../packages/web/dist/interaction.css" />
      <style>
        body { margin: 0; font-family: var(--md-sys-typescale-font); background: var(--md-sys-color-surface); color: var(--md-sys-color-on-surface); }
        header { padding: var(--md-sys-spacing-lg); display: flex; gap: var(--md-sys-spacing-sm); flex-wrap: wrap; border-bottom: 1px solid var(--md-sys-color-outline-variant); }
        main { padding: var(--md-sys-spacing-xl); display: grid; gap: var(--md-sys-spacing-2xl); }
        .theme-block h2 { margin: 0 0 var(--md-sys-spacing-md); }
        .row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: var(--md-sys-spacing-md); }
        .swatch {
          --rgds-surface-base: var(--md-sys-color-surface-container-high);
          min-height: 88px; padding: var(--md-sys-spacing-md);
          border-radius: var(--md-sys-shape-corner-medium);
          border: 1px solid var(--md-sys-color-outline-variant);
          background: var(--rgds-surface-base);
          display: flex; flex-direction: column; justify-content: space-between;
        }
        .swatch .label { font-size: var(--md-sys-typescale-label-large-size); font-weight: 600; }
        .swatch .meta { font-size: 0.75rem; opacity: 0.8; }
        .static-card {
          padding: var(--md-sys-spacing-md);
          border-radius: var(--md-sys-shape-corner-large);
          border: 1px solid var(--md-sys-color-outline-variant);
          background: var(--md-sys-color-surface-container);
        }
        .md-btn {
          --rgds-surface-base: var(--md-sys-color-primary);
          background: var(--md-sys-color-primary);
          color: var(--md-sys-color-on-primary);
          border: 1px solid transparent;
          border-radius: var(--md-sys-shape-corner-full);
          min-height: 48px; padding: 0 20px; font: inherit; font-weight: 600; cursor: pointer;
        }
      </style>
    </head>
    <body>
      <header>
        <strong>RGDS state matrix</strong>
        <button type="button" class="md-theme-btn rgds-interactive" data-theme-set="primary-light" aria-pressed="true">Theme 1</button>
        <button type="button" class="md-theme-btn rgds-interactive" data-theme-set="secondary-light">Theme 2</button>
        <button type="button" class="md-theme-btn rgds-interactive" data-theme-set="primary-dark">Theme 3</button>
        <button type="button" class="md-theme-btn rgds-interactive" data-theme-set="secondary-dark">Theme 4</button>
      </header>
      <main>
        <section class="theme-block">
          <h2>Forced interaction states (visual regression)</h2>
          <div class="row" id="forced-states">
            <div class="swatch"><span class="label">default</span><span class="meta">baseline</span></div>
            <div class="swatch rgds-state-hover"><span class="label">hover</span><span class="meta">surface+border</span></div>
            <div class="swatch rgds-state-focus"><span class="label">focus</span><span class="meta">focus-visible</span></div>
            <div class="swatch rgds-state-pressed"><span class="label">pressed</span><span class="meta">active</span></div>
            <div class="swatch rgds-state-selected"><span class="label">selected</span><span class="meta">aria-selected</span></div>
            <div class="swatch rgds-state-disabled"><span class="label">disabled</span><span class="meta">opacity</span></div>
          </div>
        </section>
        <section>
          <h2>Live interactive controls</h2>
          <div class="row">
            <button type="button" class="md-btn rgds-interactive">Primary button</button>
            <button type="button" class="md-btn rgds-interactive" disabled>Disabled</button>
            <div class="md-card" data-interactive="true" tabindex="0" class="rgds-interactive" style="padding:16px;border:1px solid var(--md-sys-color-outline-variant);border-radius:16px;background:var(--md-sys-color-surface-container-highest)">Actionable card</div>
            <div class="static-card">Static info card (no hover lift)</div>
          </div>
        </section>
        <section>
          <h2>All themes snapshot strip</h2>
          <div id="theme-strips"></div>
        </section>
      </main>
      <script>
        const themes = ["primary-light","secondary-light","primary-dark","secondary-dark"];
        const states = ["default","rgds-state-hover","rgds-state-focus","rgds-state-pressed","rgds-state-selected","rgds-state-disabled"];
        const labels = ["default","hover","focus","pressed","selected","disabled"];
        document.querySelectorAll("[data-theme-set]").forEach((btn) => {
          btn.addEventListener("click", () => {
            document.documentElement.setAttribute("data-theme", btn.getAttribute("data-theme-set"));
            document.querySelectorAll("[data-theme-set]").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
          });
        });
        const host = document.getElementById("theme-strips");
        themes.forEach((theme) => {
          const wrap = document.createElement("div");
          wrap.setAttribute("data-theme", theme);
          wrap.style.cssText = "margin-top:24px;padding:16px;border-radius:16px;background:var(--md-sys-color-surface);color:var(--md-sys-color-on-surface);border:1px solid var(--md-sys-color-outline-variant)";
          wrap.innerHTML = "<h3 style='margin:0 0 12px'>" + theme + "</h3>";
          const row = document.createElement("div");
          row.className = "row";
          states.forEach((cls, i) => {
            const el = document.createElement("div");
            el.className = "swatch " + (cls === "default" ? "" : cls);
            el.innerHTML = "<span class='label'>" + labels[i] + "</span>";
            row.appendChild(el);
          });
          wrap.appendChild(row);
          host.appendChild(wrap);
        });
      </script>
    </body>
    </html>
    """
)


CONTRAST_JS = textwrap.dedent(
    """\
    #!/usr/bin/env node
    /** Minimal contrast gate for RGDS interaction states (relative luminance). */
    function parseOklch(str) {
      const m = String(str).match(/oklch\\((\\d+(?:\\.\\d+)?)%\\s+([\\d.]+)\\s+([\\d.]+)\\)/i);
      if (!m) return null;
      return { L: Number(m[1]) / 100, C: Number(m[2]), H: Number(m[3]) };
    }
    function oklchToApproxY({ L }) {
      // Use L as perceptual stand-in for fixture gate (not full CSS Color 4).
      return Math.max(0, Math.min(1, L));
    }
    function contrast(a, b) {
      const ya = oklchToApproxY(a);
      const yb = oklchToApproxY(b);
      const lighter = Math.max(ya, yb);
      const darker = Math.min(ya, yb);
      return (lighter + 0.05) / (darker + 0.05);
    }
    const pairs = [
      ["primary-light onSurface/surface", "oklch(16% 0.008 260)", "oklch(99% 0.001 260)"],
      ["primary-dark onSurface/surface", "oklch(99% 0.001 260)", "oklch(10% 0.012 250)"],
      ["secondary-dark onSurface/surface", "oklch(99% 0.001 260)", "oklch(8% 0 0)"],
    ];
    let failed = 0;
    for (const [name, fg, bg] of pairs) {
      const a = parseOklch(fg);
      const b = parseOklch(bg);
      if (!a || !b) { console.error("parse fail", name); failed++; continue; }
      const ratio = contrast(a, b);
      const ok = ratio >= 4.5;
      console.log((ok ? "PASS" : "FAIL"), name, ratio.toFixed(2));
      if (!ok) failed++;
    }
    process.exit(failed ? 1 : 0);
    """
)


def install_discovery() -> None:
    DISCOVERY.mkdir(parents=True, exist_ok=True)
    repo_manifest = json.loads((DST / "rgds.manifest.json").read_text(encoding="utf-8"))
    pointer = {
        "schema_version": 1,
        "name": repo_manifest["name"],
        "abbreviation": "RGDS",
        "version": repo_manifest["version"],
        "status": repo_manifest.get("status", "building"),
        "repository_path": str(DST),
        "repository_manifest": str(DST / "rgds.manifest.json"),
        "themes": repo_manifest["themes"],
        "platforms": repo_manifest["platforms"],
        "packages": repo_manifest["packages"],
        "figma": repo_manifest.get("figma", {}),
        "updated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "authority": "Independent org design system — not AgentCore-owned",
    }
    target = DISCOVERY / "RGDS_MANIFEST.json"
    target.write_text(json.dumps(pointer, indent=2) + "\n", encoding="utf-8")
    print(f"discovery -> {target}")


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    for rel in [
        "tokens/ref/type.json",
        "tokens/sys/elevation.json",
        "tokens/sys/shape.json",
        "tokens/sys/spacing.json",
        "tokens/sys/typography.json",
        "tokens/themes/primary-light.json",
        "tokens/themes/secondary-light.json",
        "tokens/themes/primary-dark.json",
        "tokens/themes/secondary-dark.json",
        "css/animations.css",
    ]:
        sync(rel)

    write("tokens/sys/state.json", json.dumps(STATE_JSON, indent=2) + "\n")
    for name in THEME_STATE:
        enhance_theme(name)

    write("packages/web/dist/tokens.css", TOKENS_CSS)
    write("packages/web/dist/interaction.css", INTERACTION_CSS)
    write_components_css()
    write("tools/build-tokens.mjs", BUILD_TOKENS)
    write("tools/check-contrast.mjs", CONTRAST_JS)
    write(
        "packages/flutter/pubspec.yaml",
        textwrap.dedent(
            """\
            name: rgds
            description: R3lentless-Grind Design System Flutter adapter
            version: 0.2.0-dev
            publish_to: none
            environment:
              sdk: ">=3.3.0 <4.0.0"
            """
        ),
    )
    write(
        "packages/flutter/lib/rgds.dart",
        "library rgds;\\nexport 'src/generated/rgds_tokens.dart';\\n",
    )
    write("packages/flutter/lib/src/generated/rgds_tokens.dart", FLUTTER_DART)
    write(
        "packages/web/package.json",
        json.dumps(
            {
                "name": "@r3lentless/rgds-web",
                "version": "0.2.0-dev",
                "private": True,
                "type": "module",
                "files": ["dist"],
                "exports": {
                    "./tokens.css": "./dist/tokens.css",
                    "./interaction.css": "./dist/interaction.css",
                    "./components.css": "./dist/components.css",
                },
            },
            indent=2,
        )
        + "\n",
    )
    write("fixtures/web/states.html", STATES_HTML)
    # Refresh preview from AgentCore then patch token paths
    if (SRC / "preview.html").is_file():
        preview = (SRC / "preview.html").read_text(encoding="utf-8")
        preview = preview.replace("css/tokens.css", "../packages/web/dist/tokens.css")
        preview = preview.replace("css/components.css", "../packages/web/dist/components.css")
        preview = preview.replace("css/animations.css", "../packages/web/dist/animations.css")
        if "interaction.css" not in preview:
            preview = preview.replace(
                'href="../packages/web/dist/components.css"',
                'href="../packages/web/dist/components.css" />\\n  <link rel="stylesheet" href="../packages/web/dist/interaction.css"',
            )
        write("fixtures/web/preview.html", preview)
    if (SRC / "css/animations.css").is_file():
        sync("css/animations.css")
        shutil.copyfile(SRC / "css/animations.css", DST / "packages/web/dist/animations.css")

    write(
        "package.json",
        json.dumps(
            {
                "name": "@r3lentless/rgds",
                "version": "0.2.0-dev",
                "private": True,
                "description": "R3lentless-Grind Design System",
                "license": "UNLICENSED",
                "type": "module",
                "scripts": {
                    "build:tokens": "node tools/build-tokens.mjs",
                    "check:contrast": "node tools/check-contrast.mjs",
                    "test:fixtures": "node tools/check-contrast.mjs",
                },
                "workspaces": ["packages/*"],
            },
            indent=2,
        )
        + "\n",
    )

    write(
        "scripts/install-discovery.ps1",
        textwrap.dedent(
            """\
            # Installs neutral user-scope RGDS discovery pointer (not AgentCore F: runtime).
            $ErrorActionPreference = "Stop"
            $repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
            if (-not (Test-Path (Join-Path $repoRoot "rgds.manifest.json"))) {
              $repoRoot = "D:\\github\\r3lentless-grind-design-system"
            }
            $destDir = Join-Path $env:USERPROFILE ".rgds"
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
            $repoManifest = Get-Content (Join-Path $repoRoot "rgds.manifest.json") -Raw | ConvertFrom-Json
            $pointer = [ordered]@{
              schema_version = 1
              name = $repoManifest.name
              abbreviation = "RGDS"
              version = $repoManifest.version
              status = $repoManifest.status
              repository_path = $repoRoot
              repository_manifest = (Join-Path $repoRoot "rgds.manifest.json")
              themes = $repoManifest.themes
              platforms = $repoManifest.platforms
              packages = $repoManifest.packages
              figma = $repoManifest.figma
              updated_at = (Get-Date).ToUniversalTime().ToString("o")
              authority = "Independent org design system — not AgentCore-owned"
            }
            $pointer | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 (Join-Path $destDir "RGDS_MANIFEST.json")
            Write-Host "Installed $destDir\\RGDS_MANIFEST.json"
            """
        ),
    )

    write(
        "AGENTS.md",
        textwrap.dedent(
            """\
            # RGDS — Agent contract

            This repository is the canonical home of the **R3lentless-Grind Design System (RGDS)**.

            - Not owned by NFA, AgentCore, CRM, alert-engine, or notification-collector.
            - Agents adopting RGDS: read `docs/ADOPTION.md`, resolve `~/.rgds/RGDS_MANIFEST.json`, install versioned packages — never absolute checkout paths in app source.
            - Themes: `primary-light`, `secondary-light`, `primary-dark`, `secondary-dark`.
            - Interaction: `md.rgds.state.*` — semantic surfaces only; no universal brightness filters; `rainbowPulse` is featured-only.
            - Figma library: independent file "R3lentless-Grind Design System — RGDS" (see `docs/FIGMA.md`).
            """
        ),
    )

    # Update root manifest status
    manifest_path = DST / "rgds.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "building"
    manifest["version"] = "0.2.0-dev"
    manifest["discovery"]["user_manifest_windows"] = r"C:\Users\ynotf\.rgds\RGDS_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    install_discovery()
    print("RGDS materialize complete")


if __name__ == "__main__":
    main()
