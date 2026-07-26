# ChatGPT Project Source Manifest — Canonical Source Package

**Authority:** `DOC_AUTHORITY.md` Level 2  
**Updated:** 2026-07-25  
**Script:** `scripts/export_chatgpt_project_sources.py`  
**Canonical Repository:** `D:\github\agentcore-control-plane`

---

## 1. Operating Rules & Upload Constraints

1. **Exactly One Uploaded Copy:** Every source file uploaded to the ChatGPT Project Sources UI must correspond to exactly one canonical absolute path in this manifest.
2. **Upload Artifacts Are Not Authority:** Filename suffixes created by browsers or upload interfaces (e.g., `DOC_AUTHORITY (2).md`, `BLUEPRINT (5).md`, `CONTEXT_BLOCK (8).md`) are non-authoritative upload artifacts. The ChatGPT chat must recognize the base canonical name.
3. **No Same-Title Duplicates:** Same-title duplicate files (e.g. uploading both a historical `CONTEXT_BLOCK` and a current `CONTEXT_BLOCK`) must NOT coexist in the ChatGPT Project source set.
4. **Historical Banners Excluded from Broad Retrieval:** A historical banner on a large stale document does not make it suitable for broad ChatGPT retrieval. Historical and superseded documents belong in `EXCLUDE_FROM_PROJECT_SOURCES` and must not be uploaded to the default project sources.
5. **Forbidden Project Sources:** Live screenshots, secret-bearing configuration exports, raw database dumps, and files containing resolved secrets or virtual keys are STRICTLY FORBIDDEN as ChatGPT Project Sources.
6. **Live Claims Verification:** Files marked with `mutable_live_claims_require_verification: true` contain runtime facts (e.g., live provider availability or client status) that require verification via `agentcore-memory` before taking architectural actions.

---

## 2. CORE_ALWAYS_INCLUDE (Default Lean Source Package)

Attach these 13 files to any new ChatGPT project chat for general AgentCore and control-plane work:

| # | Canonical Absolute Path | Authority Level | Status | SHA-256 | Last Verified Date | Supersedes / Superseded-By | Mutable Live Claims Require Verification | Safe for Broad ChatGPT Retrieval |
|---|---|---:|---|---|---|---|---|---|
| 1 | `D:\github\agentcore-control-plane\PROJECT_ANCHOR.md` | 1 | stable | `f0e55d55e824ee8f955a9dc7b28bafa09df8f6045e5705d4ab202795d1619800` | 2026-07-25 | None | false | true |
| 2 | `D:\github\agentcore-control-plane\DOC_AUTHORITY.md` | 2 | stable | `99c4fd0d53c5ee3facf9466a8b8f255af43ccb7a9ef81ba226f31e9dc2e55ed2` | 2026-07-25 | Supersedes 2026-07-20 version | true | true |
| 3 | `D:\github\agentcore-control-plane\BLUEPRINT.md` | 3 | stable | `c2df8fd5f471b65a6c56e89d87c849ce32adc7325596b0cc9737bb6360fb263d` | 2026-07-25 | Locked architecture blueprint | false | true |
| 4 | `D:\github\agentcore-control-plane\CONTEXT_BLOCK.md` | 4 | current | `5e6c29cd8ce43b1e65ea2aec4e5c4f633683cdc926baf8d0e49ea7398f2a4922` | 2026-07-25 | Supersedes 2026-06-30 CONTEXT_BLOCK | true | true |
| 5 | `D:\github\agentcore-control-plane\docs\memory-platform\MEMORY_PLATFORM_EXECUTION_PLAN.md` | 5 | stable | `16bfc3a22619da081de0fc330cec2f8dd5985ff435ef9d27d28a9869a35ea39c` | 2026-07-25 | Derives from BLUEPRINT.md | false | true |
| 6 | `D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json` | 6 | current | `dfe80100377468ed8db4df32675a20d096baac6ec984f72d187efb41f09dc5f4` | 2026-07-25 | Canonical upstream MCP registry | true | true |
| 7 | `D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json` | 6 | stable | `6bf88671d68fb8a55c092f09f8b6f657952c00fb5f982be391a2486713bfda68` | 2026-07-25 | Single IDE gateway client contract | false | true |
| 8 | `D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml` | 7 | stable | `8207ebe55408297866a5d20ddeb6a70b3176a8e68553eaa5236bea8cb796e188` | 2026-07-25 | Source for per-IDE rule profiles | false | true |
| 9 | `D:\github\agentcore-control-plane\contracts\model-context-profiles.json` | 7 | stable | `5b8aae35be2faaad22001881720dfe6bcd75f5ac542629f467199676d5946082` | 2026-07-25 | Model token budget profiles | false | true |
| 10 | `D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md` | 7 | current | `905242678b09474841fccaa6b6bd40e35cba8b1777f23f80d9694461153d5e9c` | 2026-07-25 | Root setup guide & embedded prompt | true | true |
| 11 | `D:\github\agentcore-control-plane\AGENTS.md` | 6 | stable | `b835ef4571cfb7d96457168c44f11c01c1d79901fae25055776dddc369458c8e` | 2026-07-25 | Source-controlled agent operating contract | false | true |
| 12 | `D:\github\agentcore-control-plane\CLAUDE.md` | 6 | stable | `2a1241e710ea22ffc1d8e4c91e5f730aaf67a293779347fcb53df034693658de` | 2026-07-25 | Agent-specific guidelines | false | true |
| 13 | `D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_SWARM_DUAL_ECOSYSTEM_HANDOFF_2026-07-25.md` | 8 | current | `da1e376b21137d494e27ddf66d18eee2c0fa89eb150a5414b0f8b1e96af52878` | 2026-07-25 | Supersedes 2026-07-22 full-chat handoff | true | true |

