# Zoo Code Native Max — execution evidence

Date: 2026-10-20
Scope: Maximize Zoo Code native capabilities in Cursor. No AgentCore gateway enrollment.

## Done

- Qdrant Test-ZooCodeQdrant.ps1 overall True at 2026-10-20T13:19:42-04:00; HTTP 200; version 1.19.0
- Qdrant collections were empty before UI indexing bind
- Removed Zoo MCP `agentcore-gateway` (legacy drift)
- Disabled Zoo MCP `claude-context` until native Qdrant index is green
- Removed `zoo-code.autoImportSettingsPath` pointing at Downloads
- Quarantined secret-bearing Downloads export to `C:\Users\ynotf\.agentcore\zoo-code-settings.quarantine-20261020.json` and replaced Downloads stub
- Turned `zoo-code.debug` off on configured profiles; expanded safe git allowlist; ensured deny list
- Set `zoo-code.useAgentRules: true` on configured profiles
- Curated `C:\Users\ynotf\.roo\skills` (Cursor-only skills quarantined under `C:\Users\ynotf\.agentcore\zoo-skills-quarantine-20261020`)
- Removed leftover extension folder `zoocodeorganization.zoo-code-3.91.100649-universal` after confirming `3.91.100651` present
- Kept NFA custom modes (no built-in slug overrides)
- Updated `ide-profiles/zoo-code/IDE_PROFILE.yaml` live facts
- Rollback bundle: `.agentcore/rollback/20261020-132147-zoo-code-native-max/`

## Docs ingest

- Arabold scrape job `6ba2d49c-1c06-44ba-986e-aaa0f6fc3a36` for `zoo-code@3.91.100651` from `https://docs.zoocode.dev` — status **completed** at 2026-10-20T17:28:02Z
- `find_version` best match: `3.91.100651`
- `search_docs` returned real hits for codebase indexing / Qdrant

## Operator follow-up (indexing)

See `INDEXING_OPERATOR_CARD.txt` in the rollback bundle. Zoo UI Save and Start Indexing is required for a green index icon and nonempty Qdrant collections. Computer Use was unavailable in this session.

## Sticky model guidance (Zoo UI)

Built-in modes already exist: Orchestrator, Code, Architect, Debug, Ask.
Assign sticky models in Zoo UI (prefer Zoo Gateway for Zoo inference):
- Orchestrator / Architect: stronger planner
- Code / Debug: implementer
- Ask: cheaper/faster
NFA custom modes remain specialists only.

Generated: 2026-10-20T17:25:33.205630+00:00

## Indexing UI check 2026-10-20 14:54

- Qdrant API key: NOT required for this loopback deployment (left empty / optional).
- Operator UI: OpenRouter embedder, model mistralai/mistral-embed-2312 (1024d), Qdrant http://127.0.0.1:6333, score 0.40, max 50, workspace indexing enabled.
- Live collection ws-237e8b7784b2f9e0: status green, points_count 15901, vector size 1024 Cosine.
- Test-ZooCodeQdrant.ps1 overall True at 2026-10-20T14:54:07-04:00.

## Operator confirmation 2026-10-20 14:57

- Zoo Codebase Indexing status icon reported green by operator.
- Profile status set to indexed_green_openrouter_mistral_embed_2312.
