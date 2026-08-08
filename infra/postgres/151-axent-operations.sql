-- 151-axent-operations.sql — AXENT operational surfaces (cierre funcional E2E)
--
-- Additive spine for the AXENT workspace-operations mandate:
--   * opportunity_workspaces.title     -> human-resolvable workspace name
--     ("añade ... al workspace Iberia")
--   * opportunity_pursuits.priority    -> explicit priority field with a
--     typed domain (HIGH/MEDIUM/LOW), replacing the previous misuse of
--     record_qualification(decision=...) for priority (semantically wrong:
--     a qualification decision is BID/NO_BID, not a priority).
--
-- Applies cleanly on top of 143 (opportunity operations spine); no data
-- migration is required (both columns default to NULL / MEDIUM).

ALTER TABLE tenant_private.opportunity_workspaces
  ADD COLUMN IF NOT EXISTS title text;

ALTER TABLE tenant_private.opportunity_pursuits
  ADD COLUMN IF NOT EXISTS priority text
  NOT NULL DEFAULT 'MEDIUM'
  CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW'));

-- Workspace lookup by human-readable title (tenant-scoped).
CREATE INDEX IF NOT EXISTS opportunity_workspaces_title_idx
  ON tenant_private.opportunity_workspaces (tenant_id, title)
  WHERE title IS NOT NULL;
