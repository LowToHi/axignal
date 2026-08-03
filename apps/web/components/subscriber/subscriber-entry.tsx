import { AuthGate } from "@/components/auth-gate";
import {
  getAuthenticatedIdentity,
  isAuthenticationRequired,
  isPasswordlessIdentityEnabled
} from "@/lib/server-auth";

import { SubscriberLiveWorkspace } from "./subscriber-live-workspace";

function boolEnv(name: string): boolean {
  return ["1", "true", "yes", "on", "explicit"].includes(
    (process.env[name] ?? "").trim().toLowerCase()
  );
}

function unauthenticatedGate() {
  const turnstileSiteKey = process.env.NEXT_PUBLIC_AXIGNAL_TURNSTILE_SITE_KEY;
  return (
    <AuthGate
      passwordless={isPasswordlessIdentityEnabled()}
      testRuntime={boolEnv("AXIGNAL_TEST_RUNTIME_ENABLED")}
      {...(turnstileSiteKey ? { turnstileSiteKey } : {})}
    />
  );
}

function configurationError(message: string) {
  return (
    <main
      role="alert"
      data-e2e-terminal-error="true"
      style={{
        minHeight: "100vh",
        display: "grid",
        placeContent: "center",
        gap: "0.75rem",
        padding: "2rem",
        color: "#f4f7fb",
        background: "#08111d",
        textAlign: "center"
      }}
    >
      <strong>Persistent AXIGNAL workspace unavailable</strong>
      <p>{message}</p>
    </main>
  );
}

export async function SubscriberEntry() {
  if (!isAuthenticationRequired()) {
    return configurationError("Authentication must be enabled for the main subscriber path.");
  }

  const identity = await getAuthenticatedIdentity();
  if (!identity) return unauthenticatedGate();

  if (!boolEnv("AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED")) {
    return configurationError("AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED is required.");
  }

  if ((process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_FIXTURE_MODE ?? "").trim()) {
    return configurationError("Fixture mode is forbidden on the main subscriber path.");
  }

  return (
    <SubscriberLiveWorkspace
      initialIdentity={{
        email: identity.email,
        subject: identity.subject,
        tenantId: identity.tenantId
      }}
    />
  );
}
