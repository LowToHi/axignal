"use client";

import { FormEvent, useState } from "react";

type AlertState = "idle" | "submitting" | "accepted" | "error";

export function TenderAlertForm({
  countryCode,
  sectorSlug,
  sourcePath,
  testRuntime = false
}: {
  countryCode: string;
  sectorSlug: string;
  sourcePath: string;
  testRuntime?: boolean;
}) {
  const [state, setState] = useState<AlertState>("idle");
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const cadence = String(form.get("cadence") ?? "DAILY");
    setState("submitting");
    const response = await fetch("/api/public/tender-alerts", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        email,
        country_code: countryCode,
        sector_slug: sectorSlug,
        locale: "en",
        cadence,
        source_path: sourcePath,
        bot_token: testRuntime ? "axignal-test-bot-pass" : String(form.get("bot-token") ?? "")
      })
    });
    const body = (await response.json().catch(() => ({}))) as Record<string, unknown>;
    if (!response.ok) {
      setState("error");
      setMessage("The alert could not be prepared. No account or trial was created.");
      return;
    }
    setState("accepted");
    setMessage(typeof body.message === "string" ? body.message : "Check your email to confirm the alert.");
    event.currentTarget.reset();
  }

  return (
    <form className="tender-alert-form" onSubmit={submit} aria-label="Tender alert subscription">
      <div>
        <span>TENDER ALERT</span>
        <strong>Receive new matching opportunities.</strong>
        <small>Double opt-in. An alert does not create an AXIGNAL account, tenant or trial.</small>
      </div>
      <label>
        <span>Professional email</span>
        <input name="email" type="email" required autoComplete="email" placeholder="you@company.com" />
      </label>
      <label>
        <span>Cadence</span>
        <select name="cadence" defaultValue="DAILY">
          <option value="IMMEDIATE">Immediate</option>
          <option value="DAILY">Daily digest</option>
          <option value="WEEKLY">Weekly digest</option>
        </select>
      </label>
      {!testRuntime && <input name="bot-token" type="hidden" value="" readOnly />}
      <button type="submit" disabled={state === "submitting"}>{state === "submitting" ? "Preparing…" : "Create tender alert"}</button>
      {message && <p role="status" data-state={state}>{message}</p>}
    </form>
  );
}
