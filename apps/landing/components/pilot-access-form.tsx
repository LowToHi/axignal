"use client";

import { FormEvent, useState } from "react";

type FormStatus =
  | { state: "idle" }
  | { state: "submitting" }
  | { state: "success"; message: string }
  | { state: "error"; message: string; contactEmail?: string };

const roles = [
  "Head of B2G or public-sector sales",
  "Business development",
  "Bid or proposal management",
  "Tender or procurement intelligence",
  "Market expansion or internationalisation",
  "Founder or executive",
  "Advisory or consulting",
  "Other"
] as const;

type PilotAccessFormProps = {
  messageVersion: string;
};

export function PilotAccessForm({ messageVersion }: PilotAccessFormProps) {
  const [status, setStatus] = useState<FormStatus>({ state: "idle" });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus({ state: "submitting" });

    const form = event.currentTarget;
    const formData = new FormData(form);
    const payload = {
      email: String(formData.get("email") ?? ""),
      role: String(formData.get("role") ?? ""),
      company: String(formData.get("company") ?? ""),
      useCase: String(formData.get("useCase") ?? ""),
      consent: formData.get("consent") === "on",
      website: String(formData.get("website") ?? ""),
      messageVersion
    };

    try {
      const response = await fetch("/api/pilot-intake", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload)
      });
      const body = (await response.json()) as {
        status?: string;
        message?: string;
        contactEmail?: string;
      };

      if (!response.ok) {
        setStatus({
          state: "error",
          message: body.message ?? "The controlled B2G trial request could not be delivered.",
          ...(body.contactEmail ? { contactEmail: body.contactEmail } : {})
        });
        return;
      }

      form.reset();
      window.dispatchEvent(
        new CustomEvent("axignal:conversion", {
          detail: {
            event: "b2g_trial_requested",
            source: "landing_b2g_opportunity_v1_0",
            messageVersion
          }
        })
      );
      setStatus({
        state: "success",
        message:
          body.message ??
          "Request received. AXIGNAL will review the B2G market, source coverage and controlled-trial fit."
      });
    } catch {
      setStatus({
        state: "error",
        message: "The controlled-trial endpoint is temporarily unavailable. No request was stored."
      });
    }
  }

  return (
    <form className="access-form" onSubmit={submit} noValidate data-testid="controlled-access-form">
      <div className="form-grid">
        <label>
          <span>Work email</span>
          <input name="email" type="email" autoComplete="email" required maxLength={254} />
        </label>
        <label>
          <span>Your role in the B2G decision</span>
          <select name="role" required defaultValue="">
            <option value="" disabled>
              Select the closest role
            </option>
            {roles.map((role) => (
              <option key={role}>{role}</option>
            ))}
          </select>
        </label>
        <label>
          <span>Company</span>
          <input name="company" type="text" autoComplete="organization" maxLength={120} />
        </label>
        <label className="form-wide">
          <span>What does your company sell to government, and which markets or tenders must you qualify?</span>
          <textarea
            name="useCase"
            rows={5}
            required
            minLength={20}
            maxLength={1200}
            placeholder="Describe your offer, target countries or public buyers, typical contract size and the current tender-workflow bottleneck."
          />
        </label>
      </div>

      <label className="consent-row">
        <input name="consent" type="checkbox" required />
        <span>
          I agree that AXIGNAL may use this information only to evaluate and respond to this controlled B2G
          trial request. See the Privacy notice.
        </span>
      </label>

      <label className="honeypot" aria-hidden="true">
        Website
        <input name="website" type="text" tabIndex={-1} autoComplete="off" />
      </label>

      <div className="form-actions">
        <button className="primary-button" type="submit" disabled={status.state === "submitting"}>
          {status.state === "submitting" ? "Sending…" : "Request 7-day B2G trial"}
        </button>
        <span className="form-note">No card, payment or subscription is created by this request.</span>
      </div>

      <div className="form-status" aria-live="polite" role="status">
        {status.state === "success" ? <p data-status="success">{status.message}</p> : null}
        {status.state === "error" ? (
          <p data-status="error">
            {status.message}
            {status.contactEmail ? (
              <>
                {" "}
                Contact <a href={`mailto:${status.contactEmail}`}>{status.contactEmail}</a>.
              </>
            ) : null}
          </p>
        ) : null}
      </div>
    </form>
  );
}
