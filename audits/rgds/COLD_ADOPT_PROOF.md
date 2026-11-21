# Cold adopt proof — RGDS 1.0.0

Generated: 2026-09-22T17:47:59.402000+00:00

Instruction simulated: **Adopt RGDS for this project.**

## Proven

| Gate | Result |
| --- | --- |
| `~/.rgds/RGDS_MANIFEST.json` | version 1.0.0, Figma KbhSAUCrADaqhxOm7jM2FC, 4 themes |
| `node tools/cold-adopt-sim.mjs` | COLD PASS (23 component sets) |
| `node tools/prove-discovery.mjs` | PASS |
| `node tools/parity-check.mjs` | PASS 23/23 |
| `node tools/visual-regression.mjs` | PASS |
| `node tools/validate-all.mjs` | PASS |
| Web consumer `fixtures/consumers/web-vite` | vite build PASS vs packed tgz |
| Flutter consumer `fixtures/consumers/flutter` | flutter test PASS |
| Web unit tests | 3 PASS |
| Flutter package tests | PASS |

## Agent path

1. Read `C:\\Users\\ynotf\\.rgds\\RGDS_MANIFEST.json`
2. Open `repository_manifest` + `docs/ADOPTION.md`
3. Open Figma https://www.figma.com/design/KbhSAUCrADaqhxOm7jM2FC
4. Install `@r3lentless/rgds-web@1.0.0` from npm or `dist-packages/*.tgz`
5. Flutter: depend on `rgds` 1.0.0
6. `applyRgdsTheme(...)` / `rgdsThemeData(RgdsTheme.*)`
7. Compose only exported RGDS components; use `contracts/figma-code-map.json`
