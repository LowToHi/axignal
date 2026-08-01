export const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export type MutationSecurityInput = {
  method: string;
  pathname: string;
  origin: string | null;
  secFetchSite: string | null;
  configuredPublicOrigin: string | undefined;
  requestOrigin: string;
  environment: string | undefined;
  legacyPasswordLoginEnabled: string | undefined;
};

export type MutationSecurityDecision =
  | { allowed: true; code: "not_mutating" | "same_origin" }
  | {
      allowed: false;
      code:
        | "legacy_password_login_disabled"
        | "public_origin_not_configured"
        | "origin_required"
        | "cross_origin_forbidden"
        | "cross_site_forbidden";
      status: 403 | 404 | 503;
    };

function normaliseOrigin(value: string): string | null {
  try {
    const parsed = new URL(value);
    if (!["http:", "https:"].includes(parsed.protocol)) return null;
    return parsed.origin;
  } catch {
    return null;
  }
}

export function legacyPasswordLoginAllowed(input: {
  environment: string | undefined;
  enabled: string | undefined;
}): boolean {
  return (
    input.environment !== "production" &&
    input.enabled?.trim().toLowerCase() === "true"
  );
}

export function evaluateMutationSecurity(
  input: MutationSecurityInput
): MutationSecurityDecision {
  const method = input.method.toUpperCase();
  if (!MUTATING_METHODS.has(method)) {
    return { allowed: true, code: "not_mutating" };
  }

  if (
    input.pathname === "/api/auth/login" &&
    !legacyPasswordLoginAllowed({
      environment: input.environment,
      enabled: input.legacyPasswordLoginEnabled
    })
  ) {
    return {
      allowed: false,
      code: "legacy_password_login_disabled",
      status: 404
    };
  }

  const expected = normaliseOrigin(
    input.environment === "production"
      ? input.configuredPublicOrigin ?? ""
      : input.configuredPublicOrigin ?? input.requestOrigin
  );
  if (!expected) {
    return {
      allowed: false,
      code: "public_origin_not_configured",
      status: 503
    };
  }

  const supplied = input.origin ? normaliseOrigin(input.origin) : null;
  if (!supplied) {
    return { allowed: false, code: "origin_required", status: 403 };
  }
  if (supplied !== expected) {
    return { allowed: false, code: "cross_origin_forbidden", status: 403 };
  }

  if (
    input.secFetchSite !== null &&
    input.secFetchSite.toLowerCase() !== "same-origin"
  ) {
    return { allowed: false, code: "cross_site_forbidden", status: 403 };
  }

  return { allowed: true, code: "same_origin" };
}

export const CONTENT_SECURITY_POLICY = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  "connect-src 'self' https: wss:",
  "worker-src 'self' blob:",
  "manifest-src 'self'",
  "upgrade-insecure-requests"
].join("; ");

export function securityHeaders(production: boolean): Array<{
  key: string;
  value: string;
}> {
  const headers = [
    { key: "Content-Security-Policy", value: CONTENT_SECURITY_POLICY },
    { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
    { key: "X-Content-Type-Options", value: "nosniff" },
    { key: "X-Frame-Options", value: "DENY" },
    { key: "X-DNS-Prefetch-Control", value: "off" },
    {
      key: "Permissions-Policy",
      value: "camera=(), microphone=(), geolocation=(), browsing-topics=()"
    }
  ];
  if (production) {
    headers.push({
      key: "Strict-Transport-Security",
      value: "max-age=63072000; includeSubDomains; preload"
    });
  }
  return headers;
}
