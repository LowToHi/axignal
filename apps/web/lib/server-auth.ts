import { createHmac, scryptSync, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

import { identityRuntimeEnabled, resolveIdentitySession } from "./identity-server";

const SESSION_COOKIE = "axignal_session";
const SESSION_VERSION = "v1";
const SESSION_TTL_SECONDS = 60 * 60 * 8;
const ASSERTION_TTL_SECONDS = 60;

export type AuthenticatedIdentity = {
  subject: string;
  email: string;
  tenantId: string;
  userId?: string;
  sessionId?: string;
  membershipId?: string | null;
  roles?: string[];
  authMethod?: string;
  assuranceLevel?: string;
  authenticatedAt?: string;
  stepUpValidUntil?: string | null;
  absoluteExpiresAt?: string;
};

type SessionClaims = {
  sub: string;
  email: string;
  iat: number;
  exp: number;
};

function boolEnv(name: string): boolean {
  return ["1", "true", "yes", "on"].includes(
    (process.env[name] ?? "").trim().toLowerCase()
  );
}

function requiredEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`${name} is required`);
  return value;
}

function encode(value: Buffer | string): string {
  return Buffer.from(value).toString("base64url");
}

function decode(value: string): Buffer {
  return Buffer.from(value, "base64url");
}

function sign(version: string, payload: string, secret: string): string {
  return createHmac("sha256", secret)
    .update(`${version}.${payload}`)
    .digest("base64url");
}

function equalText(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  return (
    leftBuffer.length === rightBuffer.length &&
    timingSafeEqual(leftBuffer, rightBuffer)
  );
}

function createSignedToken(payload: object, secret: string): string {
  const encodedPayload = encode(JSON.stringify(payload));
  return `${SESSION_VERSION}.${encodedPayload}.${sign(
    SESSION_VERSION,
    encodedPayload,
    secret
  )}`;
}

function verifySignedToken<T>(token: string, secret: string): T | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const version = parts[0];
  const payload = parts[1];
  const signature = parts[2];
  if (!version || !payload || !signature || version !== SESSION_VERSION) return null;
  if (!equalText(signature, sign(version, payload, secret))) return null;
  try {
    return JSON.parse(decode(payload).toString("utf8")) as T;
  } catch {
    return null;
  }
}

function validUuid(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      value
    )
  );
}

