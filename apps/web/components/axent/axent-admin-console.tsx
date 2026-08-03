"use client";

import { useCallback, useEffect, useState } from "react";

type SupportCase = {
  case_id: string;
  case_type: string;
  severity: string;
  status: string;
  service_area: string;
  customer_impact?: string | null;
  owner_subject?: string | null;
  opened_by_subject: string;
  opened_at: string;
};

type CasesResponse = {
  cases?: SupportCase[];
  error?: string;
  detail?: string;
};

export function AxentAdminConsole() {
  const [cases, setCases] = useState<SupportCase[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [resolution, setResolution] = useState<Record<string, string>>({});

  const loadCases = useCallback(async () => {
    const response = await fetch("/api/axent-admin/cases", { cache: "no-store" });
    const payload = (await response.json()) as CasesResponse;
    if (!response.ok) {
      setError(payload.detail ?? payload.error ?? "Support queue unavailable.");
      return;
    }
    setCases(payload.cases ?? []);
    setError(null);
  }, []);

  useEffect(() => {
    void loadCases();
  }, [loadCases]);

  async function transition(
    supportCase: SupportCase,
    action: "ACKNOWLEDGE" | "ASSIGN" | "RESOLVE" | "REOPEN" | "CLOSE"
  ) {
    setBusy(supportCase.case_id);
    setError(null);
    try {
      const response = await fetch(
        `/api/axent-admin/cases/${supportCase.case_id}/transition`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            transition: action,
            resolution: action === "RESOLVE" ? resolution[supportCase.case_id] : null
          })
        }
      );
      const payload = (await response.json()) as { detail?: string };
      if (!response.ok) throw new Error(payload.detail ?? "Transition failed.");
      await loadCases();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Transition failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main style={{ minHeight: "100vh", background: "#07111d", color: "#eef5ff", padding: "2rem" }}>
      <header style={{ maxWidth: 1120, margin: "0 auto 2rem" }}>
        <p style={{ letterSpacing: "0.16em", textTransform: "uppercase", opacity: 0.65 }}>
          AXIGNAL · Human authority
        </p>
        <h1>Axent support console</h1>
        <p>Assign, investigate, resolve and reopen escalated customer cases.</p>
      </header>
      <section aria-live="polite" style={{ maxWidth: 1120, margin: "0 auto", display: "grid", gap: "1rem" }}>
        {error && <div role="alert">{error}</div>}
        {!error && cases.length === 0 && <p>No open support cases.</p>}
        {cases.map((supportCase) => (
          <article key={supportCase.case_id} style={{ border: "1px solid #294057", borderRadius: 12, padding: "1rem" }}>
            <strong>{supportCase.severity} · {supportCase.case_type}</strong>
            <p>{supportCase.service_area} — {supportCase.status}</p>
            <p>{supportCase.customer_impact ?? "No customer impact supplied."}</p>
            <small>Opened by {supportCase.opened_by_subject}</small>
            <textarea
              aria-label={`Resolution for ${supportCase.case_id}`}
              value={resolution[supportCase.case_id] ?? ""}
              onChange={(event) => setResolution((current) => ({ ...current, [supportCase.case_id]: event.target.value }))}
              placeholder="Verified resolution and customer-facing explanation"
              style={{ display: "block", width: "100%", minHeight: 84, margin: "1rem 0" }}
            />
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              {(["ACKNOWLEDGE", "ASSIGN", "RESOLVE", "REOPEN", "CLOSE"] as const).map((action) => (
                <button
                  key={action}
                  type="button"
                  disabled={busy === supportCase.case_id || (action === "RESOLVE" && !(resolution[supportCase.case_id] ?? "").trim())}
                  onClick={() => void transition(supportCase, action)}
                >
                  {action}
                </button>
              ))}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
