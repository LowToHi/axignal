import assert from "node:assert/strict";
import test from "node:test";

import {
  contentSecurityPolicy,
  evaluateMutationSecurity,
  MUTATION_ORIGIN_EXEMPT_PATHS,
  securityHeaders,
} from "../lib/security-boundaries";

const base = {
  method: "POST",
  pathname: "/api/pilot-intake",
  origin: "https://axignal.com",
  secFetchSite: "same-origin",
  configuredPublicOrigin: "https://axignal.com",
  requestOrigin: "http://127.0.0.1:3001",
  environment: "production",
  legacyPasswordLoginEnabled: undefined,
};

test("allows only exact-origin landing mutations", () => {
  assert.deepEqual(evaluateMutationSecurity(base), {
    allowed: true,
    code: "same_origin",
  });
  assert.deepEqual(evaluateMutationSecurity({ ...base, origin: null }), {
    allowed: false,
    code: "origin_required",
    status: 403,
  });
  assert.deepEqual(
    evaluateMutationSecurity({ ...base, origin: "https://attacker.example" }),
    {
      allowed: false,
      code: "cross_origin_forbidden",
      status: 403,
    },
  );
});

test("has no unsigned callback exemption", () => {
  assert.equal(MUTATION_ORIGIN_EXEMPT_PATHS.size, 0);
});

test("emits a Turnstile-compatible production CSP without unsafe-eval", () => {
  const policy = contentSecurityPolicy(true);
  assert.match(policy, /https:\/\/challenges\.cloudflare\.com/);
  assert.doesNotMatch(policy, /'unsafe-eval'/);
  assert.equal(
    new Map(securityHeaders(true).map(({ key, value }) => [key, value])).get(
      "X-Content-Type-Options",
    ),
    "nosniff",
  );
});
