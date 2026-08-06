"use client";

import { FormEvent, useRef, useState } from "react";
import { trackLandingEvent } from "@/lib/analytics";
import { AXIGNAL_TRIAL_INTAKE } from "@/lib/canonical-commercial-contract";
import type { LandingMessages, Locale } from "@/lib/i18n";

type FormStatus =
  | { state: "idle" }
  | { state: "submitting" }
  | { state: "success"; message: string }
  | { state: "error"; message: string; contactEmail?: string };

type PilotAccessFormProps = {
  locale: Locale;
  messages: LandingMessages["form"];
  selectedPlan: string;
};

function newIdempotencyKey() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `landing-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function canonicalSelectedPlan(selectedPlan: string) {
  return selectedPlan === "Design Partner" ? "Controlled Trial" : selectedPlan;
}

export function PilotAccessForm({ locale, messages: m, selectedPlan }: PilotAccessFormProps) {
  const [step, setStep] = useState<1 | 2>(1);
  const [status, setStatus] = useState<FormStatus>({ state: "idle" });
  const [validationMessage, setValidationMessage] = useState("");
  const idempotencyKey = useRef(newIdempotencyKey());

  const advance = (form: HTMLFormElement) => {
    const required = ["email", "organisation", "role"]
      .map((name) => form.elements.namedItem(name))
      .filter((field): field is HTMLInputElement | HTMLSelectElement => field instanceof HTMLElement);
    const valid = required.every((field) => field.reportValidity());
    if (!valid) {
      setValidationMessage(m.required);
      return;
    }
    setValidationMessage("");
    setStep(2);
    trackLandingEvent("intake_step_complete", { locale });
    requestAnimationFrame(() => document.getElementById("intake-fit-heading")?.focus());
  };

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;

    if (step === 1) {
      advance(form);
      return;
    }
    if (!form.reportValidity()) {
      setValidationMessage(m.required);
      return;
    }

    setValidationMessage("");
    setStatus({ state: "submitting" });
    const formData = new FormData(form);
    const params = new URLSearchParams(window.location.search);
    const plan = canonicalSelectedPlan(selectedPlan);
    const payload = {
      schema: AXIGNAL_TRIAL_INTAKE.schema,
      source: AXIGNAL_TRIAL_INTAKE.source,
      messageVersion: AXIGNAL_TRIAL_INTAKE.messageVersion,
      idempotencyKey: idempotencyKey.current,
      email: String(formData.get("email") ?? ""),
      company: String(formData.get("organisation") ?? ""),
      role: String(formData.get("role") ?? ""),
      targetMarkets: String(formData.get("countries") ?? ""),
      monthlyVolume: Number(formData.get("monthlyVolume") ?? 0),
      currentProcess: String(formData.get("currentProcess") ?? ""),
      governmentOffer: String(formData.get("useCase") ?? ""),
      qualificationBottleneck: String(formData.get("expensiveProblem") ?? ""),
      timeframe: String(formData.get("timeframe") ?? ""),
      consent: formData.get("consent") === "on",
      website: String(formData.get("website") ?? ""),
      system: {
        locale,
        utmSource: params.get("utm_source") ?? "",
        utmMedium: params.get("utm_medium") ?? "",
        utmCampaign: params.get("utm_campaign") ?? "",
        landingVariant: "b2g_opportunity_v1_0",
        referrer: document.referrer,
        selectedPlan: plan,
        ctaOrigin: plan === "Controlled Trial" ? "direct" : "pricing",
        clientTimestamp: new Date().toISOString(),
        consentVersion: AXIGNAL_TRIAL_INTAKE.consentVersion
      }
    };

    try {
      const response = await fetch("/api/pilot-intake", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "idempotency-key": idempotencyKey.current
        },
        body: JSON.stringify(payload)
      });
      const body = (await response.json()) as {
        status?: string;
        message?: string;
        contactEmail?: string;
      };

      if (!response.ok) {
        const result =
          response.status === 429 ? "rate_limited" : response.status >= 500 ? "unavailable" : "rejected";
        trackLandingEvent("intake_submit_result", { locale, result });
        setStatus({
          state: "error",
          message: body.message ?? m.error,
          ...(body.contactEmail ? { contactEmail: body.contactEmail } : {})
        });
        return;
      }

      form.reset();
      idempotencyKey.current = newIdempotencyKey();
      setStep(1);
      trackLandingEvent("intake_submit_result", { locale, result: "accepted" });
      setStatus({ state: "success", message: body.message ?? m.success });
    } catch {
      trackLandingEvent("intake_submit_result", { locale, result: "unavailable" });
      setStatus({ state: "error", message: m.error });
    }
  }

  return (
    <form className="access-form" onSubmit={submit} noValidate>
      <div className="form-progress" aria-label={`${m.step} ${step} ${m.of} 2`}>
        <span>{m.step} {step} {m.of} 2</span>
        <i style={{ transform: `scaleX(${step / 2})` }} />
      </div>

      <fieldset hidden={step !== 1}>
        <legend>{m.identity}</legend>
        <div className="form-grid">
          <label>
            <span>{m.email}</span>
            <input name="email" type="email" autoComplete="email" required maxLength={254} />
          </label>
          <label>
            <span>{m.organisation}</span>
            <input name="organisation" type="text" autoComplete="organization" required minLength={2} maxLength={120} />
          </label>
          <label className="form-wide">
            <span>{m.role}</span>
            <select name="role" required defaultValue="">
              <option value="" disabled>{m.rolePlaceholder}</option>
              {m.roles.map((role) => <option key={role} value={role}>{role}</option>)}
            </select>
          </label>
        </div>
      </fieldset>

      <fieldset hidden={step !== 2}>
        <legend id="intake-fit-heading" tabIndex={-1}>{m.fit}</legend>
        <div className="form-grid">
          <label>
            <span>{m.countries}</span>
            <input name="countries" type="text" required minLength={2} maxLength={180} />
          </label>
          <label>
            <span>{m.volume}</span>
            <input name="monthlyVolume" type="number" min="1" max="10000" required inputMode="numeric" />
          </label>
          <label className="form-wide">
            <span>{m.process}</span>
            <textarea name="currentProcess" rows={3} required minLength={10} maxLength={600} />
          </label>
          <label className="form-wide">
            <span>{m.useCase}</span>
            <textarea name="useCase" rows={3} required minLength={20} maxLength={800} />
          </label>
          <label className="form-wide">
            <span>{m.problem}</span>
            <textarea name="expensiveProblem" rows={3} required minLength={20} maxLength={800} />
          </label>
          <label className="form-wide">
            <span>{m.timeframe}</span>
            <select name="timeframe" required defaultValue="">
              <option value="" disabled>{m.rolePlaceholder}</option>
              {m.timeframes.map((timeframe) => <option key={timeframe} value={timeframe}>{timeframe}</option>)}
            </select>
          </label>
        </div>

        <label className="consent-row">
          <input name="consent" type="checkbox" required />
          <span>{m.consent}</span>
        </label>
      </fieldset>

      <label className="honeypot" aria-hidden="true">
        Website
        <input name="website" type="text" tabIndex={-1} autoComplete="off" />
      </label>

      <div className="form-actions">
        {step === 2 ? (
          <button className="button button-ghost" type="button" onClick={() => setStep(1)}>{m.back}</button>
        ) : null}
        <button className="button" type="submit" disabled={status.state === "submitting"}>
          {step === 1 ? m.next : status.state === "submitting" ? m.sending : m.submit}
        </button>
      </div>
      <p className="form-note">{m.privacy}</p>

      <div className="form-status" aria-live="polite" role="status">
        {validationMessage ? <p data-status="error">{validationMessage}</p> : null}
        {status.state === "success" ? <p data-status="success">{status.message}</p> : null}
        {status.state === "error" ? (
          <p data-status="error">
            {status.message}
            {status.contactEmail ? <> <a href={`mailto:${status.contactEmail}`}>{status.contactEmail}</a></> : null}
          </p>
        ) : null}
      </div>
    </form>
  );
}
