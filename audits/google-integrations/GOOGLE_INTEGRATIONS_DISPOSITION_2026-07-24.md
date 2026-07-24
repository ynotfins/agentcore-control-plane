# Google Integrations Disposition — Phase 4B

Date: 2026-07-24 (EDT)  
Task: PHASE_4B (Firebase / Sheets / Apps Script normalization)  
Canonical repo: `D:\github\agentcore-control-plane`  
Related: `audits/skills-hub/SKILLS_HUB_BIFROST_ACCEPTANCE_2026-07-23.md`

Sanitized: no tokens, no client secrets, no access tokens recorded.

---

## Verdict

| Integration | Registry status | Enabled | Default exposure | Live Bifrost client |
|---|---|---|---|---|
| Firebase MCP (`firebase-mcp`) | `dormant_project_scoped` | `false` | none (`capability_profiles: []`) | **absent** |
| Google Sheets MCP (`google-sheets-mcp`) | `developer_preview_oauth_pending` | `false` | none (`capability_profiles: []`) | **absent** |
| Apps Script | deferred (notes only) | n/a | none | **absent** |

Gateway `tools/list` post-render/restart: `firebase=0`, `sheets=0`.

---

## Firebase — dormant project-scoped

### Preserved

- Full registry record retained (not deleted).
- Authenticated Firebase CLI state preserved (operator login unchanged).
- Package pin evidence: `firebase-tools@15.24.0`.

### Removed from live/default surface

- `enabled: false`, `deferred: true`, `status: dormant_project_scoped`.
- Removed from builder/reviewer/docs default exposure (`capability_profiles: []`).
- Not present in rendered `H:\AgentRuntime\bifrost\config.json` `mcp.client_configs`.
- Cleared User-scope `FIREBASE_PROJECT_ID` (was `alerts-sheets-bb09c`) — **no machine-global project selected**.
- Removed `FIREBASE_PROJECT_ID` from registry `env_var_names` so renderers do not imply a global project env.

### Future wrapper requirements (not built in Phase 4B)

Documented in registry notes:

1. Launch against a validated registered project directory using `--dir`.
2. Restrict features using `--only`.
3. Resolve project identity from `agentcore-project-router`.
4. One bounded process per project/worktree where needed.
5. Prevent cross-project state reuse.
6. Separate read and mutation tools.
7. Operator-gate deploy/delete/admin operations (`firebase_init` / `firebase_deploy` already denied when ever re-enabled).

No Firebase tool is visible without a future JIT project lease.

### Source/runtime drift correction

Earlier Phase 4 had connected Firebase live while the desired Phase 4B posture is deferred.
Re-render from registry after normalization:

- Enabled clients (13): includes `skills_hub`; excludes `firebase_mcp` and `google_sheets_mcp`.
- Validators: `validate_contracts.py` OK after schema extension for `dormant_project_scoped`.

---

## Google Sheets — developer preview, OAuth pending

### Official target (documented)

| Field | Value |
|---|---|
| Server URL | `https://sheetsmcp.googleapis.com/mcp/v1` |
| Transport | HTTP |
| Authentication | OAuth 2.0 client flow with **renewable** credential state |
| Capability split (future) | `sheets-read` / `sheets-write` |

### Explicitly forbidden in this phase

- Do **not** request or store `GOOGLE_SHEETS_ACCESS_TOKEN` as a persistent Windows User variable.
- Do **not** treat a manually copied short-lived access token as durable authentication.
- Removed `GOOGLE_SHEETS_ACCESS_TOKEN` from registry `env_var_names` and removed Bearer header stub that referenced it.
- Registry `auth_type` set to schema-valid `oauth` (not a static headers token).
- Confirmed User-scope `GOOGLE_SHEETS_ACCESS_TOKEN` **absent**.

### Activation gates (all must pass later)

1. Bifrost OAuth compatibility proven with Google OAuth flow.
2. Consent/scopes approved.
3. Credential storage protected (not plain Windows env var).
4. Refresh behavior passes.
5. Read/write profiles separated (`sheets-read` / `sheets-write`).
6. Prompt-injection risk documented.
7. Operator approves activation.

**No OAuth setup performed in Phase 4B.**

---

## Apps Script

- No official dedicated MCP as of 2026-07-24.
- Keep deferred.
- Do **not** implement a custom Apps Script API wrapper.
- Do **not** create credentials, endpoints, or tools for Apps Script in this phase.

---

## Regression proof (post-normalization)

| Check | Result |
|---|---|
| Bifrost health 200 | PASS |
| PostgreSQL Running + Automatic | PASS |
| Ten memory tools | PASS |
| Four project-router tools | PASS |
| Zero Swarm / Obsidian | PASS |
| Skills-Hub read/search/get via Bifrost | PASS |
| Skills-Hub cannot install/write | PASS (`install_skill` not exposed) |
| Firebase tools not visible by default | PASS |
| Google Sheets tools not visible | PASS |
| Cursor one MCP entry | PASS (`agentcore-gateway`) |
| Cursor one foundation rule | PASS |
| Memory lifecycle | PASS (entry gate) |
| Projections current | PASS |
| LangGraph topology `a86e40e8…` | PASS |

---

## Rollback

1. Registry already has Firebase/Sheets `enabled=false` — no live clients to remove if current render is kept.
2. If accidentally re-enabled: set `enabled=false`, clear `capability_profiles`, re-render, restart Bifrost task.
3. Do not reintroduce User-scope `FIREBASE_PROJECT_ID` or `GOOGLE_SHEETS_ACCESS_TOKEN`.
