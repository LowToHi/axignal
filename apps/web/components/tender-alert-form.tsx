"use client";

import Script from "next/script";
import { FormEvent, useEffect, useRef, useState } from "react";

type AlertState = "idle" | "submitting" | "accepted" | "error";

type TurnstileApi = {
  render: (
    container: HTMLElement,
    options: {
      sitekey: string;
      action: string;
      theme: "dark" | "light";
      callback: (token: string) => void;
      "error-callback": () => void;
      "expired-callback": () => void;
    }
  ) => string;
  reset: (widgetId?: string) => void;
  remove: (widgetId: string) => void;
};

declare global {
  interface Window {
    turnstile?: TurnstileApi;
  }
}

export function TenderAlertForm({
  countryCode,
  sectorSlug,
  sourcePath,
  turnstileSiteKey,
  testRuntime = false
}: {
  countryCode: string;
  sectorSlug: string;
  sourcePath: string;
  turnstileSiteKey?: string;
  testRuntime?: boolean;
}) {
  const [state, setState] = useState<AlertState>("idle");
  const [message, setMessage] = useState("");
  const [botToken, setBotToken] = useState("");
  const [scriptReady, setScriptReady] = useState(false);
  const widgetContainer = useRef<HTMLDivElement | null>(null);
  const widgetId = useRef<string | null>(null);

  useEffect(() => {
    if (
      testRuntime ||
      !turnstileSiteKey ||
      !scriptReady ||
      !widgetContainer.current ||
      !window.turnstile ||
      widgetId.current
    ) {
      return;
    }
    widgetId.current = window.turnstile.render(widgetContainer.current, {
      sitekey: turnstileSiteKey,
      action: "tender_alert_signup",
      theme: "dark",
      callback: (token) => {
        setBotToken(token);
        setMessage("");
      },
      "error-callback": () => {
        setBotToken("");
        setState("error");
        setMessage("Bot verification is unavailable.");
      },
      "expired-callback": () => setBotToken("")
    });
    return () => {
      if (widgetId.current && window.turnstile) {
        window.turnstile.remove(widgetId.current);
      }
      widgetId.current = null;
    };
  }, [scriptReady, testRuntime, turnstileSiteKey]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const cadence = String(form.get("cadence") ?? "DAILY");
    const effectiveBotToken = testRuntime
      ? "axignal-test-bot-pass"
      : botToken;
    if (!effectiveBotToken) {
      setState("error");
      setMessage("Complete the verification before creating the alert.");
      return;
    }
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
        bot_token: effectiveBotToken
      })
    });
    const body = (await response.json().catch(() => ({}))) as Record<
      string,
      unknown
    >;
    if (!response.ok) {
      setState("error");
      setMessage(
        "The alert could not be prepared. No account or trial was created."
      );
      if (widgetId.current && window.turnstile) {
        window.turnstile.reset(widgetId.current);
        setBotToken("");
      }
      return;
    }
    setState("accepted");
    setMessage(
      typeof body.message === "string"
        ? body.message
        : "Check your email to confirm the alert."
    );
    event.currentTarget.reset();
    if (widgetId.current && window.turnstile) {
      window.turnstile.reset(widgetId.current);
      setBotToken("");
    }
  }

  const missingProductionProvider = !testRuntime && !turnstileSiteKey;

  return (
    <>
      {!testRuntime && turnstileSiteKey && (
        <Script
          src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"
          strategy="afterInteractive"
          onLoad={() => setScriptReady(true)}
        />
      )}
      <form
        className="tender-alert-form"
        onSubmit={submit}
        aria-label="Tender alert subscription"
      >
        <div>
          <span>TENDER ALERT</span>
          <strong>Receive new matching opportunities.</strong>
          <small>
            Double opt-in. An alert does not create an AXIGNAL account, tenant
            or trial.
          </small>
        </div>
        <label>
          <span>Professional email</span>
          <input
            name="email"
            type="email"
            required
            autoComplete="email"
            placeholder="you@company.com"
          />
        </label>
        <label>
          <span>Cadence</span>
          <select name="cadence" defaultValue="DAILY">
            <option value="IMMEDIATE">Immediate</option>
            <option value="DAILY">Daily digest</option>
            <option value="WEEKLY">Weekly digest</option>
          </select>
        </label>
        {!testRuntime && turnstileSiteKey && (
          <div
            className="tender-alert-turnstile"
            ref={widgetContainer}
            aria-label="Bot verification"
          />
        )}
        <button
          type="submit"
          disabled={
            state === "submitting" ||
            missingProductionProvider ||
            (!testRuntime && !botToken)
          }
        >
          {state === "submitting" ? "Preparing…" : "Create tender alert"}
        </button>
        {missingProductionProvider && (
          <p role="status" data-state="error">
            Alert capture is not configured on this environment.
          </p>
        )}
        {message && (
          <p role="status" data-state={state}>
            {message}
          </p>
        )}
      </form>
    </>
  );
}
