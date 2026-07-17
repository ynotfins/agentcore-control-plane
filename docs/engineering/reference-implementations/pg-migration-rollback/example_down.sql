-- Reference implementation — PostgreSQL migration (DOWN)
-- Rollback for example_up.sql

BEGIN;

DROP TABLE IF EXISTS agentcore.example_items CASCADE;
DROP TYPE IF EXISTS agentcore.example_status;
DELETE FROM agentcore.schema_migrations WHERE version = 'ref.example.001';

COMMIT;