---

## 3. WORKSTREAM_ONLY (Include Only When Active)

Attach these files ONLY when working on the corresponding specific workstream:

| # | Workstream | Canonical Absolute Path | Authority Level | Status | SHA-256 | Last Verified Date | Supersedes / Superseded-By | Mutable Live Claims Require Verification | Safe for Broad ChatGPT Retrieval |
|---|---|---|---:|---|---|---|---|---|---|
| 1 | Cursor / Hooks | `D:\github\agentcore-control-plane\audits\cursor-context\CURSOR_STAGE_B_INTEGRITY_HARNESS_ACCEPTANCE_2026-07-24.md` | 8 | runbook | `1cde698d270f1e9cf2137562af960739b1a878af0fc2b51642adfa80d5c0ae89` | 2026-07-25 | Cursor Stage B acceptance evidence | true | true |
| 2 | Cursor / Hooks | `D:\github\agentcore-control-plane\audits\cursor-context\CURSOR_NATIVE_SKILL_SURFACE_2026-07-24.md` | 8 | runbook | `1ff81013e807658543e02089b68929f207e67a44a977fee8cce3093625b33c93` | 2026-07-25 | Cursor native skill surface audit | true | true |
| 3 | Cursor / Hooks | `D:\github\agentcore-control-plane\docs\operations\AUTOMATIC_NEW_CHAT_RECOVERY.md` | 8 | runbook | `899b62545900f3fddd232e0f5dff3e8b984813252c96d1b3c28c629d9efce318` | 2026-07-25 | Cursor new-chat recovery runbook | true | true |
| 4 | Bifrost / Tunnel | `D:\github\agentcore-control-plane\audits\bifrost\BIFROST_COMPLETE_CONFIGURATION_ACCEPTANCE_2026-07-24.md` | 8 | runbook | `ba3b1e064005038a49d796ae79f2074b7a102c42efeb1c7be2d7acc54ae95774` | 2026-07-25 | Bifrost acceptance audit | true | true |
| 5 | Bifrost / Tunnel | `D:\github\agentcore-control-plane\docs\bifrost\BIFROST_OPERATOR_RUNBOOK.md` | 8 | runbook | `73201e8b9c8f94f36477e05d9f2de96346dea4d08747965c9738ef00005a96b8` | 2026-07-25 | Bifrost start/stop/restart runbook | true | true |
| 6 | Bifrost / Tunnel | `D:\github\agentcore-control-plane\docs\bifrost\BIFROST_PROVIDER_RUNBOOK.md` | 8 | runbook | `9ea9c4333a41a1bce8442af95737539dcdf639216a772079f44c590874a604a2` | 2026-07-25 | Bifrost provider runbook | true | true |
| 7 | Bifrost / Tunnel | `D:\github\agentcore-control-plane\docs\bifrost\CHATGPT_SECURE_MCP_TUNNEL.md` | 8 | runbook | `a9e2de948a8981f862b28ac7594d10b69fd6a9eb978e94986554d7937872258c` | 2026-07-25 | ChatGPT tunnel & compat proxy runbook | true | true |
| 8 | Bifrost / Tunnel | `D:\github\agentcore-control-plane\docs\bifrost\MCP_CLASSIFICATION_MATRIX.md` | 8 | runbook | `117225721b7c2bedc57ae39d03af57553f00b013e44568122612589e73f28ff3` | 2026-07-25 | Bifrost MCP classification matrix | true | true |
| 9 | Bifrost / Tunnel | `D:\github\agentcore-control-plane\docs\bifrost\UNIFIED_GATEWAY_SETUP.md` | 8 | runbook | `0d461035aac27dee1ff59c9f29efea6f72bd42eee1419795f469e8d8d65d423c` | 2026-07-25 | Unified IDE gateway setup runbook | true | true |
| 10 | Bifrost / Tunnel | `D:\github\agentcore-control-plane\docs\bifrost\CAPABILITY_PROFILES.md` | 8 | runbook | `7d04b0da24a88ab6cebe4f3d6214f661924d1a73d5b15e812d7e49a1e5b4980a` | 2026-07-25 | Bifrost capability profiles runbook | true | true |
| 11 | Workflow | `D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_AND_STUDIO.md` | 8 | runbook | `e7c736fa9516a1eb39345449f1fa679d551e0efdb7b61b91825def22e2992a48` | 2026-07-25 | LangGraph M6 production & Studio runbook | true | true |
| 12 | Workflow | `D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_QUICKSTART.md` | 8 | runbook | `ed1a62ab46464224b2adcff83b8f39a206b416071e568fa0792aaad875ef4b78` | 2026-07-25 | LangGraph workflow CLI quickstart | true | true |
| 13 | OpenRouter | `D:\github\agentcore-control-plane\docs\operations\OPENROUTER_MCP.md` | 8 | runbook | `6ed17b91c5727aa291695cefc0d0d262f50ce5dd74d62b33fc6c89759f6e36c7` | 2026-07-25 | OpenRouter MCP runbook | true | true |
| 14 | Dormant Catalog | `D:\github\agentcore-control-plane\docs\operations\DORMANT_MCP_CAPABILITY_CATALOG.md` | 8 | runbook | `a246962815155837ee3a80aeb91bb773a146cf8d44931cc53099a68e2bddfbc3` | 2026-07-25 | Dormant MCP capability catalog | true | true |
| 15 | Cherry Studio | `D:\github\agentcore-control-plane\docs\operations\CHERRY_STUDIO_AGENTCORE.md` | 8 | runbook | `54fa41295179b32d6623d02cc624c677d4aa1ceb074228845defa79c6de190c9` | 2026-07-25 | Cherry Studio AgentCore runbook | true | true |
| 16 | Cherry Studio | `D:\github\agentcore-control-plane\audits\CHERRY_TARGET_AGENT_REPAIR_2026-07-24.md` | 8 | runbook | `a83cbe73d7ac4a541f7e2ae0f0ca0b8e367caaad406c213cf1b996ffdcd91b74` | 2026-07-25 | Cherry Studio target agent repair evidence | true | true |
| 17 | Reconstruction | `D:\github\agentcore-control-plane\docs\current\CURRENT_PROJECT_RECONSTRUCTION.md` | 8 | task-specific | `230d0dc731fd89192da37b1c302186c0d193dd9f20c84bd8518a68282ec88b02` | 2026-07-25 | Long-form evidence synthesis | true | true |

