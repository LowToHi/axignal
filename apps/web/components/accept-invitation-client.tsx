"use client";

import { useState } from "react";

export function AcceptInvitationClient({ token }: { token: string }) {
  const [state, setState] = useState<"idle" | "submitting" | "accepted" | "error">("idle");
  const [error, setError] = useState("");

  async function accept() {
    if (state === "submitting") return;
    setState("submitting");
    setError("");
    const response = await fetch("/api/organisation/seats/invitations/accept", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ token, confirm_acceptance: true })
    });
    const body = (await response.json().catch(() => null)) as { detail?: string; error?: string } | null;
    if (!response.ok) {
      setError(body?.detail ?? body?.error ?? "Invitation acceptance failed.");
      setState("error");
      return;
    }
    setState("accepted");
  }

  return (
    <main className="auth-shell">
      <section className="auth-card" aria-label="Accept AXIGNAL invitation">
        <span className="auth-kicker">TENANT MEMBERSHIP</span>
        <h1>Join your AXIGNAL organisation</h1>
        <p>
          Acceptance consumes the seat already reserved for this invitation and binds
          your authenticated identity to the organisation role selected by its admin.
        </p>
        {state === "accepted" ? (
          <>
            <p>Invitation accepted. Your membership and seat allocation are active.</p>
            <a href="/">Open AXIGNAL</a>
          </>
        ) : (
          <button type="button" disabled={state === "submitting"} onClick={() => void accept()}>
            {state === "submitting" ? "Accepting…" : "Accept invitation"}
          </button>
        )}
        {error && <p className="auth-error" role="alert">{error}</p>}
        <small>The invitation is single-use, email-bound and tenant-bound.</small>
      </section>
    </main>
  );
}
