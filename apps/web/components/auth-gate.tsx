"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

type Props = {
  passwordless?: boolean;
  turnstileSiteKey?: string;
  testRuntime?: boolean;
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
        }
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
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

function registrationPublicKey(
  value: RegistrationOptions
): PublicKeyCredentialCreationOptions {
  return {
    ...value,
    challenge: decode(value.challenge),
    user: { ...value.user, id: decode(value.user.id) },
    excludeCredentials: value.excludeCredentials?.map((item) => ({
      ...item,
      id: decode(item.id)
    }))
  } as unknown as PublicKeyCredentialCreationOptions;
}

function authenticationPublicKey(
  value: AuthenticationOptions
): PublicKeyCredentialRequestOptions {
  return {
    ...value,
    challenge: decode(value.challenge),
    allowCredentials: value.allowCredentials?.map((item) => ({
      ...item,
      id: decode(item.id)
    }))
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
      transports: response.getTransports?.() ?? []
    }
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
      userHandle: response.userHandle ? encode(response.userHandle) : null
    }
  };
}

async function post<T>(path: string, body: object): Promise<T> {
  const response = await fetch(`/api/identity/${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body)
  });
  const payload = (await response.json().catch(() => ({}))) as T & ApiError;
  if (!response.ok) {
    throw new Error(payload.detail ?? payload.error ?? "Identity operation failed.");
  }
  return payload;
}

function LegacyAuthGate() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [state, setState] = useState<"idle" | "submitting" | "error">("idle");
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state === "submitting") return;
    setState("submitting");
    setError("");
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (!response.ok) {
      const body = (await response.json().catch(() => null)) as ApiError | null;
      setError(body?.error ?? "No se pudo autenticar la identidad.");
      setState("error");
      return;
    }
    window.location.reload();
  }

  return (
    <main className="auth-shell">
      <section className="auth-card" aria-label="Acceso a AXIGNAL">
        <span className="auth-kicker">IDENTITY BOUNDARY</span>
        <h1>AXIGNAL</h1>
        <p>Autentícate para resolver el tenant en el servidor y abrir el InvestigationContext persistente.</p>
        <form onSubmit={submit}>
          <label>
            Email
            <input type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label>
            Contraseña
            <input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button type="submit" disabled={state === "submitting"}>{state === "submitting" ? "Verificando…" : "Entrar"}</button>
        </form>
        <small>La identidad del navegador no puede declarar ni cambiar el tenant.</small>
      </section>
    </main>
  );
}

export function AuthGate({ passwordless = false, turnstileSiteKey, testRuntime = false }: Props) {
  const [mode, setMode] = useState<"signup" | "login" | "recovery">("login");
  const [email, setEmail] = useState("");
  const [recoveryCode, setRecoveryCode] = useState("");
  const [botToken, setBotToken] = useState(testRuntime ? "axignal-test-bot-pass" : "");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [testToken, setTestToken] = useState<string | null>(null);
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const turnstileTarget = useRef<HTMLDivElement>(null);
  const consumedLink = useRef(false);

  useEffect(() => {
    if (!passwordless || testRuntime || !turnstileSiteKey || !turnstileTarget.current) return;
    const render = () => {
      if (!window.turnstile || !turnstileTarget.current) return;
      window.turnstile.render(turnstileTarget.current, {
        sitekey: turnstileSiteKey,
        callback: setBotToken,
        "expired-callback": () => setBotToken(""),
        "error-callback": () => setBotToken(""),
        appearance: "interaction-only"
      });
    };
    if (window.turnstile) {
      render();
      return;
    }
    const script = document.createElement("script");
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
    script.async = true;
    script.defer = true;
    script.onload = render;
    document.head.appendChild(script);
    return () => script.remove();
  }, [passwordless, testRuntime, turnstileSiteKey]);

  async function registerPasskey(registrationTicket: string) {
    if (!window.PublicKeyCredential || !navigator.credentials) {
      throw new Error("Este navegador no admite passkeys.");
    }
    const options = await post<RegistrationOptions>("passkeys/registration/options", {
      registration_ticket: registrationTicket
    });
    const credential = (await navigator.credentials.create({
      publicKey: registrationPublicKey(options)
    })) as PublicKeyCredential | null;
    if (!credential) throw new Error("No se creó la passkey.");
    const result = await post<{ recovery_codes?: string[] }>("passkeys/registration/verify", {
      registration_ticket: registrationTicket,
      challenge: options.challenge,
      credential: registrationCredential(credential)
    });
    setRecoveryCodes(result.recovery_codes ?? []);
    if ((result.recovery_codes ?? []).length === 0) window.location.assign("/");
  }

  async function verifyEmail(token: string) {
    setBusy(true);
    setError("");
    try {
      const result = await post<{ registration_ticket: string; decision: string }>("signup/verify", { token });
      setMessage(result.decision === "STEP_UP_REQUIRED" ? "Email verificado. La activación del trial requerirá una comprobación adicional." : "Email verificado. Crea una passkey para terminar.");
      await registerPasskey(result.registration_ticket);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo verificar el email.");
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

  if (!passwordless) return <LegacyAuthGate />;

  async function signup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (!botToken) throw new Error("Completa la comprobación de seguridad.");
      const result = await post<{ accepted: true; test_verification_token?: string }>("signup/start", { email, bot_token: botToken });
      setTestToken(result.test_verification_token ?? null);
      setMessage("Si la dirección puede utilizarse, recibirás un enlace de verificación.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo iniciar el alta.");
    } finally {
      setBusy(false);
    }
  }

  async function login() {
    setBusy(true);
    setError("");
    try {
      if (!botToken) throw new Error("Completa la comprobación de seguridad.");
      const options = await post<AuthenticationOptions>("passkeys/authentication/options", { bot_token: botToken });
      const credential = (await navigator.credentials.get({
        publicKey: authenticationPublicKey(options),
        mediation: "optional"
      })) as PublicKeyCredential | null;
      if (!credential) throw new Error("No se seleccionó una passkey.");
      await post("passkeys/authentication/verify", {
        challenge: options.challenge,
        credential: authenticationCredential(credential)
      });
      window.location.assign("/");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo iniciar sesión.");
    } finally {
      setBusy(false);
    }
  }

  async function recover(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (!botToken) throw new Error("Completa la comprobación de seguridad.");
      const result = await post<{ recovery_ticket: string }>("recovery/start", {
        email,
        recovery_code: recoveryCode,
        bot_token: botToken
      });
      await registerPasskey(result.recovery_ticket);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo recuperar la cuenta.");
    } finally {
      setBusy(false);
    }
  }

  if (recoveryCodes.length > 0) {
    return (
      <main className="auth-shell">
        <section className="auth-card" aria-label="Códigos de recuperación AXIGNAL">
          <span className="auth-kicker">RECOVERY BOUNDARY</span>
          <h1>Guarda tus códigos</h1>
          <p>Cada código es de un solo uso. AXIGNAL no volverá a mostrarlos.</p>
          <pre>{recoveryCodes.join("\n")}</pre>
          <button type="button" onClick={() => window.location.assign("/")}>He guardado los códigos</button>
        </section>
      </main>
    );
  }

  return (
    <main className="auth-shell">
      <section className="auth-card" aria-label="Acceso seguro a AXIGNAL">
        <span className="auth-kicker">PASSWORDLESS · PHISHING-RESISTANT</span>
        <h1>AXIGNAL</h1>
        <p>Accede con una passkey. El tenant y los permisos se resuelven siempre en el servidor.</p>

        <div role="tablist" aria-label="Método de acceso">
          <button type="button" role="tab" aria-selected={mode === "login"} onClick={() => setMode("login")}>Entrar</button>
          <button type="button" role="tab" aria-selected={mode === "signup"} onClick={() => setMode("signup")}>Crear cuenta</button>
          <button type="button" role="tab" aria-selected={mode === "recovery"} onClick={() => setMode("recovery")}>Recuperar</button>
        </div>

        {mode === "login" && (
          <button type="button" disabled={busy} onClick={() => void login()}>{busy ? "Verificando…" : "Usar passkey"}</button>
        )}

        {mode === "signup" && (
          <form onSubmit={signup}>
            <label>
              Email profesional
              <input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            </label>
            <button type="submit" disabled={busy}>{busy ? "Enviando…" : "Continuar"}</button>
          </form>
        )}

        {mode === "recovery" && (
          <form onSubmit={recover}>
            <label>
              Email
              <input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            </label>
            <label>
              Código de recuperación
              <input type="text" autoComplete="one-time-code" value={recoveryCode} onChange={(event) => setRecoveryCode(event.target.value)} required />
            </label>
            <button type="submit" disabled={busy}>{busy ? "Verificando…" : "Crear una passkey nueva"}</button>
          </form>
        )}

        <div ref={turnstileTarget} aria-label="Comprobación anti-bot adaptativa" />
        {message && <p role="status">{message}</p>}
        {testToken && (
          <button type="button" disabled={busy} onClick={() => void verifyEmail(testToken)}>Verificar email de prueba y crear passkey</button>
        )}
        {error && <p className="auth-error" role="alert">{error}</p>}
        <small>Email verifica la dirección; la passkey autentica. Crear otra cuenta no concede otro trial.</small>
      </section>
    </main>
  );
}
