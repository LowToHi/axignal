import assert from "node:assert/strict";
import { scryptSync } from "node:crypto";
import { test } from "node:test";

import {
  createSignedToken,
  equalText,
  timestamp,
  validUuid,
  verifyScryptPassword,
  verifySignedToken
} from "../lib/auth-token";

const secret = "test-only-session-secret-with-sufficient-entropy";

test("signed token round-trips typed claims", () => {
  const claims = {
    sub: "founder@example.test",
    tenant_id: "7fd744ec-52c3-4f86-a9ac-371899717293",
    exp: 2_000_000_000
  };

  const token = createSignedToken(claims, secret);

  assert.deepEqual(verifySignedToken<typeof claims>(token, secret), claims);
});

test("signed token rejects modified payload, signature and secret", () => {
  const token = createSignedToken({ sub: "subject-a" }, secret);
  const [version, payload] = token.split(".");
  assert.ok(version);
  assert.ok(payload);

  assert.equal(
    verifySignedToken(`${version}.${payload}x.invalid`, secret),
    null
  );
  assert.equal(verifySignedToken(token, `${secret}-different`), null);
});

test("signed token rejects malformed envelopes", () => {
  assert.equal(verifySignedToken("", secret), null);
  assert.equal(verifySignedToken("v1.payload", secret), null);
  assert.equal(verifySignedToken("v2.payload.signature", secret), null);
  assert.equal(verifySignedToken("v1..signature", secret), null);
});

test("constant-time text comparison preserves exact equality semantics", () => {
  assert.equal(equalText("same-value", "same-value"), true);
  assert.equal(equalText("same-value", "different-value"), false);
  assert.equal(equalText("short", "longer"), false);
});

test("UUID validation accepts supported UUIDs and rejects malformed identifiers", () => {
  assert.equal(validUuid("7fd744ec-52c3-4f86-a9ac-371899717293"), true);
  assert.equal(validUuid("not-a-uuid"), false);
  assert.equal(validUuid("00000000-0000-0000-0000-000000000000"), false);
  assert.equal(validUuid(null), false);
});

test("timestamp converts valid ISO instants and rejects missing or invalid values", () => {
  assert.equal(timestamp("2026-08-01T00:00:00Z"), 1_785_542_400);
  assert.equal(timestamp("invalid"), undefined);
  assert.equal(timestamp(null), undefined);
  assert.equal(timestamp(undefined), undefined);
});

test("scrypt password verification accepts only the exact password", () => {
  const salt = Buffer.from("00112233445566778899aabbccddeeff", "hex");
  const expected = scryptSync("correct horse battery staple", salt, 32);
  const encoded = `scrypt$${salt.toString("hex")}$${expected.toString("hex")}`;

  assert.equal(
    verifyScryptPassword("correct horse battery staple", encoded),
    true
  );
  assert.equal(verifyScryptPassword("wrong password", encoded), false);
});

test("scrypt password verification rejects malformed credential material", () => {
  assert.throws(
    () => verifyScryptPassword("password", "pbkdf2$salt$hash"),
    /scrypt\$saltHex\$hashHex/
  );
  assert.throws(
    () => verifyScryptPassword("password", "scrypt$not-hex$00"),
    /scrypt\$saltHex\$hashHex/
  );
  assert.throws(
    () => verifyScryptPassword("password", "scrypt$00$"),
    /scrypt\$saltHex\$hashHex/
  );
});
