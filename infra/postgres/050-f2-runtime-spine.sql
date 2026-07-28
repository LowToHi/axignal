DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='axignal_scheduler') THEN
    CREATE ROLE axignal_scheduler NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='axignal_scheduler_login') THEN
    CREATE ROLE axignal_scheduler_login LOGIN PASSWORD 'axignal_scheduler';
  ELSE
    ALTER ROLE axignal_scheduler_login LOGIN PASSWORD 'axignal_scheduler';
  END IF;
END $$;
GRANT axignal_scheduler TO axignal_scheduler_login;
GRANT USAGE ON SCHEMA axignal_global TO axignal_scheduler;

CREATE TABLE IF NOT EXISTS axignal_global.scheduled_jobs (
  scheduled_job_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid,
  job_kind text NOT NULL CHECK (job_kind IN (
    'VERIFY_RUNTIME_HEALTH','RECOVER_EXPIRED_SCHEDULER_LEASES',
    'CHECK_SOURCE_FRESHNESS','REBUILD_DOSSIER_IF_DIRTY','RETRY_STALE_OUTBOX'
  )),
  idempotency_key text NOT NULL UNIQUE,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  trace_context jsonb NOT NULL DEFAULT '{}'::jsonb,
  state text NOT NULL DEFAULT 'SCHEDULED' CHECK (state IN (
    'SCHEDULED','QUEUED','LEASED','SUCCEEDED','FAILED','DEAD_LETTER','CANCELLED'
  )),
  run_at timestamptz NOT NULL DEFAULT now(),
  attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  max_attempts integer NOT NULL DEFAULT 3 CHECK (max_attempts BETWEEN 1 AND 20),
  lease_owner text,
  lease_expires_at timestamptz,
  result jsonb,
  last_error_code text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS scheduled_jobs_due_idx
  ON axignal_global.scheduled_jobs(state,run_at,created_at);
CREATE INDEX IF NOT EXISTS scheduled_jobs_lease_idx
  ON axignal_global.scheduled_jobs(state,lease_expires_at);

CREATE TABLE IF NOT EXISTS axignal_global.scheduler_outbox_events (
  scheduler_outbox_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scheduled_job_id uuid NOT NULL UNIQUE REFERENCES axignal_global.scheduled_jobs(scheduled_job_id) ON DELETE CASCADE,
  payload jsonb NOT NULL,
  status text NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','PUBLISHED')),
  publish_attempts integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz
);
CREATE INDEX IF NOT EXISTS scheduler_outbox_pending_idx
  ON axignal_global.scheduler_outbox_events(status,created_at);

CREATE TABLE IF NOT EXISTS axignal_global.scheduler_events (
  scheduler_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scheduled_job_id uuid NOT NULL REFERENCES axignal_global.scheduled_jobs(scheduled_job_id) ON DELETE CASCADE,
  event_type text NOT NULL CHECK (event_type IN (
    'JOB_SCHEDULED','JOB_QUEUED','JOB_LEASED','JOB_SUCCEEDED',
    'JOB_FAILED','JOB_DEAD_LETTERED','LEASE_RECOVERED'
  )),
  actor_id text,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS scheduler_events_job_idx
  ON axignal_global.scheduler_events(scheduled_job_id,occurred_at);

CREATE OR REPLACE FUNCTION axignal_global.reject_scheduler_event_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'AXIGNAL_SCHEDULER_EVENTS_APPEND_ONLY'; END $$;
DROP TRIGGER IF EXISTS scheduler_events_immutable ON axignal_global.scheduler_events;
CREATE TRIGGER scheduler_events_immutable BEFORE UPDATE OR DELETE
ON axignal_global.scheduler_events FOR EACH ROW
EXECUTE FUNCTION axignal_global.reject_scheduler_event_mutation();

CREATE OR REPLACE FUNCTION axignal_global.schedule_maintenance_job(
  p_job_kind text,p_idempotency_key text,p_payload jsonb,p_tenant_id uuid DEFAULT NULL,
  p_run_at timestamptz DEFAULT NULL,p_max_attempts integer DEFAULT 3,
  p_trace_context jsonb DEFAULT '{}'::jsonb
) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,axignal_global AS $$
DECLARE existing_job axignal_global.scheduled_jobs%ROWTYPE; created_id uuid;
BEGIN
  IF p_idempotency_key IS NULL OR length(trim(p_idempotency_key)) < 8 THEN
    RAISE EXCEPTION 'AXIGNAL_SCHEDULER_IDEMPOTENCY_KEY_REQUIRED';
  END IF;
  SELECT * INTO existing_job FROM axignal_global.scheduled_jobs
    WHERE idempotency_key=p_idempotency_key;
  IF FOUND THEN
    IF existing_job.job_kind<>p_job_kind
       OR existing_job.tenant_id IS DISTINCT FROM p_tenant_id
       OR existing_job.payload<>COALESCE(p_payload,'{}'::jsonb)
       OR existing_job.max_attempts<>p_max_attempts THEN
      RAISE EXCEPTION 'AXIGNAL_SCHEDULER_IDEMPOTENCY_CONFLICT';
    END IF;
    RETURN existing_job.scheduled_job_id;
  END IF;
  INSERT INTO axignal_global.scheduled_jobs(
    tenant_id,job_kind,idempotency_key,payload,trace_context,run_at,max_attempts
  ) VALUES (
    p_tenant_id,p_job_kind,p_idempotency_key,COALESCE(p_payload,'{}'::jsonb),
    COALESCE(p_trace_context,'{}'::jsonb),COALESCE(p_run_at,now()),p_max_attempts
  ) RETURNING scheduled_job_id INTO created_id;
  INSERT INTO axignal_global.scheduler_outbox_events(scheduled_job_id,payload)
  SELECT scheduled_job_id,jsonb_build_object(
    'scheduled_job_id',scheduled_job_id,'tenant_id',tenant_id,
    'job_kind',job_kind,'trace_context',trace_context
  ) FROM axignal_global.scheduled_jobs WHERE scheduled_job_id=created_id;
  INSERT INTO axignal_global.scheduler_events(scheduled_job_id,event_type,actor_id,payload)
  VALUES(created_id,'JOB_SCHEDULED',current_user,jsonb_build_object('idempotency_key',p_idempotency_key));
  RETURN created_id;
END $$;

DROP FUNCTION IF EXISTS axignal_global.scheduler_pending_outbox(integer);
CREATE FUNCTION axignal_global.scheduler_pending_outbox(p_limit integer DEFAULT 100)
RETURNS TABLE(
  scheduler_outbox_event_id uuid,
  scheduled_job_id uuid,
  publish_attempts integer,
  payload jsonb
)
LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,axignal_global AS $$
  SELECT e.scheduler_outbox_event_id,e.scheduled_job_id,e.publish_attempts,e.payload
  FROM axignal_global.scheduler_outbox_events e
  JOIN axignal_global.scheduled_jobs j USING(scheduled_job_id)
  WHERE e.status='PENDING' AND j.state='SCHEDULED' AND j.run_at<=now()
  ORDER BY e.created_at LIMIT GREATEST(1,LEAST(p_limit,500))
$$;

CREATE OR REPLACE FUNCTION axignal_global.mark_scheduler_outbox_published(p_event_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,axignal_global AS $$
DECLARE target_job_id uuid;
BEGIN
  UPDATE axignal_global.scheduler_outbox_events SET
    status='PUBLISHED',publish_attempts=publish_attempts+1,
    published_at=COALESCE(published_at,now())
  WHERE scheduler_outbox_event_id=p_event_id AND status='PENDING'
  RETURNING scheduled_job_id INTO target_job_id;
  IF target_job_id IS NULL THEN RETURN; END IF;
  UPDATE axignal_global.scheduled_jobs SET state='QUEUED',updated_at=now()
    WHERE scheduled_job_id=target_job_id AND state='SCHEDULED';
  INSERT INTO axignal_global.scheduler_events(scheduled_job_id,event_type,actor_id)
    VALUES(target_job_id,'JOB_QUEUED',current_user);
END $$;

CREATE OR REPLACE FUNCTION axignal_global.claim_scheduled_job(
  p_job_id uuid,p_worker_id text,p_lease_seconds integer DEFAULT 30
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,axignal_global AS $$
DECLARE claimed axignal_global.scheduled_jobs%ROWTYPE;
BEGIN
  IF p_worker_id IS NULL OR length(trim(p_worker_id))<3 THEN
    RAISE EXCEPTION 'AXIGNAL_SCHEDULER_WORKER_ID_REQUIRED';
  END IF;
  SELECT * INTO claimed FROM axignal_global.scheduled_jobs
    WHERE scheduled_job_id=p_job_id FOR UPDATE;
  IF NOT FOUND THEN RETURN NULL; END IF;
  IF claimed.state='LEASED' AND claimed.lease_expires_at<=now() THEN
    UPDATE axignal_global.scheduled_jobs SET state='QUEUED',lease_owner=NULL,
      lease_expires_at=NULL,updated_at=now() WHERE scheduled_job_id=p_job_id;
    claimed.state:='QUEUED';
  END IF;
  IF claimed.state<>'QUEUED' THEN RETURN NULL; END IF;
  IF claimed.attempt_count>=claimed.max_attempts THEN
    UPDATE axignal_global.scheduled_jobs SET state='DEAD_LETTER',updated_at=now()
      WHERE scheduled_job_id=p_job_id;
    INSERT INTO axignal_global.scheduler_events(scheduled_job_id,event_type,actor_id)
      VALUES(p_job_id,'JOB_DEAD_LETTERED',p_worker_id);
    RETURN NULL;
  END IF;
  UPDATE axignal_global.scheduled_jobs SET state='LEASED',
    attempt_count=attempt_count+1,lease_owner=p_worker_id,
    lease_expires_at=now()+make_interval(secs=>GREATEST(1,p_lease_seconds)),updated_at=now()
  WHERE scheduled_job_id=p_job_id RETURNING * INTO claimed;
  INSERT INTO axignal_global.scheduler_events(scheduled_job_id,event_type,actor_id,payload)
    VALUES(p_job_id,'JOB_LEASED',p_worker_id,jsonb_build_object('attempt_count',claimed.attempt_count));
  RETURN to_jsonb(claimed);
END $$;

CREATE OR REPLACE FUNCTION axignal_global.complete_scheduled_job(
  p_job_id uuid,p_worker_id text,p_result jsonb
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,axignal_global AS $$
BEGIN
  UPDATE axignal_global.scheduled_jobs SET state='SUCCEEDED',
    result=COALESCE(p_result,'{}'::jsonb),lease_owner=NULL,lease_expires_at=NULL,
    last_error_code=NULL,updated_at=now()
  WHERE scheduled_job_id=p_job_id AND state='LEASED' AND lease_owner=p_worker_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'AXIGNAL_SCHEDULER_LEASE_MISMATCH'; END IF;
  INSERT INTO axignal_global.scheduler_events(scheduled_job_id,event_type,actor_id,payload)
    VALUES(p_job_id,'JOB_SUCCEEDED',p_worker_id,COALESCE(p_result,'{}'::jsonb));
END $$;

CREATE OR REPLACE FUNCTION axignal_global.fail_scheduled_job(
  p_job_id uuid,p_worker_id text,p_error_code text,p_retry_delay_seconds integer DEFAULT 0
) RETURNS text LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,axignal_global AS $$
DECLARE target axignal_global.scheduled_jobs%ROWTYPE; next_state text;
BEGIN
  SELECT * INTO target FROM axignal_global.scheduled_jobs
    WHERE scheduled_job_id=p_job_id FOR UPDATE;
  IF NOT FOUND OR target.state<>'LEASED' OR target.lease_owner IS DISTINCT FROM p_worker_id THEN
    RAISE EXCEPTION 'AXIGNAL_SCHEDULER_LEASE_MISMATCH';
  END IF;
  next_state:=CASE WHEN target.attempt_count>=target.max_attempts THEN 'DEAD_LETTER' ELSE 'SCHEDULED' END;
  UPDATE axignal_global.scheduled_jobs SET state=next_state,
    run_at=CASE WHEN next_state='SCHEDULED' THEN now()+make_interval(secs=>GREATEST(0,p_retry_delay_seconds)) ELSE run_at END,
    lease_owner=NULL,lease_expires_at=NULL,last_error_code=p_error_code,updated_at=now()
  WHERE scheduled_job_id=p_job_id;
  IF next_state='SCHEDULED' THEN
    UPDATE axignal_global.scheduler_outbox_events SET status='PENDING',published_at=NULL
      WHERE scheduled_job_id=p_job_id;
  END IF;
  INSERT INTO axignal_global.scheduler_events(scheduled_job_id,event_type,actor_id,payload)
  VALUES(p_job_id,CASE WHEN next_state='DEAD_LETTER' THEN 'JOB_DEAD_LETTERED' ELSE 'JOB_FAILED' END,
    p_worker_id,jsonb_build_object('error_code',p_error_code,'next_state',next_state));
  RETURN next_state;
END $$;

CREATE OR REPLACE FUNCTION axignal_global.recover_expired_scheduler_leases()
RETURNS integer LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,axignal_global AS $$
DECLARE recovered integer;
BEGIN
  WITH updated AS (
    UPDATE axignal_global.scheduled_jobs SET
      state=CASE WHEN attempt_count>=max_attempts THEN 'DEAD_LETTER' ELSE 'SCHEDULED' END,
      run_at=now(),lease_owner=NULL,lease_expires_at=NULL,
      last_error_code='LEASE_EXPIRED',updated_at=now()
    WHERE state='LEASED' AND lease_expires_at<=now()
    RETURNING scheduled_job_id,state
  ) SELECT count(*) INTO recovered FROM updated;
  UPDATE axignal_global.scheduler_outbox_events e SET status='PENDING',published_at=NULL
  FROM axignal_global.scheduled_jobs j
  WHERE e.scheduled_job_id=j.scheduled_job_id AND j.state='SCHEDULED'
    AND j.last_error_code='LEASE_EXPIRED' AND j.updated_at>=transaction_timestamp();
  INSERT INTO axignal_global.scheduler_events(scheduled_job_id,event_type,actor_id,payload)
  SELECT scheduled_job_id,
    CASE WHEN state='DEAD_LETTER' THEN 'JOB_DEAD_LETTERED' ELSE 'LEASE_RECOVERED' END,
    current_user,jsonb_build_object('error_code','LEASE_EXPIRED')
  FROM axignal_global.scheduled_jobs
  WHERE last_error_code='LEASE_EXPIRED' AND updated_at>=transaction_timestamp();
  RETURN recovered;
END $$;

REVOKE ALL ON axignal_global.scheduled_jobs FROM PUBLIC,axignal_scheduler;
REVOKE ALL ON axignal_global.scheduler_outbox_events FROM PUBLIC,axignal_scheduler;
REVOKE ALL ON axignal_global.scheduler_events FROM PUBLIC,axignal_scheduler;
REVOKE ALL ON FUNCTION axignal_global.schedule_maintenance_job(text,text,jsonb,uuid,timestamptz,integer,jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION axignal_global.scheduler_pending_outbox(integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION axignal_global.mark_scheduler_outbox_published(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION axignal_global.claim_scheduled_job(uuid,text,integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION axignal_global.complete_scheduled_job(uuid,text,jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION axignal_global.fail_scheduled_job(uuid,text,text,integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION axignal_global.recover_expired_scheduler_leases() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION axignal_global.schedule_maintenance_job(text,text,jsonb,uuid,timestamptz,integer,jsonb) TO axignal_scheduler;
GRANT EXECUTE ON FUNCTION axignal_global.scheduler_pending_outbox(integer) TO axignal_scheduler;
GRANT EXECUTE ON FUNCTION axignal_global.mark_scheduler_outbox_published(uuid) TO axignal_scheduler;
GRANT EXECUTE ON FUNCTION axignal_global.claim_scheduled_job(uuid,text,integer) TO axignal_scheduler;
GRANT EXECUTE ON FUNCTION axignal_global.complete_scheduled_job(uuid,text,jsonb) TO axignal_scheduler;
GRANT EXECUTE ON FUNCTION axignal_global.fail_scheduled_job(uuid,text,text,integer) TO axignal_scheduler;
GRANT EXECUTE ON FUNCTION axignal_global.recover_expired_scheduler_leases() TO axignal_scheduler;
REVOKE INSERT,UPDATE,DELETE ON axignal_global.canonical_claims FROM axignal_scheduler;
REVOKE INSERT,UPDATE,DELETE ON axignal_global.evidence_objects FROM axignal_scheduler;
REVOKE INSERT,UPDATE,DELETE ON axignal_global.admission_decisions FROM axignal_scheduler;
