-- AXIGNAL Opportunity Operations durable spine (Prioridad 2).
-- Tenant-scoped persistence for pursuits, workspaces, outcomes, learnings,
-- manifest states, kill-switch audit, sandbox catalogue/subscriptions,
-- idempotency keys, entitlements, webhook events and cross-library portfolio.
--
-- Follows the C3/C4 conventions: tenant_private tables with forced RLS,
-- SECURITY DEFINER functions for idempotent operations, GRANT EXECUTE to
-- axignal_app/axignal_worker only.

-- ===========================================================================
-- 1. Pursuits
-- ===========================================================================

CREATE TABLE IF NOT EXISTS tenant_private.opportunity_pursuits (
  pursuit_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  pursuit_ref text NOT NULL CHECK (pursuit_ref ~ '^prs_[A-Za-z0-9_-]{8,}$'),
  opportunity_ref text NOT NULL,
  state text NOT NULL CHECK (
    state IN ('QUALIFIED', 'DECISION_REVIEW', 'ACTIVE', 'WON', 'LOST', 'WITHDRAWN')
  ),
  workspace_ref uuid,
  created_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  decided_by text,
  decided_at timestamptz,
  outcome_ref text,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  UNIQUE (tenant_id, pursuit_ref)
);

ALTER TABLE tenant_private.opportunity_pursuits ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.opportunity_pursuits FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS opportunity_pursuits_tenant_isolation
  ON tenant_private.opportunity_pursuits;
CREATE POLICY opportunity_pursuits_tenant_isolation
  ON tenant_private.opportunity_pursuits
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

-- ===========================================================================
-- 2. Workspaces (opportunity operations)
-- ===========================================================================

CREATE TABLE IF NOT EXISTS tenant_private.opportunity_workspaces (
  workspace_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  pursuit_ref text NOT NULL,
  opportunity_ref text NOT NULL,
  opportunity_version_digest text CHECK (opportunity_version_digest ~ '^sha256:[0-9a-f]{64}$'),
  subscriber_profile_version text NOT NULL,
  assessment_version text NOT NULL,
  state text NOT NULL CHECK (
    state IN ('CREATED', 'QUALIFYING', 'GO_REVIEW', 'NO_GO_REVIEW', 'PREPARING',
              'AWAITING_INFORMATION', 'READY_FOR_INTERNAL_REVIEW',
              'READY_FOR_SUBSCRIBER_APPROVAL', 'PRESENTED_EXTERNALLY',
              'APPROVED', 'HANDED_OFF')
  ),
  created_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  presented_externally_confirmed_by text,
  presented_externally_confirmed_at timestamptz
);

ALTER TABLE tenant_private.opportunity_workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.opportunity_workspaces FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS opportunity_workspaces_tenant_isolation
  ON tenant_private.opportunity_workspaces;
CREATE POLICY opportunity_workspaces_tenant_isolation
  ON tenant_private.opportunity_workspaces
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

-- ===========================================================================
-- 3. Outcomes and learnings
-- ===========================================================================

CREATE TABLE IF NOT EXISTS tenant_private.opportunity_outcomes (
  outcome_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  outcome_ref text NOT NULL CHECK (outcome_ref ~ '^out_[A-Za-z0-9_-]{8,}$'),
  pursuit_ref text NOT NULL,
  result text NOT NULL CHECK (result IN ('WON', 'LOST', 'WITHDRAWN')),
  decided_at timestamptz NOT NULL,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  notes text,
  UNIQUE (tenant_id, outcome_ref)
);

ALTER TABLE tenant_private.opportunity_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.opportunity_outcomes FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS opportunity_outcomes_tenant_isolation
  ON tenant_private.opportunity_outcomes;
CREATE POLICY opportunity_outcomes_tenant_isolation
  ON tenant_private.opportunity_outcomes
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE TABLE IF NOT EXISTS tenant_private.opportunity_learnings (
  learning_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  learning_ref text NOT NULL CHECK (learning_ref ~ '^lrn_[A-Za-z0-9_-]{8,}$'),
  outcome_ref text NOT NULL,
  insight text NOT NULL CHECK (char_length(insight) >= 10),
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  derived_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, learning_ref)
);

ALTER TABLE tenant_private.opportunity_learnings ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.opportunity_learnings FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS opportunity_learnings_tenant_isolation
  ON tenant_private.opportunity_learnings;
CREATE POLICY opportunity_learnings_tenant_isolation
  ON tenant_private.opportunity_learnings
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

-- ===========================================================================
-- 4. Manifest states (libraries and sources)
-- ===========================================================================

CREATE TABLE IF NOT EXISTS axignal_global.manifest_states (
  manifest_kind text NOT NULL CHECK (manifest_kind IN ('library', 'source')),
  manifest_id text NOT NULL,
  state text NOT NULL,
  schema_version text NOT NULL DEFAULT '1.0.0',
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (manifest_kind, manifest_id)
);

GRANT SELECT, INSERT, UPDATE ON axignal_global.manifest_states TO axignal_app, axignal_worker;

-- ===========================================================================
-- 5. Kill-switch audit (append-only, tenant-agnostic operational record)
-- ===========================================================================

CREATE TABLE IF NOT EXISTS axignal_global.source_control_events (
  event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id text NOT NULL,
  from_state text NOT NULL,
  to_state text NOT NULL,
  reason text NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  exact_head text
);

