#!/usr/bin/env python3
"""RGDS finish pass: PROVISIONAL brand marking + remaining package/docs/validation.

Does not freeze final brand. Does not touch NFA.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

DST = Path(r"D:\github\r3lentless-grind-design-system")
DISCOVERY = Path(r"C:\Users\ynotf\.rgds")
AUDIT = Path(r"D:\github\agentcore-control-plane\audits\rgds")
FILE_KEY = "KbhSAUCrADaqhxOm7jM2FC"
VERSION = "0.3.0-rc.1"


def W(rel: str, text: str) -> None:
    p = DST / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")
    print("W", rel)


def replace_seed_status() -> None:
    """TEMPORARY_PLACEHOLDER → PROVISIONAL across token JSON + docs."""
    count = 0
    for path in DST.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".json", ".md", ".css", ".ts", ".tsx", ".dart"}:
            continue
        if ".git" in path.parts or "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "TEMPORARY_PLACEHOLDER" not in text and "TEMPORARY seed" not in text:
            continue
        new = text.replace("TEMPORARY_PLACEHOLDER", "PROVISIONAL")
        new = new.replace("TEMPORARY seed tonal values", "PROVISIONAL seed tonal values")
        new = new.replace("TEMPORARY brand seeds", "PROVISIONAL brand seeds")
        if new != text:
            path.write_text(new, encoding="utf-8", newline="\n")
            count += 1
            print("seed→PROVISIONAL", path.relative_to(DST))
    print("updated files", count)


def write_brand_policy() -> None:
    W(
        "docs/BRAND.md",
        f"""# Brand palette policy

## Two independent gates

| Gate | Meaning | Status |
| --- | --- | --- |
| **SYSTEM ARCHITECTURE COMPLETE** | Foundations, themes, Figma library, packages, discovery, validation, cold adopt | Target of this release (`{VERSION}`) |
| **FINAL BRAND PALETTE APPROVED** | Operator-approved permanent hex/OKLCH seeds | **Not yet** — palette is **PROVISIONAL** |

## Source of truth

Canonical brand primitives live **only** in:

`tokens/ref/palette.json`

Marked: `rgds.seedStatus: PROVISIONAL`

Semantic roles (`tokens/sys/color.json`), theme modes (`tokens/themes/*`), Figma Variables,
CSS (`packages/web/css|dist`), Flutter generated tokens, and Make guidelines **must not**
hardcode independent brand hex. Change primitives → regenerate/sync → consumers update.

## Refinement procedure (later)

1. Edit `tokens/ref/palette.json` only.
2. Run `npm run build:tokens` / package builds / Figma variable sync.
3. Re-run `node tools/validate-all.mjs`.
4. Operator sets `rgds.seedStatus` to `FINAL` and updates this doc when approving.

Do **not** stop architecture work for palette tuning.
""",
    )


def expand_web_components() -> None:
    comp = DST / "packages/web/src/components.tsx"
    text = comp.read_text(encoding="utf-8")
    if "RgdsChip" not in text:
        text = text.rstrip() + """