---

## 4. EXCLUDE_FROM_PROJECT_SOURCES (Excluded / Historical / Task-Specific)

DO NOT upload these files to default ChatGPT Project Sources (retrieved via `agentcore-memory` when required):

| # | Canonical Absolute Path | Authority Level | Status | SHA-256 | Last Verified Date | Supersedes / Superseded-By | Mutable Live Claims Require Verification | Safe for Broad ChatGPT Retrieval |
|---|---|---:|---|---|---|---|---|---|
| 1 | `D:\github\agentcore-control-plane\ECOSYSTEM_ARCHITECTURE.md` | 99 | historical | `41aa867db041fc9bc584e2b2547fdae63ac9da95bbe46dee495d2ab865c09467` | 2026-07-25 | Pre-2026-06-30 ecosystem architecture | false | false |
| 2 | `D:\github\agentcore-control-plane\VALIDATION_REPORT.md` | 99 | historical | `d83fe233825ee9c3f8ebdda810a343a73a228877eb6424485b7d4aef325ad6c5` | 2026-07-25 | Historical 2026-06-24 validation report | false | false |
| 3 | `D:\github\agentcore-control-plane\CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md` | 99 | historical | `4e0fa4398b20dc3e056427cc4791f00dbaa91e0ab0d6c3d9969adcd858750878` | 2026-07-25 | Frozen Swarm rollout status | false | false |
| 4 | `D:\github\agentcore-control-plane\docs\MCP_SERVER_CONFIGURATION_REFERENCE.md` | 99 | historical | `6f76f2adb514e7b97b411af6ac6e6d7105792b97a29a11633bdb68a40193b046` | 2026-07-25 | Superseded pre-Bifrost direct-MCP reference | false | false |
| 5 | `D:\github\agentcore-control-plane\docs\CONTEXT_WINDOW_OPTIMIZATION_POLICY.md` | 99 | historical | `1e5ca9b74ad99721fb8ea18511796d5938c10a8071fe34e590b32116cc98417b` | 2026-07-25 | Superseded pre-Bifrost context policy | false | false |
| 6 | `D:\github\agentcore-control-plane\docs\AGENTCORE_STORAGE_DESIGN.md` | 99 | historical | `7ec174fe9a197eac48db2d6c6cec530a78023e1f529b40b5ff5b03b1364c9e34` | 2026-07-25 | Superseded pre-PG18 storage design | false | false |
| 7 | `D:\github\agentcore-control-plane\docs\SERENA_CONFIGURATION.md` | 99 | historical | `ec84d715a27e3dff808785e920465e7e4ed1588b611ce0d6ed1a6d56a8cf5446` | 2026-07-25 | Superseded pre-Bifrost Serena config | false | false |
| 8 | `D:\github\agentcore-control-plane\docs\CHERRY_NEWAPI_INTEGRATION.md` | 99 | historical | `3ee0364ea3e2882314a6281129e060008b70278d5bc6768381a214acc2526913` | 2026-07-25 | Superseded Cherry/NewAPI integration notes | false | false |
| 9 | `D:\github\agentcore-control-plane\docs\bifrost\BIFROST_CODE_MODE_RUNBOOK.md` | 8 | task-specific | `0db9f09c1aad3b2c25cadab0a18f24bd9069b3fa2b690fdb386ff3d023e00727` | 2026-07-25 | Task-specific Code Mode VFS runbook | true | false |
| 10 | `D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_FULL_CHAT_HANDOFF_2026-07-22.md` | 8 | historical | `72cca398d3afda85fba435ff8ccca10a7bdf4855a2fd37ba80e12ea4dbdf85e1` | 2026-07-25 | Superseded full-chat handoff snapshot | true | false |

---

## 5. Source Export Instructions

To generate a clean export package of the 13 `CORE_ALWAYS_INCLUDE` files:

```powershell
python D:\github\agentcore-control-plane\scripts\export_chatgpt_project_sources.py --export-dir E:\ChatGPT-Project-Sources
```

This copies the 13 approved files into `E:\ChatGPT-Project-Sources` and generates a verified `CHATGPT_CORE_PACKAGE_INDEX.json` without rewriting any canonical source file.
