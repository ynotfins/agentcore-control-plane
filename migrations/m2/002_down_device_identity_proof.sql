BEGIN;

DELETE FROM agentcore.schema_migrations WHERE version = 'm2.002';

DROP TABLE IF EXISTS agentcore.device_identity_audit;
DROP TABLE IF EXISTS agentcore.device_identity_policy;
DROP TABLE IF EXISTS agentcore.device_assertion_nonces;
DROP TABLE IF EXISTS agentcore.device_keys;

COMMIT;
