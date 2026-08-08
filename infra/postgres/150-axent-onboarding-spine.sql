-- AXENT onboarding + contextual accompaniment (Mandato AXENT — secciones 10-11).
--
-- onboarding_journeys/steps/events/preferences/interventions/outcomes,
-- tenant-scoped with forced RLS, audit-friendly. Interventions are
-- deterministic-rule driven with anti-spam controls (cooldown, caps,
-- dismiss/snooze/mute).

CREATE TABLE IF NOT EXISTS tenant_private.onboarding_journeys (
  journey_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  journey_type text NOT NULL DEFAULT 'COMPANY' CHECK (journey_type IN ('COMPANY', 'FOUNDER', 'OPERATOR')),
  state text NOT NULL DEFAULT 'CREATED' CHECK (state IN (
    'CREATED', 'ORGANISATION_READY', 'PROFILE_READY', 'INTERESTS_READY',
    'CAPABILITIES_READY', 'SOURCES_EXPLAINED', 'FIRST_DISCOVERY',
    'FIRST_EXPLANATION', 'FIRST_QUALIFICATION', 'FIRST_WORKSPACE_LINK',
    'FIRST_PURSUIT', 'FIRST_VALUE', 'ACTIVATED'
  )),
  activated_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, journey_type)
);

-- Tenant-aware unique index for composite FK targets.
CREATE UNIQUE INDEX IF NOT EXISTS onboarding_journeys_tenant_journey_uidx
  ON tenant_private.onboarding_journeys (tenant_id, journey_id);

CREATE TABLE IF NOT EXISTS tenant_private.onboarding_steps (
  step_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  journey_id uuid NOT NULL,
  step_key text NOT NULL,
  state text NOT NULL DEFAULT 'PENDING' CHECK (state IN ('PENDING', 'DONE', 'SKIPPED')),
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, journey_id, step_key),
  FOREIGN KEY (tenant_id, journey_id)
    REFERENCES tenant_private.onboarding_journeys (tenant_id, journey_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tenant_private.onboarding_events (
  event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  journey_id uuid NOT NULL,
  event_type text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, journey_id)
    REFERENCES tenant_private.onboarding_journeys (tenant_id, journey_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tenant_private.onboarding_preferences (
  preference_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  preference_key text NOT NULL,
  value_json jsonb NOT NULL,
  confirmed_by_subject text,
  confirmed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, preference_key)
);

CREATE TABLE IF NOT EXISTS tenant_private.onboarding_interventions (
  intervention_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  recipient_subject text NOT NULL,
  reason text NOT NULL,
  trigger_event text NOT NULL,
  priority text NOT NULL DEFAULT 'NORMAL' CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'CRITICAL')),
  context_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  proposed_action text,
  state text NOT NULL DEFAULT 'PENDING' CHECK (state IN (
    'PENDING', 'SHOWN', 'DISMISSED', 'SNOOZED', 'ACCEPTED', 'EXECUTED', 'MUTED'
  )),
  shown_at timestamptz,
  dismissed_at timestamptz,
  accepted_at timestamptz,
  cooldown_until timestamptz,
  frequency_cap integer NOT NULL DEFAULT 3,
  shown_count integer NOT NULL DEFAULT 0,
  outcome text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, recipient_subject, reason, trigger_event)
);

CREATE TABLE IF NOT EXISTS tenant_private.onboarding_outcomes (
  outcome_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  metric_key text NOT NULL,
  value numeric NOT NULL,
  measured_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, metric_key, measured_at)
);


DO $$
DECLARE
  rel text;
BEGIN
  FOREACH rel IN ARRAY ARRAY[
    'onboarding_journeys', 'onboarding_steps', 'onboarding_events',
    'onboarding_preferences', 'onboarding_interventions', 'onboarding_outcomes'
  ]
  LOOP
    EXECUTE format('ALTER TABLE tenant_private.%I ENABLE ROW LEVEL SECURITY', rel);
    EXECUTE format('ALTER TABLE tenant_private.%I FORCE ROW LEVEL SECURITY', rel);
    EXECUTE format('DROP POLICY IF EXISTS %I ON tenant_private.%I', rel || '_tenant_isolation', rel);
    EXECUTE format(
      'CREATE POLICY %I ON tenant_private.%I '
      'USING (tenant_id = tenant_private.current_tenant_id()) '
      'WITH CHECK (tenant_id = tenant_private.current_tenant_id())',
      rel || '_tenant_isolation', rel
    );
  END LOOP;
END $$;

GRANT SELECT, INSERT, UPDATE, DELETE ON
  tenant_private.onboarding_journeys,
  tenant_private.onboarding_steps,
  tenant_private.onboarding_events,
  tenant_private.onboarding_preferences,
  tenant_private.onboarding_interventions,
  tenant_private.onboarding_outcomes
  TO axignal_worker;
GRANT SELECT ON
  tenant_private.onboarding_journeys,
  tenant_private.onboarding_steps,
  tenant_private.onboarding_events,
  tenant_private.onboarding_preferences,
  tenant_private.onboarding_interventions,
  tenant_private.onboarding_outcomes
  TO axignal_app;
