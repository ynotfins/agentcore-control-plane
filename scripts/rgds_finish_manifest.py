"""Finish RGDS manifest + discovery after materialize."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DST = Path(r"D:\github\r3lentless-grind-design-system")
DISCOVERY = Path(r"C:\Users\ynotf\.rgds")

manifest = {
    "$schema": "./schemas/rgds-manifest.schema.json",
    "name": "R3lentless-Grind Design System",
    "abbreviation": "RGDS",
    "version": "0.2.0-dev",
    "status": "building",
    "repository": {
        "type": "git",
        "path": r"D:\github\r3lentless-grind-design-system",
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
        "note": "User-scope pointer is neutral; not AgentCore F: runtime. CI uses package versions only.",
    },
    "figma": {
        "file_key": None,
        "library_url": None,
        "documentation": "docs/FIGMA.md",
    },
    "packages": {"npm": "@r3lentless/rgds", "flutter": "rgds"},
    "authority": [
        "docs/AUTHORITY.md",
        "tokens/",
        "docs/FIGMA.md",
        "packages/",
    ],
    "build": {
        "web": [
            "packages/web/dist/tokens.css",
            "packages/web/dist/interaction.css",
            "packages/web/dist/components.css",
        ],
        "flutter": ["packages/flutter/lib/src/generated/rgds_tokens.dart"],
    },
}

(DST / "rgds.manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
)

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

(DST / "packages/flutter/lib/rgds.dart").write_text(
    "library rgds;\nexport 'src/generated/rgds_tokens.dart';\n",
    encoding="utf-8",
)

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "rgds-manifest.schema.json",
    "type": "object",
    "required": ["name", "abbreviation", "version", "themes", "platforms"],
    "properties": {
        "name": {"type": "string"},
        "abbreviation": {"type": "string"},
        "version": {"type": "string"},
        "status": {"type": "string"},
        "themes": {"type": "array", "items": {"type": "string"}},
        "platforms": {"type": "array", "items": {"type": "string"}},
        "figma": {"type": "object"},
        "packages": {"type": "object"},
        "discovery": {"type": "object"},
    },
}
(DST / "schemas").mkdir(parents=True, exist_ok=True)
(DST / "schemas/rgds-manifest.schema.json").write_text(
    json.dumps(schema, indent=2) + "\n", encoding="utf-8"
)

ps1 = r'''# Installs neutral user-scope RGDS discovery pointer (not AgentCore F: runtime).
$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$destDir = Join-Path $env:USERPROFILE ".rgds"
[void][System.IO.Directory]::CreateDirectory($destDir)
$repoManifest = Get-Content (Join-Path $repoRoot "rgds.manifest.json") -Raw | ConvertFrom-Json
$pointer = [ordered]@{
  schema_version = 1
  name = $repoManifest.name
  abbreviation = "RGDS"
  version = $repoManifest.version
  status = $repoManifest.status
  repository_path = "$repoRoot"
  repository_manifest = (Join-Path $repoRoot "rgds.manifest.json")
  themes = $repoManifest.themes
  platforms = $repoManifest.platforms
  packages = $repoManifest.packages
  figma = $repoManifest.figma
  updated_at = (Get-Date).ToUniversalTime().ToString("o")
  authority = "Independent org design system — not AgentCore-owned"
}
$json = $pointer | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText((Join-Path $destDir "RGDS_MANIFEST.json"), $json)
Write-Host "Installed $(Join-Path $destDir 'RGDS_MANIFEST.json')"
'''
(DST / "scripts/install-discovery.ps1").write_text(ps1, encoding="utf-8", newline="\n")

probe = DST / "WRITE_PROBE.txt"
if probe.exists():
    probe.unlink()

print("manifest+discovery OK")
