import assert from "node:assert/strict";
import test from "node:test";

import {
  contentSecurityPolicy,
  evaluateMutationSecurity,
  legacyPasswordLoginAllowed,
  MUTATION_ORIGIN_EXEMPT_PATHS,
  normaliseOrigin,
  securityHeaders,
} from "../lib/security-boundaries";

const sameOriginInput = {
  method: "POST",
  pathname: "/api/research/runs",
  origin: "https://axignal.com",
  secFetchSite: "same-origin",
  configuredPublicOrigin: "https://axignal.com/",
  requestOrigin: "http://127.0.0.1:3000",
  environment: "production",
  legacyPasswordLoginEnabled: undefined,
};

test("allows reads without an Origin header", () => {
  assert.deepEqual(
    evaluateMutationSecurity({
      ...sameOriginInput,
      method: "GET",
      origin: null,
      secFetchSite: null,
    }),
    { allowed: true, code: "not_mutating" },
  );
});

test("allows exact same-origin browser mutations", () => {
  assert.deepEqual(evaluateMutationSecurity(sameOriginInput), {
    allowed: true,
    code: "same_origin",
  });
});

test("fails closed when the production public origin is absent", () => {
  assert.deepEqual(
    evaluateMutationSecurity({
      ...sameOriginInput,
      configuredPublicOrigin: undefined,
    }),
    {
      allowed: false,
      code: "public_origin_not_configured",
      status: 503,
    },
  );
});

test("rejects missing, malformed and cross-origin mutation headers", () => {
  assert.deepEqual(
    evaluateMutationSecurity({ ...sameOriginInput, origin: null }),
    { allowed: false, code: "origin_required", status: 403 },
  );
  assert.deepEqual(
    evaluateMutationSecurity({ ...sameOriginInput, origin: "null" }),
    { allowed: false, code: "origin_required", status: 403 },
  );
  assert.deepEqual(
    evaluateMutationSecurity({
      ...sameOriginInput,
      origin: "https://attacker.example",
    }),
    { allowed: false, code: "cross_origin_forbidden", status: 403 },
  );
});

test("rejects same-site and cross-site fetch metadata", () => {
  for (const secFetchSite of ["same-site", "cross-site", "none"]) {
    assert.deepEqual(
      evaluateMutationSecurity({ ...sameOriginInput, secFetchSite }),
      { allowed: false, code: "cross_site_forbidden", status: 403 },
    );
  }
});

test("permits clients without Fetch Metadata only when Origin is exact", () => {
  assert.deepEqual(
    evaluateMutationSecurity({ ...sameOriginInput, secFetchSite: null }),
    { allowed: true, code: "same_origin" },
  );
});

test("keeps callback exemptions empty until signature verification exists", () => {
  assert.equal(MUTATION_ORIGIN_EXEMPT_PATHS.size, 0);
});

test("normalises only authority-only HTTP origins", () => {
  assert.equal(normaliseOrigin("https://axignal.com/"), "https://axignal.com");
  assert.equal(normaliseOrigin("https://axignal.com/path"), null);
  assert.equal(normaliseOrigin("https://user:pass@axignal.com"), null);
  assert.equal(normaliseOrigin("javascript:alert(1)"), null);
});

test("disables legacy password login in production and by default", () => {
  assert.equal(
    legacyPasswordLoginAllowed({ environment: "production", enabled: "true" }),
    false,
  );
  assert.equal(
    legacyPasswordLoginAllowed({
      environment: "development",
      enabled: undefined,
    }),
    false,
  );
  assert.equal(
    legacyPasswordLoginAllowed({ environment: "development", enabled: "true" }),
    true,
  );

  assert.deepEqual(
    evaluateMutationSecurity({
      ...sameOriginInput,
      pathname: "/api/auth/login",
      legacyPasswordLoginEnabled: "true",
    }),
    {
      allowed: false,
      code: "legacy_password_login_disabled",
      status: 404,
    },
  );
});

test("emits production headers without unsafe-eval and permits Turnstile", () => {
  const policy = contentSecurityPolicy(true);
  assert.match(policy, /script-src[^;]*https:\/\/challenges\.cloudflare\.com/);
  assert.match(policy, /frame-src[^;]*https:\/\/challenges\.cloudflare\.com/);
  assert.doesNotMatch(policy, /'unsafe-eval'/);
  assert.match(policy, /upgrade-insecure-requests/);

  const headers = new Map(
    securityHeaders(true).map(({ key, value }) => [key, value]),
  );
  assert.equal(headers.get("X-Frame-Options"), "DENY");
  assert.equal(headers.get("X-Content-Type-Options"), "nosniff");
  assert.equal(headers.get("Cross-Origin-Opener-Policy"), "same-origin");
  assert.match(
    headers.get("Strict-Transport-Security") ?? "",
    /includeSubDomains/,
  );
});

test("permits unsafe-eval only in the development CSP", () => {
  assert.match(contentSecurityPolicy(false), /'unsafe-eval'/);
  assert.doesNotMatch(
    contentSecurityPolicy(false),
    /upgrade-insecure-requests/,
  );
});