export function RgdsChip({
  children,
  className,
  selected,
  onClick,
}: Common & { selected?: boolean; onClick?: () => void }) {
  return (
    <button
      type="button"
      className={cx("rgds-chip", "rgds-interactive", className)}
      aria-pressed={selected || undefined}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export function RgdsToast({ children, className }: Common) {
  return (
    <div role="status" className={cx("rgds-toast", className)}>
      {children}
    </div>
  );
}

export function RgdsProgress({
  value = 0,
  className,
}: {
  value?: number;
  className?: string;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div
      className={cx("rgds-progress", className)}
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className="rgds-progress__bar" style={{ width: `${clamped}%` }} />
    </div>
  );
}
"""
        comp.write_text(text + "\n", encoding="utf-8", newline="\n")
        print("web components +chip/toast/progress")

    idx = DST / "packages/web/src/index.ts"
    i = idx.read_text(encoding="utf-8")
    if "RgdsChip" not in i:
        i = i.replace(
            "RgdsAppShell,",
            "RgdsAppShell,\n  RgdsChip,\n  RgdsToast,\n  RgdsProgress,",
        )
        # also export types if needed - fine
        if "RgdsChip" not in i:
            i = i.rstrip() + "\nexport { RgdsChip, RgdsToast, RgdsProgress } from './components';\n"
        idx.write_text(i, encoding="utf-8", newline="\n")

    for css_path in (
        DST / "packages/web/css/components.css",
        DST / "packages/web/dist/components.css",
    ):
        c = css_path.read_text(encoding="utf-8")
        if ".rgds-chip" not in c:
            c += """
.rgds-chip {
  min-height: 32px;
  padding: 0 var(--md-sys-spacing-md);
  border-radius: var(--md-sys-shape-corner-full);
  border: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
  font: inherit;
  cursor: pointer;
}
.rgds-toast {
  position: fixed;
  bottom: var(--md-sys-spacing-lg);
  right: var(--md-sys-spacing-lg);
  padding: var(--md-sys-spacing-md) var(--md-sys-spacing-lg);
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
  box-shadow: var(--md-sys-elevation-level3);
  border: 1px solid var(--md-sys-color-outline-variant);
}
.rgds-progress {
  height: 4px;
  border-radius: var(--md-sys-shape-corner-full);
  background: var(--md-sys-color-surface-container-highest);
  overflow: hidden;
}
.rgds-progress__bar {
  height: 100%;
  background: var(--md-sys-color-primary);
}
"""
            css_path.write_text(c, encoding="utf-8", newline="\n")
            print("css", css_path.name)


def expand_flutter() -> None:
    chip = DST / "packages/flutter/lib/src/widgets/rgds_chip.dart"
    if not chip.exists():
        W(
            "packages/flutter/lib/src/widgets/rgds_chip.dart",
            """import 'package:flutter/material.dart';

class RgdsChip extends StatelessWidget {
  const RgdsChip({
    super.key,
    required this.label,
    this.selected = false,
    this.onSelected,
  });

  final String label;
  final bool selected;
  final ValueChanged<bool>? onSelected;

  @override
  Widget build(BuildContext context) {
    return FilterChip(
      label: Text(label),
      selected: selected,
      onSelected: onSelected,
    );
  }
}
""",
        )
    toast = DST / "packages/flutter/lib/src/widgets/rgds_progress.dart"
    if not toast.exists():
        W(
            "packages/flutter/lib/src/widgets/rgds_progress.dart",
            """import 'package:flutter/material.dart';

class RgdsProgress extends StatelessWidget {
  const RgdsProgress({super.key, this.value});

  /// Null = indeterminate.
  final double? value;

  @override
  Widget build(BuildContext context) {
    return LinearProgressIndicator(value: value);
  }
}
""",
        )
    lib = DST / "packages/flutter/lib/rgds.dart"
    t = lib.read_text(encoding="utf-8")
    if "rgds_chip" not in t:
        t = t.rstrip() + "\nexport 'src/widgets/rgds_chip.dart';\nexport 'src/widgets/rgds_progress.dart';\n"
        lib.write_text(t, encoding="utf-8", newline="\n")


def update_authority_and_manifest() -> None:
    auth = DST / "docs/AUTHORITY.md"
    a = auth.read_text(encoding="utf-8")
    a = a.replace("TEMPORARY_PLACEHOLDER", "PROVISIONAL")
    if "SYSTEM ARCHITECTURE COMPLETE" not in a:
        a = a.rstrip() + """

## Production readiness (two gates)

1. **SYSTEM ARCHITECTURE COMPLETE** — structure, themes, Figma, packages, discovery, validation.
2. **FINAL BRAND PALETTE APPROVED** — operator sign-off on `tokens/ref/palette.json` (currently **PROVISIONAL**).

Architecture completion does **not** require final brand hex. See `docs/BRAND.md`.
"""
    auth.write_text(a, encoding="utf-8", newline="\n")

    manifest_path = DST / "rgds.manifest.json"
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    m["brand"] = {
        "seedStatus": "PROVISIONAL",
        "note": (
            "Palette is locked as working provisional seeds for architecture completion. "
            "Final operator approval is a separate gate (docs/BRAND.md). "
            "Change only tokens/ref/palette.json then regenerate."
        ),
        "gates": {
            "systemArchitecture": "release-candidate",
            "finalBrandPalette": "pending-operator",
        },
    }
    m["version"] = VERSION
    m["status"] = "release-candidate"
    # keep component list; may expand after figma
    manifest_path.write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")

    pointer = {
        "schema_version": 1,
        "name": m["name"],
        "abbreviation": "RGDS",
        "version": VERSION,
        "status": m["status"],
        "repository_path": str(DST),
        "repository_manifest": str(DST / "rgds.manifest.json"),
        "themes": m["themes"],
        "platforms": m["platforms"],
        "packages": m["packages"],
        "figma": {
            "file_key": FILE_KEY,
            "library_url": f"https://www.figma.com/design/{FILE_KEY}",
            "component_sets": m["figma"].get("component_sets", []),
            "pages": m["figma"].get("pages", []),
        },
        "adoption": "docs/ADOPTION.md",
        "brand_seedStatus": "PROVISIONAL",
        "gates": m["brand"]["gates"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "authority": "Independent org design system — not AgentCore-owned",
    }
    DISCOVERY.mkdir(parents=True, exist_ok=True)
    (DISCOVERY / "RGDS_MANIFEST.json").write_text(
        json.dumps(pointer, indent=2) + "\n", encoding="utf-8"
    )

    adopt = (DST / "docs/ADOPTION.md").read_text(encoding="utf-8")
    adopt = adopt.replace("TEMPORARY_PLACEHOLDER", "PROVISIONAL")
    if "PROVISIONAL" not in adopt or "FINAL BRAND" not in adopt:
        adopt = adopt.rstrip() + """

## Brand

Palette seeds are **PROVISIONAL**. System architecture can be adopted now.
Final brand approval is a separate operator gate (`docs/BRAND.md`).
"""
    W("docs/ADOPTION.md", adopt)

    readme = (DST / "README.md").read_text(encoding="utf-8")
    readme = readme.replace("TEMPORARY_PLACEHOLDER", "PROVISIONAL")
    W("README.md", readme)


def update_changelog() -> None:
    cl = DST / "CHANGELOG.md"
    t = cl.read_text(encoding="utf-8") if cl.exists() else "# Changelog\n"
    if "PROVISIONAL brand policy" not in t:
        t = t.replace(
            f"## {VERSION}",
            f"## {VERSION}\n\n- Brand seeds marked **PROVISIONAL** (architecture complete ≠ final palette)\n- `docs/BRAND.md` two-gate policy",
            1,
        )
        # if replace failed because format differs
        if "PROVISIONAL brand policy" not in t and "docs/BRAND.md" not in t:
            t = f"## {VERSION}\n\n- Brand seeds marked PROVISIONAL; see docs/BRAND.md\n\n" + t
        cl.write_text(t, encoding="utf-8", newline="\n")


def write_audit() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "RGDS_COMPLETION_STATUS.md").write_text(
        f"""# RGDS completion status

## Gates

| Gate | Status |
| --- | --- |
| SYSTEM ARCHITECTURE COMPLETE | **In progress → targeting {VERSION} RC** |
| FINAL BRAND PALETTE APPROVED | **Pending** (seeds = PROVISIONAL) |

## Facts

- Repo: `{DST}`
- Figma: https://www.figma.com/design/{FILE_KEY}
- Discovery: `C:\\\\Users\\\\ynotf\\\\.rgds\\\\RGDS_MANIFEST.json`
- Brand: **PROVISIONAL** — refinement later via `tokens/ref/palette.json` only
- NFA / real consumers: **not modified**
- Make kit: guidelines ready; npm publish + Figma Make assembly operator-gated

## Validation commands

```bash
node tools/validate-all.mjs
node tools/cold-adopt-sim.mjs
npm run build -w @r3lentless/rgds-web
npm run test -w @r3lentless/rgds-web
cd packages/flutter && flutter test && flutter analyze
```
""",
        encoding="utf-8",
        newline="\n",
    )


def ensure_fixture_mentions_provisional() -> None:
    html = DST / "fixtures/consumers/web/index.html"
    if html.exists():
        t = html.read_text(encoding="utf-8")
        if "PROVISIONAL" not in t:
            t = t.replace(
                "<title>RGDS isolated web consumer</title>",
                "<title>RGDS isolated web consumer (PROVISIONAL brand)</title>",
            )
            html.write_text(t, encoding="utf-8", newline="\n")


def main() -> None:
    replace_seed_status()
    write_brand_policy()
    expand_web_components()
    expand_flutter()
    update_authority_and_manifest()
    update_changelog()
    ensure_fixture_mentions_provisional()
    write_audit()
    # Fix index exports cleanly
    idx = DST / "packages/web/src/index.ts"
    idx.write_text(
        """export {
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
  RgdsChip,
  RgdsToast,
  RgdsProgress,
  type RgdsButtonProps,
  type RgdsCardProps,
  type RgdsTextFieldProps,
} from "./components";
""",
        encoding="utf-8",
        newline="\n",
    )
    print("done provisional+finish")


if __name__ == "__main__":
    main()
