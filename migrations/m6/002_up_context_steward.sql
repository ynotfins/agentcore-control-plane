-- Context Steward findings / proposals (Phase 7B)
-- Bounded monitoring worker; never owns canonical memory authority.

CREATE TABLE IF NOT EXISTS agentcore.context_steward_findings (
  finding_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id text NOT NULL,
  check_type text NOT NULL,
  severity text NOT NULL CHECK (severity IN ('info','warn','critical')),
  summary text NOT NULL,
  detail jsonb NOT NULL DEFAULT '{}'::jsonb,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz NULL
);

CREATE INDEX IF NOT EXISTS idx_context_steward_findings_project_created
  ON agentcore.context_steward_findings (project_id, created_at DESC);

CREATE TABLE IF NOT EXISTS agentcore.context_steward_proposals (
  proposal_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id text NOT NULL,
  finding_id uuid NULL REFERENCES agentcore.context_steward_findings(finding_id),
  proposal_kind text NOT NULL,
  proposal jsonb NOT NULL,
  status text NOT NULL DEFAULT 'proposed'
    CHECK (status IN ('proposed','accepted','rejected','superseded')),
  created_at timestamptz NOT NULL DEFAULT now(),
  decided_at timestamptz NULL,
  decision_note text NULL
);

CREATE INDEX IF NOT EXISTS idx_context_steward_proposals_project_status
  ON agentcore.context_steward_proposals (project_id, status, created_at DESC);

COMMENT ON TABLE agentcore.context_steward_findings IS
  'Phase 7 Context Steward findings; proposals only — never auto-edit BLUEPRINT/STATE authority.';
COMMENT ON TABLE agentcore.context_steward_proposals IS
  'Phase 7 Context Steward proposals requiring operator/agent acceptance.';
