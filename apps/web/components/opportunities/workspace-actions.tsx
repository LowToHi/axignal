"use client";

import { useState } from "react";

/**
 * Create a bid workspace for a pursuit, then record outcome + learning.
 */
export function WorkspaceActions({
  pursuitRef,
  opportunityRef
}: {
  pursuitRef: string;
  opportunityRef: string;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);

  async function createWorkspace() {
    setBusy(true);
    setError(null);
    try {
      const id = crypto.randomUUID();
      const response = await fetch(`/api/opportunities/workspaces`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          workspace_id: id,
          pursuit_ref: pursuitRef,
          opportunity_ref: opportunityRef,
          opportunity_version_digest: "web-created",
          subscriber_profile_version: "v1",
          assessment_version: "v1"
        })
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        setError(body?.detail ?? `Error ${response.status}`);
        return;
      }
      setWorkspaceId(id);
    } catch {
      setError("No se pudo contactar con la API.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      {error ? <p style={{ color: "var(--error, #c0392b)" }}>{error}</p> : null}
      {workspaceId ? (
        <p>
          Workspace creado: <code>{workspaceId}</code>
        </p>
      ) : (
        <button type="button" disabled={busy} onClick={createWorkspace}>
          Crear Bid Workspace
        </button>
      )}
    </div>
  );
}
