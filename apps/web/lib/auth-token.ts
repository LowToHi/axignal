import { createHmac, scryptSync, timingSafeEqual } from "node:crypto";

export const SESSION_TOKEN_VERSION = "v1";

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

export function equalText(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  return (
    leftBuffer.length === rightBuffer.length &&
    timingSafeEqual(leftBuffer, rightBuffer)
  );
}

export function createSignedToken(payload: object, secret: string): string {
  const encodedPayload = encode(JSON.stringify(payload));
  return `${SESSION_TOKEN_VERSION}.${encodedPayload}.${sign(
    SESSION_TOKEN_VERSION,
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
  if (
    !version ||
    !payload ||
    !signature ||
    version !== SESSION_TOKEN_VERSION
  ) {
    return null;
  }
  if (!equalText(signature, sign(version, payload, secret))) return null;

  try {
    const parsed: unknown = JSON.parse(decode(payload).toString("utf8"));
    return parsed !== null && typeof parsed === "object" ? (parsed as T) : null;
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

export function timestamp(value: string | null | undefined): number | undefined {
  if (!value) return undefined;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? Math.floor(parsed / 1000) : undefined;
}

export function verifyScryptPassword(password: string, encoded: string): boolean {
  const [scheme, saltHex, expectedHex] = encoded.split("$");
  if (
    scheme !== "scrypt" ||
    !saltHex ||
    !expectedHex ||
    !/^[0-9a-f]+$/i.test(saltHex) ||
    !/^[0-9a-f]+$/i.test(expectedHex) ||
    saltHex.length % 2 !== 0 ||
    expectedHex.length % 2 !== 0
  ) {
    throw new Error("Scrypt credentials must use scrypt$saltHex$hashHex");
  }

  const expected = Buffer.from(expectedHex, "hex");
  if (expected.length === 0) {
    throw new Error("Scrypt credentials must contain a non-empty hash");
  }
  const actual = scryptSync(
    password,
    Buffer.from(saltHex, "hex"),
    expected.length
  );
  return expected.length === actual.length && timingSafeEqual(expected, actual);
}