function text(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

export function isPersistentResearchUiEnabled(): boolean {
  return boolEnv("AXIGNAL_PERSISTENT_RESEARCH_UI_ENABLED");
}

export function isValidationUiEnabled(): boolean {
  return boolEnv("AXIGNAL_VALIDATION_UI_ENABLED");
}

export function isSeatGovernanceUiEnabled(): boolean {
  return boolEnv("AXIGNAL_SEAT_GOVERNANCE_UI_ENABLED");
}

export function isPasswordlessIdentityEnabled(): boolean {
  return identityRuntimeEnabled();
}

export function isAuthenticationRequired(): boolean {
  return (
    identityRuntimeEnabled() ||
    boolEnv("AXIGNAL_AUTH_REQUIRED") ||
    isPersistentResearchUiEnabled() ||
    isValidationUiEnabled() ||
    isSeatGovernanceUiEnabled()
  );
}

export function verifyPassword(password: string): boolean {
  const encoded = requiredEnv("AXIGNAL_AUTH_PASSWORD_SCRYPT");
  const [scheme, saltHex, expectedHex] = encoded.split("$");
  if (scheme !== "scrypt" || !saltHex || !expectedHex) {
    throw new Error("AXIGNAL_AUTH_PASSWORD_SCRYPT must use scrypt$saltHex$hashHex");
  }
  const expected = Buffer.from(expectedHex, "hex");
  const actual = scryptSync(
    password,
    Buffer.from(saltHex, "hex"),
    expected.length
  );
  return expected.length === actual.length && timingSafeEqual(expected, actual);
}

export function authenticateCredentials(
  email: string,
  password: string
): SessionClaims | null {
  if (identityRuntimeEnabled()) return null;
  const configuredEmail = requiredEnv("AXIGNAL_AUTH_EMAIL").toLowerCase();
  if (
    !equalText(email.trim().toLowerCase(), configuredEmail) ||
    !verifyPassword(password)
  ) {
    return null;
  }
  const now = Math.floor(Date.now() / 1000);
  return {
    sub: requiredEnv("AXIGNAL_AUTH_SUBJECT"),
    email: configuredEmail,
    iat: now,
    exp: now + SESSION_TTL_SECONDS
  };
}

export function createSessionToken(claims: SessionClaims): string {
  return createSignedToken(claims, requiredEnv("AXIGNAL_SESSION_SECRET"));
}

export function sessionCookieOptions() {
  return {
    name: SESSION_COOKIE,
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: SESSION_TTL_SECONDS
  };
}

function passwordlessIdentity(
  payload: Record<string, unknown> | null
): AuthenticatedIdentity | null {
  if (!payload) return null;
  const subject = text(payload.subject);
  const email = text(payload.email);
  const tenantId = payload.tenant_id;
  const userId = payload.user_id;
  const sessionId = payload.session_id;
  if (
    !subject ||
    !email ||
    !validUuid(tenantId) ||
    !validUuid(userId) ||
    !validUuid(sessionId)
  ) {
    return null;
  }
  const roles = Array.isArray(payload.roles)
    ? payload.roles.filter((value): value is string => typeof value === "string")
    : [];
  return {
    subject,
    email,
    tenantId,
    userId,
    sessionId,
    membershipId: validUuid(payload.membership_id) ? payload.membership_id : null,
    roles,
    authMethod: text(payload.auth_method),
    assuranceLevel: text(payload.assurance_level),
    authenticatedAt: text(payload.authenticated_at),
    stepUpValidUntil: text(payload.step_up_valid_until) ?? null,
    absoluteExpiresAt: text(payload.absolute_expires_at)
  };
}

export async function getAuthenticatedIdentity(): Promise<AuthenticatedIdentity | null> {
  if (!isAuthenticationRequired()) return null;
  if (identityRuntimeEnabled()) {
    return passwordlessIdentity(await resolveIdentitySession());
  }

  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return null;
  const claims = verifySignedToken<SessionClaims>(
    token,
    requiredEnv("AXIGNAL_SESSION_SECRET")
  );
  const now = Math.floor(Date.now() / 1000);
  if (!claims || claims.iat > now + 30 || claims.exp <= now) return null;
  const configuredSubject = requiredEnv("AXIGNAL_AUTH_SUBJECT");
  const configuredEmail = requiredEnv("AXIGNAL_AUTH_EMAIL").toLowerCase();
  if (
    claims.sub !== configuredSubject ||
    claims.email.toLowerCase() !== configuredEmail
  ) {
    return null;
  }
  const tenantId = requiredEnv("AXIGNAL_AUTH_TENANT_ID");
  if (!validUuid(tenantId)) {
    throw new Error("AXIGNAL_AUTH_TENANT_ID must be a UUID");
  }
  return { subject: claims.sub, email: claims.email, tenantId };
}

function timestamp(value: string | null | undefined): number | undefined {
  if (!value) return undefined;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? Math.floor(parsed / 1000) : undefined;
}

export function buildApiIdentityAssertion(identity: AuthenticatedIdentity): string {
  const now = Math.floor(Date.now() / 1000);
  const payload: Record<string, unknown> = {
    aud: "axignal-api",
    sub: identity.subject,
    email: identity.email,
    tenant_id: identity.tenantId,
    iat: now,
    exp: now + ASSERTION_TTL_SECONDS
  };
  const optional = {
    user_id: identity.userId,
    session_id: identity.sessionId,
    auth_method: identity.authMethod,
    assurance_level: identity.assuranceLevel,
    authenticated_at: timestamp(identity.authenticatedAt),
    step_up_valid_until: timestamp(identity.stepUpValidUntil)
  };
  for (const [key, value] of Object.entries(optional)) {
    if (value !== undefined && value !== null) payload[key] = value;
  }
  return createSignedToken(
    payload,
    requiredEnv("AXIGNAL_IDENTITY_ASSERTION_SECRET")
  );
}
