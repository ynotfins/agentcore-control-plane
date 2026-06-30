-- 0005_seed_source_systems.sql
-- Seed the 8 known backend stores into memory_source_systems (database-plan.md sec 7).
-- Idempotent via ON CONFLICT (slug). Additive only. Target DB: agent_core @ 127.0.0.1:55432.
-- No credentials are stored here -- endpoint_uri is host/path only.

INSERT INTO memory_source_systems (slug, display_name, endpoint_uri, adapter_notes, is_active, is_deferred) VALUES
  ('postgres',       'AgentCore PostgreSQL',  '127.0.0.1:55432/agent_core',          'Canonical agent_core DB; adapter uses agent_read role',                       true,  false),
  ('swarmrecall',    'SwarmRecall Local API', 'http://127.0.0.1:3300',               'swarmrecall DB + Meilisearch; accessed via API/MCP, never direct SQL',        true,  false),
  ('swarmvault',     'SwarmVault Local',      'F:\AgentCore\agentmemory\swarmvault', 'File-based; accessed via SwarmVault MCP or CLI',                              true,  false),
  ('obsidian',       'Obsidian Vault REST',   'https://127.0.0.1:27124',             'OBSIDIAN_API_KEY env var; single-writer REST',                                true,  false),
  ('context-fabric', 'Context Fabric',        'repo-local .context-fabric/',          'Repo continuity; accessed via context-fabric MCP',                            true,  false),
  ('git',            'Git Source',            'repo-local',                          'Current source state; read via filesystem or context-fabric',                 true,  false),
  ('manual',         'Operator-Authored',     NULL,                                   'Human-written facts ingested through agentcore_store_project_fact',           true,  false),
  ('lcm',            'LCM / Lossless Memory', NULL,                                   'DEFERRED -- no live service; schema reserves the slug',                       false, true)
ON CONFLICT (slug) DO UPDATE SET
  display_name  = EXCLUDED.display_name,
  endpoint_uri  = EXCLUDED.endpoint_uri,
  adapter_notes = EXCLUDED.adapter_notes,
  is_active     = EXCLUDED.is_active,
  is_deferred   = EXCLUDED.is_deferred,
  updated_at    = now();
