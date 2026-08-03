import { AuthGate } from "@/components/auth-gate";
import {
  getAuthenticatedIdentity,
  isAuthenticationRequired,
  isPasswordlessIdentityEnabled
} from "@/lib/server-auth";

import { AxentHelp } from "./axent-help";

function boolEnv(name: string): boolean {
  return ["1", "true", "yes", "on", "explicit"].includes(
    (process.env[name] ?? "").trim().toLowerCase()
  );
}

export async function AxentHelpEntry() {
  if (!isAuthenticationRequired()) {
    return (
      <main role="alert">
        Axent requires server-authoritative authentication.
      </main>
    );
  }
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    const turnstileSiteKey = process.env.NEXT_PUBLIC_AXIGNAL_TURNSTILE_SITE_KEY;
    return (
      <AuthGate
        passwordless={isPasswordlessIdentityEnabled()}
        testRuntime={boolEnv("AXIGNAL_TEST_RUNTIME_ENABLED")}
        {...(turnstileSiteKey ? { turnstileSiteKey } : {})}
      />
    );
  }
  return <AxentHelp />;
}
