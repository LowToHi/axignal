"use client";

import { useState } from "react";

/**
 * Create a pursuit from an opportunity (server proxy -> API -> PostgreSQL).
 */
export function CreatePursuitForm({ opportunityRef }: { opportunityRef: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdRef, setCreatedRef] = useState<string | null>(null);

  async function createPursuit() {
    setBusy(true);
    setError(null);
    try {
      const pursuitRef = `prs_web_${Date.now().toString(36)}${Math.random()
        .toString(36)
        .slice(2, 6)}`;
      const response = await fetch(`/api/opportunities/pursuits`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          pursuit_ref: pursuitRef,
          opportunity_ref: opportunityRef,
          state: "QUALIFIED"
        })
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        setError(body?.detail ?? `Error ${response.status}`);
        return;
      }
      setCreatedRef(pursuitRef);
    } catch {
      setError("No se pudo contactar con la API.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      {createdRef ? (
        <p>
          Pursuit creado: <strong>{createdRef}</strong>.{" "}
          <a href="/opportunity-intelligence/pursuits">Ver pursuits</a>
        </p>
      ) : (
        <>
          {error ? <p style={{ color: "var(--error, #c0392b)" }}>{error}</p> : null}
          <button type="button" disabled={busy} onClick={createPursuit}>
            Crear pursuit (QUALIFIED)
          </button>
        </>
      )}
    </div>
  );
}