GRANT SELECT, INSERT ON axignal_global.source_control_events TO axignal_app, axignal_worker;

-- ===========================================================================
-- 6. Sandbox catalogue, subscriptions and idempotency
-- ===========================================================================

CREATE TABLE IF NOT EXISTS tenant_private.sandbox_products (
  product_id text PRIMARY KEY,
  shell_id text NOT NULL,
  commercial_status text NOT NULL DEFAULT 'ACTIVE_CONTRACT_DEFINITION'
);

CREATE TABLE IF NOT EXISTS tenant_private.sandbox_plans (
  plan_id text PRIMARY KEY,
  product_id text NOT NULL REFERENCES tenant_private.sandbox_products(product_id),
  name text NOT NULL,
  seats int NOT NULL CHECK (seats >= 1),
  status text NOT NULL CHECK (status IN ('DRAFT', 'ACTIVE', 'INACTIVE')),
  is_academy boolean NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS tenant_private.sandbox_prices (
  price_id text PRIMARY KEY,
  product_id text NOT NULL,
  plan_id text NOT NULL REFERENCES tenant_private.sandbox_plans(plan_id),
  amount_cents int NOT NULL CHECK (amount_cents >= 0),
  currency text NOT NULL CHECK (currency IN ('EUR', 'USD', 'GBP')),
  interval_unit text NOT NULL CHECK (interval_unit IN ('month', 'year', 'once')),
  tax_mode text NOT NULL CHECK (tax_mode IN ('INCLUSIVE', 'EXCLUSIVE')),
  version int NOT NULL DEFAULT 1 CHECK (version >= 1),
  active boolean NOT NULL DEFAULT true,
  UNIQUE (plan_id, version)
);

CREATE TABLE IF NOT EXISTS tenant_private.sandbox_subscriptions (
  subscription_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  product_id text NOT NULL,
  plan_id text NOT NULL,
  price_id text NOT NULL,
  status text NOT NULL CHECK (
    status IN ('ACTIVE', 'DUNNING', 'CANCELLED_AT_PERIOD_END', 'CANCELLED_IMMEDIATE', 'TRIAL')
  ),
  trial boolean NOT NULL DEFAULT false,
  grace_until timestamptz,
  renewed_at timestamptz,
  last_change_direction text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE tenant_private.sandbox_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.sandbox_subscriptions FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS sandbox_subscriptions_tenant_isolation
  ON tenant_private.sandbox_subscriptions;
CREATE POLICY sandbox_subscriptions_tenant_isolation
  ON tenant_private.sandbox_subscriptions
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE TABLE IF NOT EXISTS tenant_private.billing_idempotency_keys (
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  idempotency_key text NOT NULL,
  checkout_id text NOT NULL,
  product_id text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, idempotency_key)
);

ALTER TABLE tenant_private.billing_idempotency_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.billing_idempotency_keys FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS billing_idempotency_keys_tenant_isolation
  ON tenant_private.billing_idempotency_keys;
CREATE POLICY billing_idempotency_keys_tenant_isolation
  ON tenant_private.billing_idempotency_keys
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE TABLE IF NOT EXISTS tenant_private.billing_entitlements (
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  product_id text NOT NULL,
  allowed boolean NOT NULL DEFAULT false,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, product_id)
);

ALTER TABLE tenant_private.billing_entitlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.billing_entitlements FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS billing_entitlements_tenant_isolation
  ON tenant_private.billing_entitlements;
CREATE POLICY billing_entitlements_tenant_isolation
  ON tenant_private.billing_entitlements
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE TABLE IF NOT EXISTS tenant_private.billing_webhook_events (
  webhook_event_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  product_id text NOT NULL,
  event_type text NOT NULL,
  payload jsonb NOT NULL,
  signature text NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  processed boolean NOT NULL DEFAULT false
);

ALTER TABLE tenant_private.billing_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.billing_webhook_events FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS billing_webhook_events_tenant_isolation
  ON tenant_private.billing_webhook_events;
CREATE POLICY billing_webhook_events_tenant_isolation
  ON tenant_private.billing_webhook_events
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

-- ===========================================================================
-- 7. Portfolio and cross-library relations
-- ===========================================================================

CREATE TABLE IF NOT EXISTS tenant_private.opportunity_portfolio (
  item_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  item_ref text NOT NULL CHECK (item_ref ~ '^pf_[A-Za-z0-9_-]{8,}$'),
  opportunity_ref text NOT NULL,
  library_id text NOT NULL CHECK (library_id ~ '^O0[1-9]$'),
  added_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, item_ref)
);

ALTER TABLE tenant_private.opportunity_portfolio ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.opportunity_portfolio FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS opportunity_portfolio_tenant_isolation
  ON tenant_private.opportunity_portfolio;
CREATE POLICY opportunity_portfolio_tenant_isolation
  ON tenant_private.opportunity_portfolio
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE TABLE IF NOT EXISTS axignal_global.cross_library_relations (
  relation_id uuid PRIMARY KEY,
  from_ref text NOT NULL,
  to_ref text NOT NULL,
  relation text NOT NULL,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (from_ref, to_ref, relation)
);

GRANT SELECT, INSERT ON axignal_global.cross_library_relations TO axignal_app, axignal_worker;

-- ===========================================================================
-- GRANTS for tenant_private tables (functions pattern not required for
-- repository-driven access; direct DML is scoped by RLS + role membership)
-- ===========================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA tenant_private TO axignal_app, axignal_worker;
