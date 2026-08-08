"use client";

import Image from "next/image";
import {
  ArrowRight,
  Check,
  KeyRound,
  LockKeyhole,
  Mail,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";

import {
  authCopy,
  humanizeAuthError,
} from "./auth-localization";
import type { AuthCopy, AuthMode } from "./auth-localization";
import type { ShellLocale } from "./subscriber/subscriber-localization";

type Props = {
  passwordless?: boolean;
  turnstileSiteKey?: string;
  testRuntime?: boolean;
  locale?: ShellLocale;
};

type ApiError = { error?: string; detail?: string };
type RegistrationOptions = PublicKeyCredentialCreationOptionsJSON & {
  challenge: string;
};
type AuthenticationOptions = PublicKeyCredentialRequestOptionsJSON & {
  challenge: string;
};

declare global {
  interface Window {
    turnstile?: {
      render: (
        target: HTMLElement,
        options: {
          sitekey: string;
          callback: (token: string) => void;
          "expired-callback": () => void;
          "error-callback": () => void;
          appearance: "interaction-only";
        },
      ) => string;
      reset: (widgetId?: string) => void;
    };
  }
}

function decode(value: string): ArrayBuffer {
  const base64 = value.replaceAll("-", "+").replaceAll("_", "/");
  const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
  const binary = atob(padded);
  return Uint8Array.from(binary, (character) => character.charCodeAt(0)).buffer;
}

function encode(value: ArrayBuffer): string {
  const bytes = new Uint8Array(value);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary)
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
}

function registrationPublicKey(
  value: RegistrationOptions,
): PublicKeyCredentialCreationOptions {
  return {
    ...value,
    challenge: decode(value.challenge),
    user: { ...value.user, id: decode(value.user.id) },
    excludeCredentials: value.excludeCredentials?.map((item) => ({
      ...item,
      id: decode(item.id),
    })),
  } as unknown as PublicKeyCredentialCreationOptions;
}

function authenticationPublicKey(
  value: AuthenticationOptions,
): PublicKeyCredentialRequestOptions {
  return {
    ...value,
    challenge: decode(value.challenge),
    allowCredentials: value.allowCredentials?.map((item) => ({
      ...item,
      id: decode(item.id),
    })),
  } as unknown as PublicKeyCredentialRequestOptions;
}

function registrationCredential(value: PublicKeyCredential) {
  const response = value.response as AuthenticatorAttestationResponse;
  return {
    id: value.id,
    rawId: encode(value.rawId),
    type: value.type,
    authenticatorAttachment: value.authenticatorAttachment,
    clientExtensionResults: value.getClientExtensionResults(),
    response: {
      clientDataJSON: encode(response.clientDataJSON),
      attestationObject: encode(response.attestationObject),
      transports: response.getTransports?.() ?? [],
    },
  };
}

function authenticationCredential(value: PublicKeyCredential) {
  const response = value.response as AuthenticatorAssertionResponse;
  return {
    id: value.id,
    rawId: encode(value.rawId),
    type: value.type,
    authenticatorAttachment: value.authenticatorAttachment,
    clientExtensionResults: value.getClientExtensionResults(),
    response: {
      clientDataJSON: encode(response.clientDataJSON),
      authenticatorData: encode(response.authenticatorData),
      signature: encode(response.signature),
      userHandle: response.userHandle ? encode(response.userHandle) : null,
    },
  };
}

