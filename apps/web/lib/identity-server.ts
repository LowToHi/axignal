import { randomBytes } from "node:crypto";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const INSTALLATION_COOKIE = "axignal_installation";
const IDENTITY_SESSION_COOKIE =
  process.env.NODE_ENV === "production"
    ? "__Host-axignal_session"
    : "axignal_identity_session";

const ALLOWED: Record<string, ReadonlySet<string>> = {
  GET: new Set(["sessions/resolve", "trials/current"]),
  POST: new Set([
    "signup/start",
    "signup/verify",
    "passkeys/registration/options",
    "passkeys/registration/verify",
    "passkeys/authentication/options",
    "passkeys/authentication/verify",
    "recovery/start",
    "sessions/logout",
    "trials/step-up/test"
  ])
};

function cookieBase() {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/"
  };
}

export function identityRuntimeEnabled(): boolean {
  return ["1", "true", "yes", "on"].includes(
    (process.env.AXIGNAL_IDENTITY_RUNTIME_ENABLED ?? "").trim().toLowerCase()
  );
}

export function identitySessionCookieName(): string {
  return IDENTITY_SESSION_COOKIE;
}

export function identitySessionCookieOptions() {
  return {
    name: IDENTITY_SESSION_COOKIE,
    ...cookieBase(),
    maxAge: 24 * 60 * 60
  };
}

async function installationId(): Promise<{ value: string; fresh: boolean }> {
  const store = await cookies();
  const current = store.get(INSTALLATION_COOKIE)?.value;
  if (current && /^[A-Za-z0-9_-]{20,200}$/.test(current)) {
    return { value: current, fresh: false };
  }
  return { value: randomBytes(24).toString("base64url"), fresh: true };
}

export async function resolveIdentitySession(): Promise<Record<string, unknown> | null> {
  if (!identityRuntimeEnabled()) return null;
  const store = await cookies();
  const sessionToken = store.get(IDENTITY_SESSION_COOKIE)?.value;
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!sessionToken || !apiUrl) return null;
  try {
    const response = await fetch(`${apiUrl}/v1/identity/sessions/resolve`, {
      headers: { "X-AXIGNAL-Session-Token": sessionToken },
      cache: "no-store",
      signal: AbortSignal.timeout(5_000)
    });
    if (!response.ok) return null;
    const payload = await response.json();
    return payload && typeof payload === "object" ? payload : null;
  } catch {
    return null;
  }
}

export async function proxyIdentityRequest(
  request: Request,
  path: string
): Promise<NextResponse> {
  if (!identityRuntimeEnabled()) {
    return NextResponse.json(
      { error: "Passwordless identity is disabled." },
      { status: 503 }
    );
  }
  const method = request.method.toUpperCase();
  if (!ALLOWED[method]?.has(path)) {
    return NextResponse.json(
      { error: "Identity route is not allowed." },
      { status: 404 }
    );
  }
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!apiUrl) {
    return NextResponse.json(
      { error: "AXIGNAL_API_URL is required." },
      { status: 503 }
    );
  }
  const store = await cookies();
  const installation = await installationId();
  const sessionToken = store.get(IDENTITY_SESSION_COOKIE)?.value;
  const headers = new Headers();
  headers.set("content-type", "application/json");
  headers.set("X-AXIGNAL-Installation-ID", installation.value);
  if (sessionToken) headers.set("X-AXIGNAL-Session-Token", sessionToken);
  const body = method === "GET" ? undefined : await request.text();

  try {
    const init: RequestInit = {
      method,
      headers,
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
      ...(body !== undefined ? { body } : {})
    };
    const upstream = await fetch(`${apiUrl}/v1/identity/${path}`, init);
    const payload = (await upstream
      .json()
      .catch(() => ({ error: "Invalid API response." }))) as Record<
      string,
      unknown
    >;
    const issuedSession =
      typeof payload.session_token === "string" ? payload.session_token : null;
    if (issuedSession) delete payload.session_token;
    const response = NextResponse.json(payload, {
      status: upstream.status,
      headers: { "cache-control": "no-store" }
    });
    if (installation.fresh) {
      response.cookies.set({
        name: INSTALLATION_COOKIE,
        value: installation.value,
        ...cookieBase(),
        maxAge: 365 * 24 * 60 * 60
      });
    }
    if (issuedSession && upstream.ok) {
      response.cookies.set({
        ...identitySessionCookieOptions(),
        value: issuedSession
      });
    }
    if (path === "sessions/logout" && upstream.ok) {
      response.cookies.set({
        ...identitySessionCookieOptions(),
        value: "",
        maxAge: 0
      });
    }
    return response;
  } catch {
    return NextResponse.json(
      { error: "Identity API unavailable." },
      { status: 503 }
    );
  }
}
