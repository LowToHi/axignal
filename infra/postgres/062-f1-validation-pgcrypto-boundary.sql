ALTER FUNCTION evaluation.validation_condition(text, text, text)
  SET search_path = pg_catalog, public, evaluation;

ALTER FUNCTION evaluation.complete_validation_session(
  uuid, uuid, text, text[], text[], integer, text
) SET search_path = pg_catalog, evaluation, public;