async function post<T>(path: string, body: object): Promise<T> {
  const response = await fetch(`/api/identity/${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = (await response.json().catch(() => ({}))) as T & ApiError;
  if (!response.ok) {
    throw new Error(
      payload.detail ?? payload.error ?? "Identity operation failed.",
    );
  }
  return payload;
}

function AuthFrame({
  copy,
  children,
}: {
  copy: AuthCopy;
  children: ReactNode;
}) {
  return (
    <main className="auth-shell">
      <div className="auth-ambient auth-ambient--one" aria-hidden="true" />
      <div className="auth-ambient auth-ambient--two" aria-hidden="true" />
      <div className="auth-grid" aria-hidden="true" />

      <header className="auth-header">
        <a
          className="auth-logo-link"
          href="https://axignal.com"
          aria-label="AXIGNAL"
        >
          <Image
            src="/brand/axignal-logo-dark.svg"
            alt="AXIGNAL"
            width={202}
            height={43}
            priority
          />
        </a>
        <span className="auth-workspace-label">
          <LockKeyhole aria-hidden="true" size={14} strokeWidth={1.8} />
          {copy.workspaceLabel}
        </span>
      </header>

      <div className="auth-layout">
        <section className="auth-story" aria-labelledby="auth-story-title">
          <span className="auth-eyebrow">{copy.eyebrow}</span>
          <h1 id="auth-story-title">
            {copy.heroLine1}
            <span>{copy.heroLine2}</span>
          </h1>
          <p>{copy.heroBody}</p>

          <ul className="auth-trust-list">
            {copy.trustItems.map((item) => (
              <li key={item}>
                <span>
                  <Check aria-hidden="true" size={14} strokeWidth={2.2} />
                </span>
                {item}
              </li>
            ))}
          </ul>

          <div className="auth-orbit" aria-hidden="true">
            <div className="auth-orbit__ring auth-orbit__ring--outer" />
            <div className="auth-orbit__ring auth-orbit__ring--inner" />
            <div className="auth-orbit__core">
              <Sparkles size={22} strokeWidth={1.5} />
            </div>
            <i className="auth-orbit__signal auth-orbit__signal--one" />
            <i className="auth-orbit__signal auth-orbit__signal--two" />
            <i className="auth-orbit__signal auth-orbit__signal--three" />
            <span className="auth-orbit__trace auth-orbit__trace--one" />
            <span className="auth-orbit__trace auth-orbit__trace--two" />
          </div>

          <span className="auth-pilot-label">
            <i aria-hidden="true" />
            {copy.pilotLabel}
          </span>
        </section>

        <section className="auth-panel" aria-label={copy.cardTitle}>
          {children}
        </section>
      </div>

      <footer className="auth-page-footer">
        <span>AXIGNAL</span>
        <span>{copy.pageFooter}</span>
      </footer>
    </main>
  );
}

function Feedback({
  kind,
  title,
  body,
  hint,
}: {
  kind: "error" | "status";
  title: string;
  body: string;
  hint?: string;
}) {
  return (
    <div
      className={`auth-feedback auth-feedback--${kind}`}
      role={kind === "error" ? "alert" : "status"}
    >
      <span className="auth-feedback__icon" aria-hidden="true">
        {kind === "error" ? (
          <RefreshCw size={17} strokeWidth={1.9} />
        ) : (
          <Mail size={17} strokeWidth={1.9} />
        )}
      </span>
      <div>
        <strong>{title}</strong>
        <p>{body}</p>
        {hint && <small>{hint}</small>}
      </div>
    </div>
  );
}

function LegacyAuthGate({
  locale,
  copy,
}: {
  locale: ShellLocale;
  copy: AuthCopy;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [state, setState] = useState<"idle" | "submitting" | "error">(
    "idle",
  );
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state === "submitting") return;
    setState("submitting");
    setError("");
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) {
        const body = (await response
          .json()
          .catch(() => null)) as ApiError | null;
        throw new Error(body?.error ?? copy.loginFailed);
      }
      window.location.reload();
    } catch (cause) {
      setError(humanizeAuthError(locale, cause, "loginFailed"));
      setState("error");
    }
  }

  return (
    <AuthFrame copy={copy}>
      <div className="auth-card">
        <div className="auth-card__heading">
          <span className="auth-card__icon">
            <ShieldCheck aria-hidden="true" size={22} strokeWidth={1.7} />
          </span>
          <div>
            <span className="auth-kicker">{copy.legacyKicker}</span>
            <h2>{copy.legacyTitle}</h2>
          </div>
        </div>
        <p className="auth-card__intro">{copy.legacyBody}</p>

        <form className="auth-form" onSubmit={submit}>
          <label>
            <span>{copy.signupEmail}</span>
            <input
              type="email"
              autoComplete="username"
              placeholder={copy.emailPlaceholder}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label>
            <span>{copy.legacyPassword}</span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          <button
            className="auth-primary"
            type="submit"
            disabled={state === "submitting"}
          >
            <span>
              {state === "submitting"
                ? copy.legacySubmitting
                : copy.legacySubmit}
            </span>
            <ArrowRight aria-hidden="true" size={17} />
          </button>
        </form>

        {error && (
          <Feedback
            kind="error"
            title={copy.errorTitle}
            body={error}
            hint={copy.retryHint}
          />
        )}
        <p className="auth-card__footer">{copy.legacyFooter}</p>
      </div>
    </AuthFrame>
  );
}

export function AuthGate({
  passwordless = false,
  turnstileSiteKey,
  testRuntime = false,
  locale = "en",
}: Props) {
  const copy = authCopy[locale];
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [recoveryCode, setRecoveryCode] = useState("");
  const [botToken, setBotToken] = useState(
    testRuntime ? "axignal-test-bot-pass" : "",
  );
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [testToken, setTestToken] = useState<string | null>(null);
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const turnstileTarget = useRef<HTMLDivElement>(null);
  const consumedLink = useRef(false);

  useEffect(() => {
    if (
      !passwordless ||
      testRuntime ||
      !turnstileSiteKey ||
      !turnstileTarget.current
    ) {
      return;
    }
    const render = () => {
      if (!window.turnstile || !turnstileTarget.current) return;
      window.turnstile.render(turnstileTarget.current, {
        sitekey: turnstileSiteKey,
        callback: setBotToken,
        "expired-callback": () => setBotToken(""),
        "error-callback": () => setBotToken(""),
        appearance: "interaction-only",
      });
    };
    if (window.turnstile) {
      render();
      return;
    }
    const script = document.createElement("script");
    script.src =
      "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
    script.async = true;
    script.defer = true;
    script.onload = render;
    document.head.appendChild(script);
    return () => script.remove();
  }, [passwordless, testRuntime, turnstileSiteKey]);

  function changeMode(nextMode: AuthMode) {
    setMode(nextMode);
    setMessage("");
    setError("");
    setTestToken(null);
  }

  async function registerPasskey(registrationTicket: string) {
    if (!window.PublicKeyCredential || !navigator.credentials) {
      throw new Error(copy.browserUnsupported);
    }
    const options = await post<RegistrationOptions>(
      "passkeys/registration/options",
      {
        registration_ticket: registrationTicket,
      },
    );
    const credential = (await navigator.credentials.create({
      publicKey: registrationPublicKey(options),
    })) as PublicKeyCredential | null;
    if (!credential) throw new DOMException("", "NotAllowedError");
    const result = await post<{ recovery_codes?: string[] }>(
      "passkeys/registration/verify",
      {
        registration_ticket: registrationTicket,
        challenge: options.challenge,
        credential: registrationCredential(credential),
      },
    );
    setRecoveryCodes(result.recovery_codes ?? []);
    if ((result.recovery_codes ?? []).length === 0) {
      window.location.assign("/");
    }
  }

  async function verifyEmail(token: string) {
    setBusy(true);
    setError("");
    try {
      const result = await post<{
        registration_ticket: string;
        decision: string;
      }>("signup/verify", { token });
      setMessage(
        result.decision === "STEP_UP_REQUIRED"
          ? copy.emailVerifiedStepUp
          : copy.emailVerified,
      );
      await registerPasskey(result.registration_ticket);
    } catch (cause) {
      setError(
        humanizeAuthError(
          locale,
          cause,
          "verifyEmailFailed",
          "registration",
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!passwordless || consumedLink.current) return;
    const token = new URLSearchParams(window.location.search).get("verify");
    if (!token) return;
    consumedLink.current = true;
    window.history.replaceState({}, "", window.location.pathname);
    void verifyEmail(token);
  }, [passwordless]);

  if (!passwordless) {
    return <LegacyAuthGate locale={locale} copy={copy} />;
  }

  async function signup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (!botToken) throw new Error(copy.completeSecurity);
      const result = await post<{
        accepted: true;
        test_verification_token?: string;
      }>("signup/start", { email, bot_token: botToken });
      setTestToken(result.test_verification_token ?? null);
      setMessage(copy.statusEmailSent);
    } catch (cause) {
      setError(humanizeAuthError(locale, cause, "signupFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function login() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (!botToken) throw new Error(copy.completeSecurity);
      const options = await post<AuthenticationOptions>(
        "passkeys/authentication/options",
        { bot_token: botToken },
      );
      const credential = (await navigator.credentials.get({
        publicKey: authenticationPublicKey(options),
        mediation: "optional",
      })) as PublicKeyCredential | null;
      if (!credential) throw new DOMException("", "NotAllowedError");
      await post("passkeys/authentication/verify", {
        challenge: options.challenge,
        credential: authenticationCredential(credential),
      });
      window.location.assign("/");
    } catch (cause) {
      setError(
        humanizeAuthError(
          locale,
          cause,
          "loginFailed",
          "authentication",
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  async function recover(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (!botToken) throw new Error(copy.completeSecurity);
      const result = await post<{ recovery_ticket: string }>(
        "recovery/start",
        {
          email,
          recovery_code: recoveryCode,
          bot_token: botToken,
        },
      );
      await registerPasskey(result.recovery_ticket);
    } catch (cause) {
      setError(
        humanizeAuthError(
          locale,
          cause,
          "recoveryFailed",
          "registration",
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  if (recoveryCodes.length > 0) {
    return (
      <AuthFrame copy={copy}>
        <div className="auth-card auth-card--codes">
          <div className="auth-card__heading">
            <span className="auth-card__icon">
              <KeyRound aria-hidden="true" size={22} strokeWidth={1.7} />
            </span>
            <div>
              <span className="auth-kicker">{copy.saveCodesKicker}</span>
              <h2>{copy.saveCodesTitle}</h2>
            </div>
          </div>
          <p className="auth-card__intro">{copy.saveCodesBody}</p>
          <pre className="auth-recovery-codes">{recoveryCodes.join("\n")}</pre>
          <button
            className="auth-primary"
            type="button"
            onClick={() => window.location.assign("/")}
          >
            <span>{copy.codesSaved}</span>
            <ArrowRight aria-hidden="true" size={17} />
          </button>
        </div>
      </AuthFrame>
    );
  }

  return (
    <AuthFrame copy={copy}>
      <div className="auth-card">
        <div className="auth-card__heading">
          <span className="auth-card__icon">
            <KeyRound aria-hidden="true" size={22} strokeWidth={1.7} />
          </span>
          <div>
            <span className="auth-kicker">{copy.cardKicker}</span>
            <h2>{copy.cardTitle}</h2>
          </div>
        </div>
        <p className="auth-card__intro">{copy.cardBody}</p>

        <div
          className="auth-tabs"
          role="tablist"
          aria-label={copy.cardKicker}
        >
          {(["login", "signup", "recovery"] as const).map((item) => (
            <button
              key={item}
              type="button"
              role="tab"
              aria-selected={mode === item}
              tabIndex={mode === item ? 0 : -1}
              onClick={() => changeMode(item)}
            >
              {copy.tabs[item]}
            </button>
          ))}
        </div>

        <div className="auth-mode-panel" role="tabpanel">
          {mode === "login" && (
            <div className="auth-login-action">
              <button
                className="auth-primary auth-primary--passkey"
                type="button"
                disabled={busy}
                onClick={() => void login()}
              >
                <span className="auth-primary__icon">
                  <KeyRound aria-hidden="true" size={18} strokeWidth={1.8} />
                </span>
                <span>{busy ? copy.loginBusy : copy.loginButton}</span>
                {!busy && <ArrowRight aria-hidden="true" size={17} />}
              </button>
              <p className="auth-inline-hint">
                <ShieldCheck aria-hidden="true" size={15} />
                {copy.loginHint}
              </p>
            </div>
          )}

          {mode === "signup" && (
            <form className="auth-form" onSubmit={signup}>
              <label>
                <span>{copy.signupEmail}</span>
                <input
                  type="email"
                  autoComplete="email"
                  placeholder={copy.emailPlaceholder}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </label>
              <button className="auth-primary" type="submit" disabled={busy}>
                <span>{busy ? copy.sending : copy.continue}</span>
                {!busy && <ArrowRight aria-hidden="true" size={17} />}
              </button>
            </form>
          )}

          {mode === "recovery" && (
            <form className="auth-form" onSubmit={recover}>
              <label>
                <span>{copy.recoveryEmail}</span>
                <input
                  type="email"
                  autoComplete="email"
                  placeholder={copy.emailPlaceholder}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </label>
              <label>
                <span>{copy.recoveryCode}</span>
                <input
                  type="text"
                  autoComplete="one-time-code"
                  placeholder={copy.recoveryPlaceholder}
                  value={recoveryCode}
                  onChange={(event) => setRecoveryCode(event.target.value)}
                  required
                />
              </label>
              <button className="auth-primary" type="submit" disabled={busy}>
                <span>{busy ? copy.verifying : copy.createPasskey}</span>
                {!busy && <ArrowRight aria-hidden="true" size={17} />}
              </button>
            </form>
          )}
        </div>

        <div
          className="auth-turnstile"
          ref={turnstileTarget}
          aria-label={copy.securityCheck}
        />

        {message && (
          <Feedback
            kind="status"
            title={copy.statusTitle}
            body={message}
          />
        )}
        {testToken && (
          <button
            className="auth-secondary"
            type="button"
            disabled={busy}
            onClick={() => void verifyEmail(testToken)}
          >
            {copy.testVerify}
          </button>
        )}
        {error && (
          <Feedback
            kind="error"
            title={copy.errorTitle}
            body={error}
            hint={copy.retryHint}
          />
        )}

        <p className="auth-card__footer">
          <ShieldCheck aria-hidden="true" size={14} strokeWidth={1.7} />
          {copy.footer}
        </p>
      </div>
    </AuthFrame>
  );
}
