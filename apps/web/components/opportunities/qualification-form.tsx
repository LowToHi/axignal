"use client";

import { useState } from "react";

/**
 * Qualification controls: calls the server proxy (which adds the identity
 * assertion), then reloads to show the updated state.
 */
export function QualificationForm({
  opportunityRef,
  currentState
}: {
  opportunityRef: string;
  currentState: string;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function qualify(decision: "BID" | "NO_BID" | "PENDING_REVIEW") {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/opportunities/opportunities/${opportunityRef}/qualify`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ decision, decided_by: "web-user" })
        }
      );
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        setError(body?.detail ?? `Error ${response.status}`);
        return;
      }
      window.location.reload();
    } catch {
      setError("No se pudo contactar con la API.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <p>Estado actual: <strong>{currentState}</strong></p>
      {error ? <p style={{ color: "var(--error, #c0392b)" }}>{error}</p> : null}
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
        <button type="button" disabled={busy} onClick={() => qualify("BID")}>
          Bid
        </button>
        <button type="button" disabled={busy} onClick={() => qualify("NO_BID")}>
          No bid
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => qualify("PENDING_REVIEW")}
        >
          Pending review
        </button>
      </div>
    </div>
  );
}
