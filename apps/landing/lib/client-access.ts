/**
 * Client-access configuration for the public landing.
 *
 * The authenticated AXIGNAL application (AuthGate / passkey login) lives in
 * `apps/web` and is deployed separately from this landing.  The landing never
 * hardcodes its address: it is supplied at build time through
 * `NEXT_PUBLIC_AXIGNAL_APP_URL` and validated before use.
 */

const APP_URL_RAW = process.env.NEXT_PUBLIC_AXIGNAL_APP_URL;

function isSafeAppUrl(value: string | undefined): value is string {
  if (!value) return false;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" || parsed.protocol === "http:";
  } catch {
    return false;
  }
}

export const AXIGNAL_APP_URL = isSafeAppUrl(APP_URL_RAW) ? APP_URL_RAW : null;

/** Resolved application URL; callers must handle the unconfigured case. */
export function clientAppUrl(): string | null {
  return AXIGNAL_APP_URL;
}
