export const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

/**
 * External callbacks must be added individually after signature verification exists.
 * AXIGNAL currently exposes no browser-external mutation callback in either frontend.
 */
export const MUTATION_ORIGIN_EXEMPT_PATHS = new Set<string>();

export type MutationSecurityInput = {
  method: string;
  pathname: string;
  origin: string | null;
  secFetchSite: string | null;
  configuredPublicOrigin: string | undefined;
  requestOrigin: string;
  environment: string | undefined;
  legacyPasswordLoginEnabled: string | undefined;
  exemptPaths?: ReadonlySet<string>;
};

export type MutationSecurityDecision =
  | {
      allowed: true;
      code: "not_mutating" | "same_origin" | "trusted_callback";
    }
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

export function normaliseOrigin(value: string): string | null {
  try {
    const parsed = new URL(value);
    if (!["http:", "https:"].includes(parsed.protocol)) return null;
    if (parsed.username || parsed.password) return null;
    if (parsed.pathname !== "/" || parsed.search || parsed.hash) return null;
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

  const exemptPaths = input.exemptPaths ?? MUTATION_ORIGIN_EXEMPT_PATHS;
  if (exemptPaths.has(input.pathname)) {
    return { allowed: true, code: "trusted_callback" };
  }

  const configuredOrigin = input.configuredPublicOrigin?.trim();
  const expected = normaliseOrigin(
    input.environment === "production"
      ? configuredOrigin ?? ""
      : configuredOrigin || input.requestOrigin
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
    input.secFetchSite.trim().toLowerCase() !== "same-origin"
  ) {
    return { allowed: false, code: "cross_site_forbidden", status: 403 };
  }

  return { allowed: true, code: "same_origin" };
}

export function contentSecurityPolicy(production: boolean): string {
  const scriptSources = [
    "'self'",
    "'unsafe-inline'",
    "https://challenges.cloudflare.com"
  ];
  if (!production) scriptSources.push("'unsafe-eval'");

  const directives = [
    "default-src 'self'",
    "base-uri 'self'",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "form-action 'self'",
    `script-src ${scriptSources.join(" ")}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "connect-src 'self' https://challenges.cloudflare.com",
    "frame-src 'self' https://challenges.cloudflare.com",
    "worker-src 'self' blob:",
    "child-src 'self' blob: https://challenges.cloudflare.com",
    "media-src 'self'",
    "manifest-src 'self'"
  ];
  if (production) directives.push("upgrade-insecure-requests");
  return directives.join("; ");
}

export function securityHeaders(production: boolean): Array<{
  key: string;
  value: string;
}> {
  const headers = [
    {
      key: "Content-Security-Policy",
      value: contentSecurityPolicy(production)
    },
    { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
    { key: "X-Content-Type-Options", value: "nosniff" },
    { key: "X-Frame-Options", value: "DENY" },
    { key: "X-DNS-Prefetch-Control", value: "off" },
    { key: "X-Permitted-Cross-Domain-Policies", value: "none" },
    { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
    { key: "Cross-Origin-Resource-Policy", value: "same-origin" },
    { key: "Origin-Agent-Cluster", value: "?1" },
    {
      key: "Permissions-Policy",
      value:
        "camera=(), microphone=(), geolocation=(), payment=(), publickey-credentials-get=(self), browsing-topics=()"
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
