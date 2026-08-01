import { cookies } from "next/headers";

import {
  authenticateLegacyCredentials,
  authenticationRequired,
  buildApiIdentityAssertionToken,
  constantTimeTextEqual,
  createSignedToken,
  environmentFlag,
  nonEmptyText,
  requiredEnvironment,
  SESSION_COOKIE,
  sessionCookieOptionsFor,
  type AuthenticatedIdentity,
  type SessionClaims,
  validUuid,
  verifyScryptPassword,
  verifySignedToken
} from "./auth-contract";
import { identityRuntimeEnabled, resolveIdentitySession } from "./identity-server";

export type { AuthenticatedIdentity } from "./auth-contract";

export function isPersistentResearchUiEnabled(): boolean {
  return environmentFlag("AXIGNAL_PERSISTENT_RESEARCH_UI_ENABLED");
}

export function isValidationUiEnabled(): boolean {
  return environmentFlag("AXIGNAL_VALIDATION_UI_ENABLED");
}

export function isSeatGovernanceUiEnabled(): boolean {
  return environmentFlag("AXIGNAL_SEAT_GOVERNANCE_UI_ENABLED");
}

export function isPasswordlessIdentityEnabled(): boolean {
  return identityRuntimeEnabled();
}

export function isAuthenticationRequired(): boolean {
  return authenticationRequired({
    identityRuntime: identityRuntimeEnabled(),
    explicitAuthentication: environmentFlag("AXIGNAL_AUTH_REQUIRED"),
    persistentResearch: isPersistentResearchUiEnabled(),
    validation: isValidationUiEnabled(),
    seatGovernance: isSeatGovernanceUiEnabled()
  });
}

export function verifyPassword(password: string): boolean {
  return verifyScryptPassword(
    password,
    requiredEnvironment("AXIGNAL_AUTH_PASSWORD_SCRYPT")
  );
}

export function authenticateCredentials(
  email: string,
  password: string
): SessionClaims | null {
  if (identityRuntimeEnabled()) return null;
  const configuredEmail = requiredEnvironment("AXIGNAL_AUTH_EMAIL").toLowerCase();
  if (!constantTimeTextEqual(email.trim().toLowerCase(), configuredEmail)) {
    return null;
  }
  return authenticateLegacyCredentials(email, password, {
    configuredEmail,
    encodedPassword: requiredEnvironment("AXIGNAL_AUTH_PASSWORD_SCRYPT"),
    subject: () => requiredEnvironment("AXIGNAL_AUTH_SUBJECT")
  });
}

export function createSessionToken(claims: SessionClaims): string {
  return createSignedToken(
    claims,
    requiredEnvironment("AXIGNAL_SESSION_SECRET")
  );
}

export function sessionCookieOptions() {
  return sessionCookieOptionsFor(process.env.NODE_ENV);
}

function passwordlessIdentity(
  payload: Record<string, unknown> | null
): AuthenticatedIdentity | null {
  if (!payload) return null;
  const subject = nonEmptyText(payload.subject);
  const email = nonEmptyText(payload.email);
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
    authMethod: nonEmptyText(payload.auth_method),
    assuranceLevel: nonEmptyText(payload.assurance_level),
    authenticatedAt: nonEmptyText(payload.authenticated_at),
    stepUpValidUntil: nonEmptyText(payload.step_up_valid_until) ?? null,
    absoluteExpiresAt: nonEmptyText(payload.absolute_expires_at)
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
    requiredEnvironment("AXIGNAL_SESSION_SECRET")
  );
  const now = Math.floor(Date.now() / 1000);
  if (!claims || claims.iat > now + 30 || claims.exp <= now) return null;
  const configuredSubject = requiredEnvironment("AXIGNAL_AUTH_SUBJECT");
  const configuredEmail = requiredEnvironment("AXIGNAL_AUTH_EMAIL").toLowerCase();
  if (
    claims.sub !== configuredSubject ||
    claims.email.toLowerCase() !== configuredEmail
  ) {
    return null;
  }
  const tenantId = requiredEnvironment("AXIGNAL_AUTH_TENANT_ID");
  if (!validUuid(tenantId)) {
    throw new Error("AXIGNAL_AUTH_TENANT_ID must be a UUID");
  }
  return { subject: claims.sub, email: claims.email, tenantId };
}

export function buildApiIdentityAssertion(identity: AuthenticatedIdentity): string {
  return buildApiIdentityAssertionToken(
    identity,
    requiredEnvironment("AXIGNAL_IDENTITY_ASSERTION_SECRET")
  );
}
