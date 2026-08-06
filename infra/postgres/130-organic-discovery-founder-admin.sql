-- AX-GE2E-P26-T01 organic discovery, programmatic SEO and founder administration.
-- Generated candidates are not indexable until a deterministic gate admits them.

CREATE SCHEMA IF NOT EXISTS growth_private;
REVOKE ALL ON SCHEMA growth_private FROM PUBLIC;

CREATE TABLE IF NOT EXISTS growth_private.founder_admin_principals (
  subject text PRIMARY KEY,
  status text NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'SUSPENDED', 'REVOKED')),
  provisioned_by text NOT NULL,
  provisioned_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz
);

CREATE TABLE IF NOT EXISTS growth_private.seo_page_candidates (
  page_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  page_kind text NOT NULL CHECK (page_kind IN ('TENDER_HUB', 'MARKET_INTELLIGENCE', 'TENDER_DETAIL')),
  locale text NOT NULL CHECK (locale ~ '^[a-z]{2}(-[A-Z]{2})?$'),
  country_code text NOT NULL CHECK (country_code ~ '^[A-Z]{2}$'),
  country_slug text NOT NULL CHECK (country_slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
  sector_slug text NOT NULL CHECK (sector_slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
  canonical_path text NOT NULL UNIQUE CHECK (canonical_path LIKE '/%'),
  title text NOT NULL,
  description text NOT NULL,
  state text NOT NULL DEFAULT 'CANDIDATE' CHECK (
    state IN ('DISCOVERED', 'CANDIDATE', 'INDEXABLE', 'PUBLISHED', 'DECAYING', 'ARCHIVED', 'NOINDEX', 'GONE')
  ),
  active_opportunity_count integer NOT NULL DEFAULT 0 CHECK (active_opportunity_count >= 0),
  unique_buyer_count integer NOT NULL DEFAULT 0 CHECK (unique_buyer_count >= 0),
  known_value_microunits bigint NOT NULL DEFAULT 0 CHECK (known_value_microunits >= 0),
  demand_score numeric(5,4) NOT NULL DEFAULT 0 CHECK (demand_score BETWEEN 0 AND 1),
  data_quality_score numeric(5,4) NOT NULL DEFAULT 0 CHECK (data_quality_score BETWEEN 0 AND 1),
  uniqueness_score numeric(5,4) NOT NULL DEFAULT 0 CHECK (uniqueness_score BETWEEN 0 AND 1),
  source_coverage_score numeric(5,4) NOT NULL DEFAULT 0 CHECK (source_coverage_score BETWEEN 0 AND 1),
  content_depth_score numeric(5,4) NOT NULL DEFAULT 0 CHECK (content_depth_score BETWEEN 0 AND 1),
  freshness_at timestamptz NOT NULL,
  source_count integer NOT NULL DEFAULT 0 CHECK (source_count >= 0),
  methodology_version text NOT NULL DEFAULT 'public-intelligence-snapshot@1.0.0',
  is_synthetic boolean NOT NULL DEFAULT false,
  metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
  source_urls jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (page_kind, locale, country_code, sector_slug)
);

CREATE INDEX IF NOT EXISTS seo_page_candidates_state_idx
  ON growth_private.seo_page_candidates (state, freshness_at DESC);
CREATE INDEX IF NOT EXISTS seo_page_candidates_market_idx
  ON growth_private.seo_page_candidates (country_code, sector_slug, locale);

CREATE TABLE IF NOT EXISTS growth_private.seo_indexability_decisions (
  decision_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  page_id uuid NOT NULL REFERENCES growth_private.seo_page_candidates(page_id),
  policy_version text NOT NULL,
  decision text NOT NULL CHECK (decision IN ('INDEX', 'NOINDEX', 'HOLD', 'ARCHIVE', 'GONE')),
  reason_codes text[] NOT NULL DEFAULT '{}',
  score numeric(5,4) NOT NULL CHECK (score BETWEEN 0 AND 1),
  actor_subject text NOT NULL,
  evaluated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS seo_indexability_decisions_page_idx
  ON growth_private.seo_indexability_decisions (page_id, evaluated_at DESC);

CREATE TABLE IF NOT EXISTS growth_private.seo_page_snapshots (
  snapshot_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  page_id uuid NOT NULL REFERENCES growth_private.seo_page_candidates(page_id),
  snapshot_version integer NOT NULL CHECK (snapshot_version > 0),
  content_hash text NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
  methodology_version text NOT NULL,
  source_count integer NOT NULL CHECK (source_count >= 0),
  metrics jsonb NOT NULL,
  source_urls jsonb NOT NULL,
  status text NOT NULL DEFAULT 'PUBLISHED' CHECK (status IN ('PUBLISHED', 'SUPERSEDED', 'REVOKED')),
  published_by text NOT NULL,
  published_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  UNIQUE (page_id, snapshot_version),
  CHECK (expires_at > published_at)
);

CREATE UNIQUE INDEX IF NOT EXISTS seo_one_live_snapshot_idx
  ON growth_private.seo_page_snapshots (page_id)
  WHERE status = 'PUBLISHED';

CREATE TABLE IF NOT EXISTS growth_private.seo_sitemap_entries (
  canonical_path text PRIMARY KEY,
  page_id uuid NOT NULL UNIQUE REFERENCES growth_private.seo_page_candidates(page_id),
  locale text NOT NULL,
  state text NOT NULL CHECK (state IN ('INCLUDED', 'EXCLUDED')),
  change_frequency text NOT NULL CHECK (change_frequency IN ('hourly', 'daily', 'weekly', 'monthly')),
  priority numeric(2,1) NOT NULL CHECK (priority BETWEEN 0 AND 1),
  last_modified_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS growth_private.ai_citation_events (
  citation_event_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  provider text NOT NULL CHECK (provider IN ('CHATGPT', 'COPILOT', 'GOOGLE_AI', 'PERPLEXITY', 'OTHER')),
  surface text NOT NULL,
  cited_url text NOT NULL CHECK (cited_url LIKE 'http%'),
  query_hmac text NOT NULL CHECK (query_hmac ~ '^[0-9a-f]{64}$'),
  source text NOT NULL CHECK (source IN ('BING_WEBMASTER', 'ANALYTICS', 'MANUAL', 'API')),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  observed_at timestamptz NOT NULL,
  recorded_by text NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ai_citation_events_observed_idx
  ON growth_private.ai_citation_events (observed_at DESC, provider);

CREATE TABLE IF NOT EXISTS growth_private.crm_contacts (
  contact_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  email_normalized text NOT NULL UNIQUE CHECK (
    email_normalized = lower(btrim(email_normalized)) AND position('@' IN email_normalized) > 1
  ),
  email_hmac text NOT NULL UNIQUE CHECK (email_hmac ~ '^[0-9a-f]{64}$'),
  company_name text,
  source text NOT NULL,
  lifecycle_stage text NOT NULL DEFAULT 'LEAD' CHECK (
    lifecycle_stage IN ('LEAD', 'MQL', 'SQL', 'TRIAL', 'CUSTOMER', 'CHURNED', 'SUPPRESSED')
  ),
  lead_score integer NOT NULL DEFAULT 0 CHECK (lead_score BETWEEN 0 AND 100),
  owner_subject text,
  consent_status text NOT NULL DEFAULT 'PENDING' CHECK (
    consent_status IN ('PENDING', 'OPTED_IN', 'OPTED_OUT', 'SUPPRESSED')
  ),
  first_touch_path text,
  last_touch_path text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS growth_private.tender_alert_subscriptions (
  subscription_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  contact_id uuid NOT NULL REFERENCES growth_private.crm_contacts(contact_id),
  country_code text NOT NULL CHECK (country_code ~ '^[A-Z]{2}$'),
  sector_slug text NOT NULL CHECK (sector_slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
  locale text NOT NULL,
  cadence text NOT NULL DEFAULT 'DAILY' CHECK (cadence IN ('IMMEDIATE', 'DAILY', 'WEEKLY')),
  state text NOT NULL DEFAULT 'PENDING_CONFIRMATION' CHECK (
    state IN ('PENDING_CONFIRMATION', 'ACTIVE', 'PAUSED', 'UNSUBSCRIBED', 'SUPPRESSED')
  ),
  confirmation_token_digest text NOT NULL UNIQUE CHECK (confirmation_token_digest ~ '^[0-9a-f]{64}$'),
  source_path text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  confirmed_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (contact_id, country_code, sector_slug, cadence)
);

CREATE TABLE IF NOT EXISTS growth_private.crm_activities (
  activity_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  contact_id uuid NOT NULL REFERENCES growth_private.crm_contacts(contact_id),
  activity_type text NOT NULL,
  actor_subject text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS growth_private.founder_admin_audit_events (
  audit_event_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  event_type text NOT NULL,
  actor_subject text NOT NULL,
  target_type text NOT NULL,
  target_id text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS growth_private.growth_settings (
  setting_key text PRIMARY KEY,
  setting_value jsonb NOT NULL,
  updated_by text NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION growth_private.prevent_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'append_only_relation';
END;
$$;

DROP TRIGGER IF EXISTS seo_indexability_append_only ON growth_private.seo_indexability_decisions;
CREATE TRIGGER seo_indexability_append_only
BEFORE UPDATE OR DELETE ON growth_private.seo_indexability_decisions
FOR EACH ROW EXECUTE FUNCTION growth_private.prevent_mutation();

DROP TRIGGER IF EXISTS ai_citation_append_only ON growth_private.ai_citation_events;
CREATE TRIGGER ai_citation_append_only
BEFORE UPDATE OR DELETE ON growth_private.ai_citation_events
FOR EACH ROW EXECUTE FUNCTION growth_private.prevent_mutation();

DROP TRIGGER IF EXISTS founder_admin_audit_append_only ON growth_private.founder_admin_audit_events;
CREATE TRIGGER founder_admin_audit_append_only
BEFORE UPDATE OR DELETE ON growth_private.founder_admin_audit_events
FOR EACH ROW EXECUTE FUNCTION growth_private.prevent_mutation();

CREATE OR REPLACE FUNCTION growth_private.assert_founder_admin(p_subject text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, growth_private
AS $$
BEGIN
  IF p_subject IS NULL OR NOT EXISTS (
    SELECT 1 FROM growth_private.founder_admin_principals
    WHERE subject = p_subject AND status = 'ACTIVE'
  ) THEN
    RAISE EXCEPTION 'founder_admin_required';
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION growth_private.evaluate_indexability(
  p_page_id uuid,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, growth_private
AS $$
DECLARE
  v_page growth_private.seo_page_candidates%ROWTYPE;
  v_reasons text[] := '{}';
  v_decision text := 'INDEX';
  v_score numeric(5,4);
  v_min_opportunities integer;
  v_min_buyers integer;
BEGIN
  PERFORM growth_private.assert_founder_admin(p_actor_subject);
  SELECT * INTO v_page FROM growth_private.seo_page_candidates WHERE page_id = p_page_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'seo_page_not_found'; END IF;

  v_min_opportunities := CASE v_page.page_kind
    WHEN 'TENDER_HUB' THEN 8 WHEN 'MARKET_INTELLIGENCE' THEN 12 ELSE 1 END;
  v_min_buyers := CASE v_page.page_kind
    WHEN 'TENDER_HUB' THEN 3 WHEN 'MARKET_INTELLIGENCE' THEN 5 ELSE 1 END;

  IF v_page.is_synthetic THEN v_reasons := array_append(v_reasons, 'SYNTHETIC_DATA'); END IF;
  IF v_page.active_opportunity_count < v_min_opportunities THEN v_reasons := array_append(v_reasons, 'INSUFFICIENT_INVENTORY'); END IF;
  IF v_page.unique_buyer_count < v_min_buyers THEN v_reasons := array_append(v_reasons, 'INSUFFICIENT_BUYER_DIVERSITY'); END IF;
  IF v_page.demand_score < 0.55 THEN v_reasons := array_append(v_reasons, 'LOW_DEMAND'); END IF;
  IF v_page.data_quality_score < 0.75 THEN v_reasons := array_append(v_reasons, 'LOW_DATA_QUALITY'); END IF;
  IF v_page.uniqueness_score < 0.65 THEN v_reasons := array_append(v_reasons, 'LOW_UNIQUENESS'); END IF;
  IF v_page.source_coverage_score < 0.70 THEN v_reasons := array_append(v_reasons, 'LOW_SOURCE_COVERAGE'); END IF;
  IF v_page.content_depth_score < 0.70 THEN v_reasons := array_append(v_reasons, 'LOW_CONTENT_DEPTH'); END IF;
  IF v_page.freshness_at < p_now - interval '48 hours' THEN v_reasons := array_append(v_reasons, 'STALE_DATA'); END IF;

  v_score := round((
    v_page.demand_score + v_page.data_quality_score + v_page.uniqueness_score +
    v_page.source_coverage_score + v_page.content_depth_score
  ) / 5.0, 4);

  IF array_length(v_reasons, 1) IS NOT NULL THEN
    v_decision := CASE
      WHEN 'SYNTHETIC_DATA' = ANY(v_reasons) THEN 'NOINDEX'
      WHEN 'STALE_DATA' = ANY(v_reasons) THEN 'HOLD'
      ELSE 'NOINDEX'
    END;
  END IF;

  INSERT INTO growth_private.seo_indexability_decisions (
    page_id, policy_version, decision, reason_codes, score, actor_subject, evaluated_at
  ) VALUES (
    p_page_id, 'indexability-gate@1.0.0', v_decision, v_reasons, v_score, p_actor_subject, p_now
  );

  UPDATE growth_private.seo_page_candidates
  SET state = CASE v_decision WHEN 'INDEX' THEN 'INDEXABLE' WHEN 'HOLD' THEN 'CANDIDATE' ELSE 'NOINDEX' END,
      updated_at = p_now
  WHERE page_id = p_page_id;

  INSERT INTO growth_private.seo_sitemap_entries (
    canonical_path, page_id, locale, state, change_frequency, priority, last_modified_at, updated_at
  ) VALUES (
    v_page.canonical_path, p_page_id, v_page.locale,
    CASE WHEN v_decision = 'INDEX' THEN 'INCLUDED' ELSE 'EXCLUDED' END,
    CASE WHEN v_page.page_kind = 'TENDER_DETAIL' THEN 'daily' ELSE 'hourly' END,
    CASE WHEN v_page.page_kind = 'MARKET_INTELLIGENCE' THEN 0.9 ELSE 0.8 END,
    v_page.freshness_at, p_now
  )
  ON CONFLICT (canonical_path) DO UPDATE SET
    state = EXCLUDED.state,
    change_frequency = EXCLUDED.change_frequency,
    priority = EXCLUDED.priority,
    last_modified_at = EXCLUDED.last_modified_at,
    updated_at = EXCLUDED.updated_at;

  INSERT INTO growth_private.founder_admin_audit_events (
    event_type, actor_subject, target_type, target_id, payload, occurred_at
  ) VALUES (
    'SEO_INDEXABILITY_EVALUATED', p_actor_subject, 'SEO_PAGE', p_page_id::text,
    jsonb_build_object('decision', v_decision, 'reason_codes', v_reasons, 'score', v_score), p_now
  );

  RETURN jsonb_build_object(
    'page_id', p_page_id,
    'decision', v_decision,
    'reason_codes', v_reasons,
    'score', v_score,
    'policy_version', 'indexability-gate@1.0.0'
  );
END;
$$;

CREATE OR REPLACE FUNCTION growth_private.publish_page_snapshot(
  p_page_id uuid,
  p_actor_subject text,
  p_content_hash text,
  p_expires_at timestamptz,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, growth_private
AS $$
DECLARE
  v_page growth_private.seo_page_candidates%ROWTYPE;
  v_version integer;
  v_snapshot_id uuid;
BEGIN
  PERFORM growth_private.assert_founder_admin(p_actor_subject);
  SELECT * INTO v_page FROM growth_private.seo_page_candidates WHERE page_id = p_page_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'seo_page_not_found'; END IF;
  IF v_page.state <> 'INDEXABLE' THEN RAISE EXCEPTION 'seo_page_not_indexable'; END IF;
  IF p_content_hash !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'content_hash_invalid'; END IF;
  IF p_expires_at <= p_now THEN RAISE EXCEPTION 'snapshot_expiry_invalid'; END IF;

  UPDATE growth_private.seo_page_snapshots
  SET status = 'SUPERSEDED'
  WHERE page_id = p_page_id AND status = 'PUBLISHED';

  SELECT coalesce(max(snapshot_version), 0) + 1 INTO v_version
  FROM growth_private.seo_page_snapshots WHERE page_id = p_page_id;

  INSERT INTO growth_private.seo_page_snapshots (
    page_id, snapshot_version, content_hash, methodology_version, source_count,
    metrics, source_urls, published_by, published_at, expires_at
  ) VALUES (
    p_page_id, v_version, p_content_hash, v_page.methodology_version, v_page.source_count,
    v_page.metrics, v_page.source_urls, p_actor_subject, p_now, p_expires_at
  ) RETURNING snapshot_id INTO v_snapshot_id;

  UPDATE growth_private.seo_page_candidates
  SET state = 'PUBLISHED', updated_at = p_now WHERE page_id = p_page_id;

  UPDATE growth_private.seo_sitemap_entries
  SET state = 'INCLUDED', last_modified_at = p_now, updated_at = p_now
  WHERE page_id = p_page_id;

  INSERT INTO growth_private.founder_admin_audit_events (
    event_type, actor_subject, target_type, target_id, payload, occurred_at
  ) VALUES (
    'SEO_PAGE_PUBLISHED', p_actor_subject, 'SEO_PAGE', p_page_id::text,
    jsonb_build_object('snapshot_id', v_snapshot_id, 'snapshot_version', v_version), p_now
  );

  RETURN jsonb_build_object(
    'page_id', p_page_id,
    'snapshot_id', v_snapshot_id,
    'snapshot_version', v_version,
    'state', 'PUBLISHED',
    'expires_at', p_expires_at
  );
END;
$$;

CREATE OR REPLACE FUNCTION growth_private.public_discovery_page(
  p_country_slug text,
  p_sector_slug text,
  p_page_kind text,
  p_locale text DEFAULT 'en',
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, public, growth_private
AS $$
  SELECT jsonb_build_object(
    'page_id', p.page_id,
    'page_kind', p.page_kind,
    'locale', p.locale,
    'country_code', p.country_code,
    'country_slug', p.country_slug,
    'sector_slug', p.sector_slug,
    'canonical_path', p.canonical_path,
    'title', p.title,
    'description', p.description,
    'state', p.state,
    'active_opportunity_count', p.active_opportunity_count,
    'unique_buyer_count', p.unique_buyer_count,
    'known_value_microunits', p.known_value_microunits,
    'freshness_at', p.freshness_at,
    'methodology_version', p.methodology_version,
    'source_count', p.source_count,
    'metrics', s.metrics,
    'source_urls', s.source_urls,
    'snapshot_version', s.snapshot_version,
    'published_at', s.published_at,
    'expires_at', s.expires_at
  )
  FROM growth_private.seo_page_candidates p
  JOIN growth_private.seo_page_snapshots s ON s.page_id = p.page_id AND s.status = 'PUBLISHED'
  WHERE p.country_slug = p_country_slug
    AND p.sector_slug = p_sector_slug
    AND p.page_kind = p_page_kind
    AND p.locale = p_locale
    AND p.state = 'PUBLISHED'
    AND p.is_synthetic = false
    AND s.expires_at > p_now
  LIMIT 1;
$$;

CREATE OR REPLACE FUNCTION growth_private.public_sitemap_entries(p_now timestamptz DEFAULT now())
RETURNS TABLE (
  canonical_path text,
  locale text,
  change_frequency text,
  priority numeric,
  last_modified_at timestamptz
)
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, public, growth_private
AS $$
  SELECT e.canonical_path, e.locale, e.change_frequency, e.priority, e.last_modified_at
  FROM growth_private.seo_sitemap_entries e
  JOIN growth_private.seo_page_candidates p ON p.page_id = e.page_id
  JOIN growth_private.seo_page_snapshots s ON s.page_id = p.page_id AND s.status = 'PUBLISHED'
  WHERE e.state = 'INCLUDED' AND p.state = 'PUBLISHED' AND p.is_synthetic = false AND s.expires_at > p_now
  ORDER BY e.canonical_path;
$$;

CREATE OR REPLACE FUNCTION growth_private.founder_overview(p_actor_subject text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, public, growth_private
AS $$
DECLARE
  v_result jsonb;
BEGIN
  PERFORM growth_private.assert_founder_admin(p_actor_subject);
  SELECT jsonb_build_object(
    'seo', jsonb_build_object(
      'candidates', count(*) FILTER (WHERE state IN ('DISCOVERED', 'CANDIDATE')),
      'indexable', count(*) FILTER (WHERE state = 'INDEXABLE'),
      'published', count(*) FILTER (WHERE state = 'PUBLISHED'),
      'noindex', count(*) FILTER (WHERE state = 'NOINDEX'),
      'decaying', count(*) FILTER (WHERE state = 'DECAYING')
    ),
    'crm', jsonb_build_object(
      'contacts', (SELECT count(*) FROM growth_private.crm_contacts),
      'mql', (SELECT count(*) FROM growth_private.crm_contacts WHERE lifecycle_stage = 'MQL'),
      'trials', (SELECT count(*) FROM growth_private.crm_contacts WHERE lifecycle_stage = 'TRIAL'),
      'customers', (SELECT count(*) FROM growth_private.crm_contacts WHERE lifecycle_stage = 'CUSTOMER')
    ),
    'alerts', jsonb_build_object(
      'pending', (SELECT count(*) FROM growth_private.tender_alert_subscriptions WHERE state = 'PENDING_CONFIRMATION'),
      'active', (SELECT count(*) FROM growth_private.tender_alert_subscriptions WHERE state = 'ACTIVE'),
      'suppressed', (SELECT count(*) FROM growth_private.tender_alert_subscriptions WHERE state = 'SUPPRESSED')
    ),
    'citations', jsonb_build_object(
      'total', (SELECT count(*) FROM growth_private.ai_citation_events),
      'last_30_days', (SELECT count(*) FROM growth_private.ai_citation_events WHERE observed_at >= now() - interval '30 days')
    ),
    'truth_boundaries', jsonb_build_array(
      'dataset != indexable page',
      'generated page != published page',
      'alert subscriber != trial user',
      'AI citation != endorsement',
      'CI pass != public indexing approval'
    )
  ) INTO v_result
  FROM growth_private.seo_page_candidates;
  RETURN v_result;
END;
$$;

CREATE OR REPLACE FUNCTION growth_private.admin_pages(p_actor_subject text)
RETURNS SETOF growth_private.seo_page_candidates
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, public, growth_private
AS $$
BEGIN
  PERFORM growth_private.assert_founder_admin(p_actor_subject);
  RETURN QUERY SELECT * FROM growth_private.seo_page_candidates ORDER BY updated_at DESC, canonical_path;
END;
$$;

CREATE OR REPLACE FUNCTION growth_private.subscribe_tender_alert(
  p_email_normalized text,
  p_email_hmac text,
  p_confirmation_token_digest text,
  p_country_code text,
  p_sector_slug text,
  p_locale text,
  p_cadence text,
  p_source_path text,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, growth_private
AS $$
DECLARE
  v_contact_id uuid;
  v_subscription_id uuid;
  v_state text;
BEGIN
  INSERT INTO growth_private.crm_contacts (
    email_normalized, email_hmac, source, lifecycle_stage, lead_score,
    consent_status, first_touch_path, last_touch_path, created_at, updated_at
  ) VALUES (
    lower(btrim(p_email_normalized)), p_email_hmac, 'TENDER_ALERT', 'LEAD', 20,
    'PENDING', p_source_path, p_source_path, p_now, p_now
  )
  ON CONFLICT (email_hmac) DO UPDATE SET
    last_touch_path = EXCLUDED.last_touch_path,
    updated_at = EXCLUDED.updated_at
  RETURNING contact_id INTO v_contact_id;

  INSERT INTO growth_private.tender_alert_subscriptions (
    contact_id, country_code, sector_slug, locale, cadence, state,
    confirmation_token_digest, source_path, created_at, updated_at
  ) VALUES (
    v_contact_id, p_country_code, p_sector_slug, p_locale, p_cadence,
    'PENDING_CONFIRMATION', p_confirmation_token_digest, p_source_path, p_now, p_now
  )
  ON CONFLICT (contact_id, country_code, sector_slug, cadence) DO UPDATE SET
    state = CASE
      WHEN growth_private.tender_alert_subscriptions.state = 'SUPPRESSED' THEN 'SUPPRESSED'
      ELSE 'PENDING_CONFIRMATION'
    END,
    confirmation_token_digest = EXCLUDED.confirmation_token_digest,
    source_path = EXCLUDED.source_path,
    updated_at = EXCLUDED.updated_at
  RETURNING subscription_id, state INTO v_subscription_id, v_state;

  INSERT INTO growth_private.crm_activities (
    contact_id, activity_type, actor_subject, payload, occurred_at
  ) VALUES (
    v_contact_id, 'TENDER_ALERT_REQUESTED', 'public',
    jsonb_build_object('country_code', p_country_code, 'sector_slug', p_sector_slug, 'cadence', p_cadence), p_now
  );

  RETURN jsonb_build_object(
    'subscription_id', v_subscription_id,
    'state', v_state,
    'contact_id', v_contact_id,
    'trial_created', false,
    'tenant_created', false
  );
END;
$$;

CREATE OR REPLACE FUNCTION growth_private.admin_contacts(p_actor_subject text)
RETURNS SETOF growth_private.crm_contacts
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, public, growth_private
AS $$
BEGIN
  PERFORM growth_private.assert_founder_admin(p_actor_subject);
  RETURN QUERY SELECT * FROM growth_private.crm_contacts ORDER BY updated_at DESC;
END;
$$;

CREATE OR REPLACE FUNCTION growth_private.admin_alerts(p_actor_subject text)
RETURNS TABLE (
  subscription_id uuid,
  email_normalized text,
  country_code text,
  sector_slug text,
  locale text,
  cadence text,
  state text,
  source_path text,
  created_at timestamptz,
  updated_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, public, growth_private
AS $$
BEGIN
  PERFORM growth_private.assert_founder_admin(p_actor_subject);
  RETURN QUERY
    SELECT s.subscription_id, c.email_normalized, s.country_code, s.sector_slug,
           s.locale, s.cadence, s.state, s.source_path, s.created_at, s.updated_at
    FROM growth_private.tender_alert_subscriptions s
    JOIN growth_private.crm_contacts c ON c.contact_id = s.contact_id
    ORDER BY s.updated_at DESC;
END;
$$;

CREATE OR REPLACE FUNCTION growth_private.record_ai_citation(
  p_actor_subject text,
  p_provider text,
  p_surface text,
  p_cited_url text,
  p_query_hmac text,
  p_source text,
  p_metadata jsonb,
  p_observed_at timestamptz
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, growth_private
AS $$
DECLARE v_id uuid;
BEGIN
  PERFORM growth_private.assert_founder_admin(p_actor_subject);
  INSERT INTO growth_private.ai_citation_events (
    provider, surface, cited_url, query_hmac, source, metadata,
    observed_at, recorded_by
  ) VALUES (
    p_provider, p_surface, p_cited_url, p_query_hmac, p_source,
    coalesce(p_metadata, '{}'::jsonb), p_observed_at, p_actor_subject
  ) RETURNING citation_event_id INTO v_id;
  INSERT INTO growth_private.founder_admin_audit_events (
    event_type, actor_subject, target_type, target_id, payload
  ) VALUES (
    'AI_CITATION_RECORDED', p_actor_subject, 'AI_CITATION', v_id::text,
    jsonb_build_object('provider', p_provider, 'cited_url', p_cited_url)
  );
  RETURN v_id;
END;
$$;

REVOKE ALL ON ALL TABLES IN SCHEMA growth_private FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA growth_private FROM axignal_app;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA growth_private FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA growth_private FROM PUBLIC;

GRANT USAGE ON SCHEMA growth_private TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.assert_founder_admin(text) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.evaluate_indexability(uuid, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.publish_page_snapshot(uuid, text, text, timestamptz, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.public_discovery_page(text, text, text, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.public_sitemap_entries(timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.founder_overview(text) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.admin_pages(text) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.subscribe_tender_alert(text, text, text, text, text, text, text, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.admin_contacts(text) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.admin_alerts(text) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.record_ai_citation(text, text, text, text, text, text, jsonb, timestamptz) TO axignal_app;
