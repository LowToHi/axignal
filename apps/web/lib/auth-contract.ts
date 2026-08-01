import { createHmac, scryptSync, timingSafeEqual } from "node:crypto";

export const SESSION_COOKIE = "axignal_session";
export const SESSION_VERSION = "v1";
export const SESSION_TTL_SECONDS = 60 * 60 * 8;
export const ASSERTION_TTL_SECONDS = 60;

export type AuthenticatedIdentity = {
  subject: string;
  email: string;
  tenantId: string;
  userId?: string | undefined;
  sessionId?: string | undefined;
  membershipId?: string | null | undefined;
  roles?: string[] | undefined;
  authMethod?: string | undefined;
  assuranceLevel?: string | undefined;
  authenticatedAt?: string | undefined;
  stepUpValidUntil?: string | null | undefined;
  absoluteExpiresAt?: string | undefined;
};

export type SessionClaims = {
  sub: string;
  email: string;
  iat: number;
  exp: number;
};

export function environmentFlag(name: string): boolean {
  return ["1", "true", "yes", "on"].includes(
    (process.env[name] ?? "").trim().toLowerCase()
  );
}

export function requiredEnvironment(name: string): string {
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

export function constantTimeTextEqual(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  return (
    leftBuffer.length === rightBuffer.length &&
    timingSafeEqual(leftBuffer, rightBuffer)
  );
}

export function createSignedToken(payload: object, secret: string): string {
  const encodedPayload = encode(JSON.stringify(payload));
  return `${SESSION_VERSION}.${encodedPayload}.${sign(
    SESSION_VERSION,
    encodedPayload,
    secret
  )}`;
}

export function verifySignedToken<T>(token: string, secret: string): T | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const version = parts[0];
  const payload = parts[1];
  const signature = parts[2];
  if (!version || !payload || !signature || version !== SESSION_VERSION) return null;
  if (!constantTimeTextEqual(signature, sign(version, payload, secret))) return null;
  try {
    return JSON.parse(decode(payload).toString("utf8")) as T;
  } catch {
    return null;
  }
}

export function validUuid(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      value
    )
  );
}

export function nonEmptyText(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

export function verifyScryptPassword(password: string, encoded: string): boolean {
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

export function authenticateLegacyCredentials(
  email: string,
  password: string,
  configuration: {
    configuredEmail: string;
    encodedPassword: string;
    subject: string | (() => string);
    nowSeconds?: number;
  }
): SessionClaims | null {
  const configuredEmail = configuration.configuredEmail.toLowerCase();
  if (
    !constantTimeTextEqual(email.trim().toLowerCase(), configuredEmail) ||
    !verifyScryptPassword(password, configuration.encodedPassword)
  ) {
    return null;
  }
  const now = configuration.nowSeconds ?? Math.floor(Date.now() / 1000);
  return {
    sub:
      typeof configuration.subject === "function"
        ? configuration.subject()
        : configuration.subject,
    email: configuredEmail,
    iat: now,
    exp: now + SESSION_TTL_SECONDS
  };
}

export function authenticationRequired(configuration: {
  identityRuntime: boolean;
  explicitAuthentication: boolean;
  persistentResearch: boolean;
  validation: boolean;
  seatGovernance: boolean;
}): boolean {
  return (
    configuration.identityRuntime ||
    configuration.explicitAuthentication ||
    configuration.persistentResearch ||
    configuration.validation ||
    configuration.seatGovernance
  );
}

export function sessionCookieOptionsFor(nodeEnvironment: string | undefined) {
  return {
    name: SESSION_COOKIE,
    httpOnly: true,
    secure: nodeEnvironment === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: SESSION_TTL_SECONDS
  };
}

function timestamp(value: string | null | undefined): number | undefined {
  if (!value) return undefined;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? Math.floor(parsed / 1000) : undefined;
}

export function buildApiIdentityAssertionToken(
  identity: AuthenticatedIdentity,
  secret: string,
  nowSeconds = Math.floor(Date.now() / 1000)
): string {
  const payload: Record<string, unknown> = {
    aud: "axignal-api",
    sub: identity.subject,
    email: identity.email,
    tenant_id: identity.tenantId,
    iat: nowSeconds,
    exp: nowSeconds + ASSERTION_TTL_SECONDS
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
  return createSignedToken(payload, secret);
}
