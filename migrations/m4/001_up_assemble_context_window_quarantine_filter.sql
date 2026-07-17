-- M4 migration: exclude quarantined and rejected events from context window assembly.
-- The locked M4 acceptance criterion requires that startup_context exclude quarantined
-- evidence. This replaces the function with an identical body plus the trust_class filter.
-- Rollback: migrations/m4/001_down_assemble_context_window_quarantine_filter.sql

CREATE OR REPLACE FUNCTION agentcore.assemble_context_window(p_project_id uuid, p_budget_name text)
RETURNS TABLE(
    item_type       text,
    item_id         uuid,
    level           agentcore.context_level,
    bucket          agentcore.context_bucket,
    body            text,
    token_count     integer,
    importance      numeric,
    cumulative_tokens bigint
)
LANGUAGE sql
STABLE
AS $function$
WITH budget AS (
    SELECT max_tokens FROM agentcore.model_context_budgets WHERE budget_name = p_budget_name
),
items AS (
    SELECT
        'summary'::text AS item_type,
        id AS item_id,
        level,
        bucket,
        summary_text AS body,
        token_count,
        importance,
        created_at
    FROM agentcore.context_summaries
    WHERE project_id = p_project_id
    UNION ALL
    SELECT
        'raw_event'::text,
        id,
        'L0'::agentcore.context_level,
        'active_dynamic'::agentcore.context_bucket,
        payload::text,
        greatest(1, ceil(length(payload::text) / 4.0))::integer,
        1.0::numeric,
        accepted_at
    FROM agentcore.evidence_events
    WHERE project_id = p_project_id
      AND trust_class NOT IN ('quarantined', 'rejected')
    ORDER BY importance DESC, created_at DESC
),
ranked AS (
    SELECT
        *,
        sum(token_count) OVER (
            ORDER BY
              CASE bucket WHEN 'static_stable' THEN 0 ELSE 1 END,
              CASE level WHEN 'L3' THEN 0 WHEN 'L2' THEN 1 WHEN 'L1' THEN 2 ELSE 3 END,
              importance DESC,
              created_at DESC
        ) AS cumulative_tokens
    FROM items
)
SELECT item_type, item_id, level, bucket, body, token_count, importance, cumulative_tokens
FROM ranked, budget
WHERE cumulative_tokens <= budget.max_tokens
ORDER BY cumulative_tokens
$function$;

-- Record migration
INSERT INTO agentcore.schema_migrations (version, description, blueprint_level)
VALUES ('m4.001_quarantine_filter', 'Exclude quarantined/rejected events from assemble_context_window', 'M4')
ON CONFLICT (version) DO NOTHING;
