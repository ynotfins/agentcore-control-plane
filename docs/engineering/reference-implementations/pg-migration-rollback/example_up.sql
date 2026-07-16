-- Reference implementation — PostgreSQL migration (UP)
-- Teaches: idempotent, versioned, project-isolated schema change.
-- See recipe: docs/engineering/recipes/01-pg-migration-rollback.md

BEGIN;

CREATE SCHEMA IF NOT EXISTS agentcore;

-- Idempotent enum creation
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace='agentcore'::regnamespace AND typname='example_status') THEN
    CREATE TYPE agentcore.example_status AS ENUM ('pending', 'active', 'done');
  END IF;
END $$;

-- Idempotent table creation with project isolation
CREATE TABLE IF NOT EXISTS agentcore.example_items (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    label       text NOT NULL,
    status      agentcore.example_status NOT NULL DEFAULT 'pending',
    metadata    jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_example_items_project ON agentcore.example_items(project_id);
CREATE INDEX IF NOT EXISTS idx_example_items_status  ON agentcore.example_items(project_id, status);

-- Minimal grants
GRANT SELECT ON agentcore.example_items TO agentcore_read, agentcore_ingest, agentcore_worker, agentcore_backup;
GRANT INSERT, UPDATE ON agentcore.example_items TO agentcore_worker, agentcore_admin;
GRANT ALL ON agentcore.example_items TO agentcore_admin;

-- Evidence record (idempotent)
INSERT INTO agentcore.schema_migrations (version, description, blueprint_level)
VALUES ('ref.example.001', 'reference migration example — example_items', 'Reference')
ON CONFLICT (version) DO NOTHING;

COMMIT;
