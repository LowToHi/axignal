"use client";

import { useState } from "react";

/**
 * Transition a pursuit to a new state (server proxy -> API -> PostgreSQL).
 */
export function TransitionPursuitForm({ pursuitRef }: { pursuitRef: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const states = ["QUALIFIED", "DECISION_REVIEW", "ACTIVE", "WON", "LOST", "WITHDRAWN"];

  async function transition(newState: string) {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const response = await fetch(
        `/api/opportunities/pursuits/${pursuitRef}/transition`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            new_state: newState,
            decided_by: newState === "WON" || newState === "LOST" ? "web-user" : undefined
          })
        }
      );
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        setError(body?.detail ?? `Error ${response.status}`);
        return;
      }
      setMessage(`Transición a ${newState} OK`);
      window.location.reload();
    } catch {
      setError("No se pudo contactar con la API.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      {error ? <p style={{ color: "var(--error, #c0392b)" }}>{error}</p> : null}
      {message ? <p>{message}</p> : null}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        {states.map((state) => (
          <button
            key={state}
            type="button"
            disabled={busy}
            onClick={() => transition(state)}
          >
            {state}
          </button>
        ))}
      </div>
    </div>
  );
}
