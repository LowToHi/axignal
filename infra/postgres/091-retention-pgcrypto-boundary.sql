-- pgcrypto installs digest() in the public schema. Retention definer functions
-- keep a fixed search path, but public must not remain writable by PUBLIC before
-- it is admitted for explicit extension resolution.

REVOKE CREATE ON SCHEMA public FROM PUBLIC;

ALTER FUNCTION tenant_private.reject_terminally_deleted_tenant()
  SET search_path TO pg_catalog, public;
ALTER FUNCTION tenant_private.purge_claimed_workspace(uuid, text, timestamptz)
  SET search_path TO pg_catalog, public;
ALTER FUNCTION tenant_private.reapply_deletion_tombstone(uuid, timestamptz)
  SET search_path TO pg_catalog, public;
