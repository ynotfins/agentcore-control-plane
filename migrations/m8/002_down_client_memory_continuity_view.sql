-- M8 002 DOWN — Drop Client Memory Continuity View
--
-- Rollback for migrations/m8/002_up_client_memory_continuity_view.sql

BEGIN;

DROP VIEW IF EXISTS agentcore.v_client_memory_continuity;

DELETE FROM agentcore.schema_migrations WHERE version = 'm8.002';

COMMIT;
