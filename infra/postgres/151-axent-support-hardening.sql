CREATE UNIQUE INDEX IF NOT EXISTS support_messages_tenant_message_uidx
  ON tenant_private.support_messages (tenant_id, message_id);
CREATE UNIQUE INDEX IF NOT EXISTS support_invocations_tenant_invocation_uidx
  ON tenant_private.support_tool_invocations (tenant_id, invocation_id);

CREATE OR REPLACE FUNCTION tenant_private.reject_axent_citation_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'AXENT citation ledger is append-only';
END $$;

CREATE OR REPLACE FUNCTION tenant_private.reject_axent_action_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'AXENT action ledger is append-only';
END $$;

DROP TRIGGER IF EXISTS support_citations_immutable ON tenant_private.support_message_citations;
CREATE TRIGGER support_citations_immutable
BEFORE UPDATE OR DELETE ON tenant_private.support_message_citations
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_axent_citation_mutation();

DROP TRIGGER IF EXISTS support_actions_immutable ON tenant_private.support_actions;
CREATE TRIGGER support_actions_immutable
BEFORE UPDATE OR DELETE ON tenant_private.support_actions
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_axent_action_mutation();

-- Tool invocations are immutable after completion, but a PENDING row may be completed once.
CREATE OR REPLACE FUNCTION tenant_private.guard_axent_invocation_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.result_status <> 'PENDING' THEN
    RAISE EXCEPTION 'completed AXENT invocation is immutable';
  END IF;
  IF NEW.tenant_id <> OLD.tenant_id
     OR NEW.conversation_id <> OLD.conversation_id
     OR NEW.tool_name <> OLD.tool_name
     OR NEW.input_hash <> OLD.input_hash
     OR NEW.decision <> OLD.decision THEN
    RAISE EXCEPTION 'AXENT invocation authority fields are immutable';
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS support_invocations_immutable ON tenant_private.support_tool_invocations;
CREATE TRIGGER support_invocations_guard
BEFORE UPDATE OR DELETE ON tenant_private.support_tool_invocations
FOR EACH ROW EXECUTE FUNCTION tenant_private.guard_axent_invocation_mutation();
