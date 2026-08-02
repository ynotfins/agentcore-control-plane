BEGIN;

CREATE TABLE IF NOT EXISTS agentcore.device_keys (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id          uuid NOT NULL REFERENCES agentcore.machines(id) ON DELETE RESTRICT,
    user_id             uuid NOT NULL REFERENCES agentcore.users(id) ON DELETE RESTRICT,
    key_id              text NOT NULL UNIQUE,
    algorithm           text NOT NULL CHECK (algorithm = 'Ed25519'),
    public_key          bytea NOT NULL CHECK (octet_length(public_key) = 32),
    status              text NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'rotating', 'revoked', 'disabled')),
    valid_from          timestamptz NOT NULL DEFAULT now(),
    valid_until         timestamptz,
    revoked_at          timestamptz,
    rotated_from_key_id text REFERENCES agentcore.device_keys(key_id) ON DELETE RESTRICT,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    CHECK (valid_until IS NULL OR valid_until > valid_from),
    CHECK ((status = 'revoked') = (revoked_at IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_device_keys_machine_user_status
    ON agentcore.device_keys (machine_id, user_id, status);

CREATE TABLE IF NOT EXISTS agentcore.device_assertion_nonces (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    device_key_id   uuid NOT NULL REFERENCES agentcore.device_keys(id) ON DELETE RESTRICT,
    nonce_sha256    bytea NOT NULL CHECK (octet_length(nonce_sha256) = 32),
    target_tool     text NOT NULL,
    request_sha256  bytea NOT NULL CHECK (octet_length(request_sha256) = 32),
    issued_at       timestamptz NOT NULL,
    expires_at      timestamptz NOT NULL,
    consumed_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (device_key_id, nonce_sha256),
    CHECK (expires_at > issued_at)
);

CREATE INDEX IF NOT EXISTS idx_device_assertion_nonces_expiry
    ON agentcore.device_assertion_nonces (expires_at);

CREATE TABLE IF NOT EXISTS agentcore.device_identity_policy (
    singleton                   boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    schema_version              integer NOT NULL DEFAULT 1 CHECK (schema_version = 1),
    enforcement_mode            text NOT NULL DEFAULT 'legacy_compat'
                                CHECK (enforcement_mode IN ('legacy_compat', 'required')),
    migration_window_ends_at    timestamptz NOT NULL DEFAULT (now() + interval '7 days'),
    legacy_machine_id           uuid REFERENCES agentcore.machines(id) ON DELETE RESTRICT,
    legacy_user_id              uuid REFERENCES agentcore.users(id) ON DELETE RESTRICT,
    updated_at                  timestamptz NOT NULL DEFAULT now()
);

INSERT INTO agentcore.device_identity_policy (singleton)
VALUES (true)
ON CONFLICT (singleton) DO NOTHING;

CREATE TABLE IF NOT EXISTS agentcore.device_identity_audit (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    action          text NOT NULL CHECK (
                        action IN (
                            'enrolled', 'rotated', 'revoked', 'disabled',
                            'enabled', 'legacy_default_set', 'enforcement_changed'
                        )
                    ),
    device_key_id   uuid REFERENCES agentcore.device_keys(id) ON DELETE RESTRICT,
    machine_id      uuid REFERENCES agentcore.machines(id) ON DELETE RESTRICT,
    user_id         uuid REFERENCES agentcore.users(id) ON DELETE RESTRICT,
    detail          jsonb NOT NULL DEFAULT '{}'::jsonb,
    occurred_at     timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE agentcore.device_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE agentcore.device_assertion_nonces ENABLE ROW LEVEL SECURITY;
ALTER TABLE agentcore.device_identity_policy ENABLE ROW LEVEL SECURITY;
ALTER TABLE agentcore.device_identity_audit ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON agentcore.device_keys FROM PUBLIC;
REVOKE ALL ON agentcore.device_assertion_nonces FROM PUBLIC;
REVOKE ALL ON agentcore.device_identity_policy FROM PUBLIC;
REVOKE ALL ON agentcore.device_identity_audit FROM PUBLIC;

INSERT INTO agentcore.schema_migrations (version, description)
VALUES ('m2.002', 'Cryptographically enrolled device identity and replay prevention')
ON CONFLICT (version) DO NOTHING;

COMMIT;
