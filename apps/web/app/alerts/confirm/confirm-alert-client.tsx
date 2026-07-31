"use client";

import { useState } from "react";

export function ConfirmAlertClient({ token }: { token: string }) {
  const [state, setState] = useState<
    "idle" | "confirming" | "confirmed" | "error"
  >("idle");

  async function confirm() {
    setState("confirming");
    const response = await fetch("/api/public/tender-alerts/confirm", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ token })
    });
    setState(response.ok ? "confirmed" : "error");
  }

  return (
    <main className="alert-confirm-shell">
      <section className="alert-confirm-card">
        <span>AXIGNAL TENDER ALERT</span>
        <h1>
          {state === "confirmed"
            ? "Your tender alert is active."
            : "Confirm your tender alert."}
        </h1>
        <p>
          This confirms email delivery for the selected public-contract market.
          It does not create an AXIGNAL account, organisation, trial or paid
          subscription.
        </p>
        {state !== "confirmed" && (
          <button
            type="button"
            onClick={confirm}
            disabled={state === "confirming"}
          >
            {state === "confirming" ? "Confirming…" : "Confirm tender alert"}
          </button>
        )}
        {state === "confirmed" && <a href="/">Return to AXIGNAL</a>}
        {state === "error" && (
          <p role="alert">
            This confirmation is invalid, suppressed or currently unavailable.
          </p>
        )}
      </section>
    </main>
  );
}
