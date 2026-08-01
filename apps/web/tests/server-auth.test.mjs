import assert from "node:assert/strict";
import { createHmac, scryptSync } from "node:crypto";
import test from "node:test";

import {
  authenticateCredentials,
  buildApiIdentityAssertion,
  isAuthenticationRequired,
  isPersistentResearchUiEnabled,
  isSeatGovernanceUiEnabled,
  isValidationUiEnabled,
  sessionCookieOptions,
  verifyPassword
} from "../lib/server-auth.ts";

const ENV_KEYS = [
  "AXIGNAL_AUTH_EMAIL",
  "AXIGNAL_AUTH_PASSWORD_SCRYPT",
  "AXIGNAL_AUTH_REQUIRED",
  "AXIGNAL_AUTH_SUBJECT",
  "AXIGNAL_IDENTITY_ASSERTION_SECRET",
  "AXIGNAL_IDENTITY_RUNTIME_ENABLED",
  "AXIGNAL_PERSISTENT_RESEARCH_UI_ENABLED",
  "AXIGNAL_SEAT_GOVERNANCE_UI_ENABLED",
  "AXIGNAL_SESSION_SECRET",
  "AXIGNAL_VALIDATION_UI_ENABLED",
  "NODE_ENV"
];

function withEnvironment(values, callback) {
  const previous = new Map(ENV_KEYS.map((key) => [key, process.env[key]]));
  for (const key of ENV_KEYS) delete process.env[key];
  for (const [key, value] of Object.entries(values)) {
    if (value !== undefined) process.env[key] = String(value);
  }
  try {
    return callback();
  } finally {
    for (const key of ENV_KEYS) {
      const value = previous.get(key);
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
}

function passwordContract(password) {
  const saltHex = "00112233445566778899aabbccddeeff";
  const expectedHex = scryptSync(password, Buffer.from(saltHex, "hex"), 32).toString(
    "hex"
  );
  return `scrypt$${saltHex}$${expectedHex}`;
}

function decodeAndVerify(token, secret) {
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

test("feature flags accept only explicit truthy values and force authentication", () => {
  withEnvironment(
    {
      AXIGNAL_PERSISTENT_RESEARCH_UI_ENABLED: " YES ",
      AXIGNAL_VALIDATION_UI_ENABLED: "on",
      AXIGNAL_SEAT_GOVERNANCE_UI_ENABLED: "1"
    },
    () => {
      assert.equal(isPersistentResearchUiEnabled(), true);
      assert.equal(isValidationUiEnabled(), true);
      assert.equal(isSeatGovernanceUiEnabled(), true);
      assert.equal(isAuthenticationRequired(), true);
    }
  );

  withEnvironment(
    {
      AXIGNAL_PERSISTENT_RESEARCH_UI_ENABLED: "enabled",
      AXIGNAL_VALIDATION_UI_ENABLED: "0",
      AXIGNAL_SEAT_GOVERNANCE_UI_ENABLED: "false"
    },
    () => {
      assert.equal(isPersistentResearchUiEnabled(), false);
      assert.equal(isValidationUiEnabled(), false);
      assert.equal(isSeatGovernanceUiEnabled(), false);
      assert.equal(isAuthenticationRequired(), false);
    }
  );
});

test("legacy password verification uses the declared scrypt contract", () => {
  withEnvironment(
    { AXIGNAL_AUTH_PASSWORD_SCRYPT: passwordContract("correct horse") },
    () => {
      assert.equal(verifyPassword("correct horse"), true);
      assert.equal(verifyPassword("wrong battery"), false);
    }
  );

  withEnvironment({ AXIGNAL_AUTH_PASSWORD_SCRYPT: "sha256$00$11" }, () => {
    assert.throws(
      () => verifyPassword("anything"),
      /must use scrypt\$saltHex\$hashHex/
    );
  });
});

test("credential authentication normalises email and issues an eight-hour claim", () => {
  withEnvironment(
    {
      AXIGNAL_AUTH_EMAIL: "owner@axignal.example",
      AXIGNAL_AUTH_PASSWORD_SCRYPT: passwordContract("correct horse"),
      AXIGNAL_AUTH_SUBJECT: "founder-owner",
      AXIGNAL_IDENTITY_RUNTIME_ENABLED: "false"
    },
    () => {
      const before = Math.floor(Date.now() / 1000);
      const claims = authenticateCredentials(
        "  OWNER@AXIGNAL.EXAMPLE ",
        "correct horse"
      );
      const after = Math.floor(Date.now() / 1000);

      assert.ok(claims);
      assert.equal(claims.sub, "founder-owner");
      assert.equal(claims.email, "owner@axignal.example");
      assert.ok(claims.iat >= before && claims.iat <= after);
      assert.equal(claims.exp - claims.iat, 8 * 60 * 60);
      assert.equal(
        authenticateCredentials("intruder@axignal.example", "correct horse"),
        null
      );
      assert.equal(
        authenticateCredentials("owner@axignal.example", "wrong battery"),
        null
      );
    }
  );
});

test("legacy credentials fail closed when passwordless identity is enabled", () => {
  withEnvironment({ AXIGNAL_IDENTITY_RUNTIME_ENABLED: "true" }, () => {
    assert.equal(authenticateCredentials("any@example.com", "anything"), null);
    assert.equal(isAuthenticationRequired(), true);
  });
});

test("session cookies are HTTP-only, same-site and secure in production", () => {
  withEnvironment({ NODE_ENV: "production" }, () => {
    assert.deepEqual(sessionCookieOptions(), {
      name: "axignal_session",
      httpOnly: true,
      secure: true,
      sameSite: "lax",
      path: "/",
      maxAge: 8 * 60 * 60
    });
  });

  withEnvironment({ NODE_ENV: "test" }, () => {
    assert.equal(sessionCookieOptions().secure, false);
  });
});

test("API identity assertions are signed, short-lived and tenant-bound", () => {
  const secret = "identity-assertion-secret-with-sufficient-test-entropy";
  withEnvironment({ AXIGNAL_IDENTITY_ASSERTION_SECRET: secret }, () => {
    const before = Math.floor(Date.now() / 1000);
    const authenticatedAt = "2026-08-01T10:00:00.500Z";
    const stepUpValidUntil = "2026-08-01T10:05:00.900Z";
    const token = buildApiIdentityAssertion({
      subject: "usr_founder",
      email: "owner@axignal.example",
      tenantId: "11111111-1111-4111-8111-111111111111",
      userId: "22222222-2222-4222-8222-222222222222",
      sessionId: "33333333-3333-4333-8333-333333333333",
      authMethod: "PASSKEY",
      assuranceLevel: "AAL2",
      authenticatedAt,
      stepUpValidUntil
    });
    const after = Math.floor(Date.now() / 1000);
    const payload = decodeAndVerify(token, secret);

    assert.equal(payload.aud, "axignal-api");
    assert.equal(payload.sub, "usr_founder");
    assert.equal(payload.email, "owner@axignal.example");
    assert.equal(payload.tenant_id, "11111111-1111-4111-8111-111111111111");
    assert.equal(payload.user_id, "22222222-2222-4222-8222-222222222222");
    assert.equal(payload.session_id, "33333333-3333-4333-8333-333333333333");
    assert.equal(payload.auth_method, "PASSKEY");
    assert.equal(payload.assurance_level, "AAL2");
    assert.equal(payload.authenticated_at, Math.floor(Date.parse(authenticatedAt) / 1000));
    assert.equal(
      payload.step_up_valid_until,
      Math.floor(Date.parse(stepUpValidUntil) / 1000)
    );
    assert.ok(payload.iat >= before && payload.iat <= after);
    assert.equal(payload.exp - payload.iat, 60);
  });
});
