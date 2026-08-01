import assert from "node:assert/strict";
import { createHmac, scryptSync } from "node:crypto";
import test from "node:test";

import {
  authenticateLegacyCredentials,
  authenticationRequired,
  buildApiIdentityAssertionToken,
  createSignedToken,
  environmentFlag,
  sessionCookieOptionsFor,
  validUuid,
  verifyScryptPassword,
  verifySignedToken
} from "../lib/auth-contract.ts";

function passwordContract(password) {
  const saltHex = "00112233445566778899aabbccddeeff";
  const expectedHex = scryptSync(password, Buffer.from(saltHex, "hex"), 32).toString(
    "hex"
  );
  return `scrypt$${saltHex}$${expectedHex}`;
}

function decodeAndVerifyIndependently(token, secret) {
  const [version, payload, signature] = token.split(".");
  assert.equal(version, "v1");
  assert.ok(payload);
  assert.ok(signature);
  assert.equal(
    signature,
    createHmac("sha256", secret)
      .update(`${version}.${payload}`)
      .digest("base64url")
  );
  return JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
}

test("feature flags accept only explicit truthy values", () => {
  const previous = process.env.AXIGNAL_TEST_FLAG;
  try {
    for (const value of ["1", "true", " YES ", "on"]) {
      process.env.AXIGNAL_TEST_FLAG = value;
      assert.equal(environmentFlag("AXIGNAL_TEST_FLAG"), true);
    }
    for (const value of ["", "0", "false", "enabled", "truthy"]) {
      process.env.AXIGNAL_TEST_FLAG = value;
      assert.equal(environmentFlag("AXIGNAL_TEST_FLAG"), false);
    }
  } finally {
    if (previous === undefined) delete process.env.AXIGNAL_TEST_FLAG;
    else process.env.AXIGNAL_TEST_FLAG = previous;
  }
});

test("every protected frontend capability forces authentication", () => {
  const baseline = {
    identityRuntime: false,
    explicitAuthentication: false,
    persistentResearch: false,
    validation: false,
    seatGovernance: false
  };
  assert.equal(authenticationRequired(baseline), false);

  for (const capability of Object.keys(baseline)) {
    assert.equal(
      authenticationRequired({ ...baseline, [capability]: true }),
      true,
      `${capability} must require authentication`
    );
  }
});

test("password verification uses the declared scrypt contract", () => {
  const encoded = passwordContract("correct horse");
  assert.equal(verifyScryptPassword("correct horse", encoded), true);
  assert.equal(verifyScryptPassword("wrong battery", encoded), false);
  assert.throws(
    () => verifyScryptPassword("anything", "sha256$00$11"),
    /must use scrypt\$saltHex\$hashHex/
  );
});

test("legacy credentials normalise email, preserve timing and resolve subject lazily", () => {
  let subjectReads = 0;
  const configuration = {
    configuredEmail: "owner@axignal.example",
    encodedPassword: passwordContract("correct horse"),
    subject: () => {
      subjectReads += 1;
      return "founder-owner";
    },
    nowSeconds: 1_800_000_000
  };

  assert.equal(
    authenticateLegacyCredentials(
      "intruder@axignal.example",
      "correct horse",
      configuration
    ),
    null
  );
  assert.equal(subjectReads, 0);
  assert.equal(
    authenticateLegacyCredentials(
      "owner@axignal.example",
      "wrong battery",
      configuration
    ),
    null
  );
  assert.equal(subjectReads, 0);

  assert.deepEqual(
    authenticateLegacyCredentials(
      "  OWNER@AXIGNAL.EXAMPLE ",
      "correct horse",
      configuration
    ),
    {
      sub: "founder-owner",
      email: "owner@axignal.example",
      iat: 1_800_000_000,
      exp: 1_800_028_800
    }
  );
  assert.equal(subjectReads, 1);
});

test("session cookies are HTTP-only, same-site and secure only in production", () => {
  assert.deepEqual(sessionCookieOptionsFor("production"), {
    name: "axignal_session",
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
    maxAge: 8 * 60 * 60
  });
  assert.equal(sessionCookieOptionsFor("test").secure, false);
});

test("API identity assertions are signed, short-lived and tenant-bound", () => {
  const secret = "identity-assertion-secret-with-sufficient-test-entropy";
  const authenticatedAt = "2026-08-01T10:00:00.500Z";
  const stepUpValidUntil = "2026-08-01T10:05:00.900Z";
  const token = buildApiIdentityAssertionToken(
    {
      subject: "usr_founder",
      email: "owner@axignal.example",
      tenantId: "11111111-1111-4111-8111-111111111111",
      userId: "22222222-2222-4222-8222-222222222222",
      sessionId: "33333333-3333-4333-8333-333333333333",
      authMethod: "PASSKEY",
      assuranceLevel: "AAL2",
      authenticatedAt,
      stepUpValidUntil
    },
    secret,
    1_800_000_000
  );
  const payload = decodeAndVerifyIndependently(token, secret);

  assert.deepEqual(payload, {
    aud: "axignal-api",
    sub: "usr_founder",
    email: "owner@axignal.example",
    tenant_id: "11111111-1111-4111-8111-111111111111",
    iat: 1_800_000_000,
    exp: 1_800_000_060,
    user_id: "22222222-2222-4222-8222-222222222222",
    session_id: "33333333-3333-4333-8333-333333333333",
    auth_method: "PASSKEY",
    assurance_level: "AAL2",
    authenticated_at: Math.floor(Date.parse(authenticatedAt) / 1000),
    step_up_valid_until: Math.floor(Date.parse(stepUpValidUntil) / 1000)
  });
  assert.deepEqual(verifySignedToken(token, secret), payload);
});

test("signed tokens reject tampering, wrong secrets and malformed structures", () => {
  const token = createSignedToken({ sub: "owner" }, "correct-secret");
  const [version, payload, signature] = token.split(".");

  assert.deepEqual(verifySignedToken(token, "correct-secret"), { sub: "owner" });
  assert.equal(verifySignedToken(token, "wrong-secret"), null);
  assert.equal(
    verifySignedToken(`${version}.${payload}x.${signature}`, "correct-secret"),
    null
  );
  assert.equal(verifySignedToken("not-a-token", "correct-secret"), null);
});

test("tenant and session identifiers accept only RFC 4122 UUID variants", () => {
  assert.equal(validUuid("11111111-1111-4111-8111-111111111111"), true);
  assert.equal(validUuid("11111111-1111-7111-8111-111111111111"), false);
  assert.equal(validUuid("11111111-1111-4111-0111-111111111111"), false);
  assert.equal(validUuid("tenant-from-browser"), false);
  assert.equal(validUuid(null), false);
});
