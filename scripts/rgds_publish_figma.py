"""Publish Figma file_key into RGDS manifests + FIGMA.md + adoption proof."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DST = Path(r"D:\github\r3lentless-grind-design-system")
DISCOVERY = Path(r"C:\Users\ynotf\.rgds")
AUDIT = Path(r"D:\github\agentcore-control-plane\audits\rgds")
FILE_KEY = "KbhSAUCrADaqhxOm7jM2FC"
FILE_URL = f"https://www.figma.com/design/{FILE_KEY}"

manifest_path = DST / "rgds.manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["figma"] = {
    "file_key": FILE_KEY,
    "library_url": FILE_URL,
    "documentation": "docs/FIGMA.md",
    "component_sets": [
        "RGDS / Button",
        "RGDS / Card / Interactive",
    ],
    "color_collection": "RGDS / Color",
    "modes": [
        "primary-light",
        "secondary-light",
        "primary-dark",
        "secondary-dark",
    ],
    "code_connect": {
        "status": "deferred",
        "note": "Pro plan may lack Code Connect; naming/APIs reserved for later attachment.",
    },
}
manifest["status"] = "alpha"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

DISCOVERY.mkdir(parents=True, exist_ok=True)
pointer = {
    "schema_version": 1,
    "name": manifest["name"],
    "abbreviation": "RGDS",
    "version": manifest["version"],
    "status": manifest["status"],
    "repository_path": str(DST),
    "repository_manifest": str(DST / "rgds.manifest.json"),
    "themes": manifest["themes"],
    "platforms": manifest["platforms"],
    "packages": manifest["packages"],
    "figma": manifest["figma"],
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "authority": "Independent org design system — not AgentCore-owned",
}
(DISCOVERY / "RGDS_MANIFEST.json").write_text(
    json.dumps(pointer, indent=2) + "\n", encoding="utf-8"
)

figma_md = f"""# RGDS Figma library

Independent organization design system file (not the NFA Figma library).

- **File:** [R3lentless-Grind Design System — RGDS]({FILE_URL})
- **file_key:** `{FILE_KEY}`
- **Color collection:** `RGDS / Color` with modes:
  - `primary-light`
  - `secondary-light`
  - `primary-dark`
  - `secondary-dark`
- **Components (State variants):**
  - `RGDS / Button` — Default, Hover, Focus, Pressed, Selected, Disabled
  - `RGDS / Card / Interactive` — same states (interactive only; static cards are separate)

## Code Connect

Deferred until plan supports it. Component set names, descriptions, and package exports
(`@r3lentless/rgds-web`, `rgds` Flutter) are stable attachment points — do not rename lightly.

## Agent inspection

Use Figma MCP against `{FILE_KEY}` to inspect default and interaction states. Theme
appearance resolves via variable modes — do not maintain four duplicated component libraries.
"""
(DST / "docs/FIGMA.md").write_text(figma_md, encoding="utf-8", newline="\n")

adoption = """# Adoption (cold path)

1. Read `C:\\\\Users\\\\ynotf\\\\.rgds\\\\RGDS_MANIFEST.json` (or `$HOME/.rgds/RGDS_MANIFEST.json`).
2. Open `repository_manifest` → `rgds.manifest.json` for version, themes, packages, Figma `file_key`.
3. Install versioned packages (`@r3lentless/rgds-web`, Flutter `rgds`) — never absolute checkout paths in app `dependencies`.
4. Apply `data-theme` / Flutter `RgdsTheme` and import interaction CSS / state tokens.
5. Inspect Figma library linked in the manifest for visual + state truth.

AgentCore may point at the user-scope manifest; AgentCore does not own RGDS.
"""
(DST / "docs/ADOPTION.md").write_text(adoption, encoding="utf-8", newline="\n")

proof = '''#!/usr/bin/env node
import { readFileSync, existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const pointerPath = join(homedir(), ".rgds", "RGDS_MANIFEST.json");
if (!existsSync(pointerPath)) {
  console.error("FAIL missing discovery pointer", pointerPath);
  process.exit(1);
}
const pointer = JSON.parse(readFileSync(pointerPath, "utf8"));
const required = ["repository_path", "repository_manifest", "version", "themes", "figma"];
for (const key of required) {
  if (!(key in pointer)) {
    console.error("FAIL pointer missing", key);
    process.exit(1);
  }
}
if (!pointer.figma?.file_key) {
  console.error("FAIL figma.file_key missing");
  process.exit(1);
}
const repoManifest = JSON.parse(readFileSync(pointer.repository_manifest, "utf8"));
if (repoManifest.figma.file_key !== pointer.figma.file_key) {
  console.error("FAIL pointer/repo figma key drift");
  process.exit(1);
}
console.log("PASS cold discovery", {
  version: pointer.version,
  figma: pointer.figma.file_key,
  themes: pointer.themes.length,
});
'''
(DST / "tools/prove-discovery.mjs").write_text(proof, encoding="utf-8", newline="\n")

pkg = json.loads((DST / "package.json").read_text(encoding="utf-8"))
pkg.setdefault("scripts", {})
pkg["scripts"]["prove:discovery"] = "node tools/prove-discovery.mjs"
(DST / "package.json").write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")

AUDIT.mkdir(parents=True, exist_ok=True)
status = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "rgds_repo": str(DST),
    "discovery": str(DISCOVERY / "RGDS_MANIFEST.json"),
    "figma_file_key": FILE_KEY,
    "figma_url": FILE_URL,
    "stage_b": "pathless Figma MCP exception added to hooks.py",
    "consumer_apps_modified": False,
    "status": "alpha — foundations + Figma modes/components + discovery live",
}
(AUDIT / "FIGMA_CREATE_STATUS.json").write_text(
    json.dumps(status, indent=2) + "\n", encoding="utf-8"
)
(AUDIT / "RGDS_MILESTONE_STATUS.md").write_text(
    f"""# RGDS milestone status

- Independent repo: `{DST}`
- Discovery: `C:\\\\Users\\\\ynotf\\\\.rgds\\\\RGDS_MANIFEST.json`
- Figma: {FILE_URL}
- Web fixtures: `fixtures/web/states.html`, `packages/web/dist/*.css`
- Flutter tokens: `packages/flutter/lib/src/generated/rgds_tokens.dart`
- Interaction: `md.rgds.state.*` semantic axes (no universal brightness filter)
- Consumer apps: **not modified**
""",
    encoding="utf-8",
    newline="\n",
)

print("published", FILE_KEY)
