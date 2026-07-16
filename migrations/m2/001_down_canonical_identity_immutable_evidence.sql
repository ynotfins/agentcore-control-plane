-- M2 001 DOWN — Canonical Identity and Immutable Evidence
--
-- Drops the M2 schema and all M2 primitives. Intended for rollback testing before
-- M2 completion and for explicit operator-approved rollback only.

BEGIN;

DROP SCHEMA IF EXISTS agentcore CASCADE;

COMMIT;
