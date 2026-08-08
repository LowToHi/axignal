import { cookies } from "next/headers";

import { AuthGate } from "@/components/auth-gate";
import { BillingBridge } from "@/components/billing-bridge";
import { HumanReviewBridge } from "@/components/human-review-bridge";
import { InvestigationShell } from "@/components/investigation-shell";
import { ResearchProgressBridge } from "@/components/research-progress-bridge";
import { SeatGovernanceBridge } from "@/components/seat-governance-bridge";
import {
  getAuthenticatedIdentity,
  isAuthenticationRequired,
  isPasswordlessIdentityEnabled,
  isSeatGovernanceUiEnabled,
} from "@/lib/server-auth";

import { SubscriberWorkspaceApp } from "./subscriber-workspace-app";
import {
  shellLocales,
  type ShellLocale,
} from "./subscriber-localization";

function boolEnv(name: string): boolean {
  return ["1", "true", "yes", "on", "explicit"].includes(
    (process.env[name] ?? "").trim().toLowerCase(),
  );
}

function subscriberWorkspaceEnabled(): boolean {
  return boolEnv("AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED");
}

function isShellLocale(value: string | undefined): value is ShellLocale {
  return shellLocales.includes(value as ShellLocale);
}

function legacyShell() {
  return (
    <>
      <ResearchProgressBridge />
      <HumanReviewBridge />
      <BillingBridge />
      {isSeatGovernanceUiEnabled() && <SeatGovernanceBridge />}
      <InvestigationShell />
    </>
  );
}

export async function SubscriberEntry({
  legacyRootInTestRuntime = false,
}: {
  legacyRootInTestRuntime?: boolean;
}) {
  const testRuntime = boolEnv("AXIGNAL_TEST_RUNTIME_ENABLED");
  const canonicalLegacyRoot =
    testRuntime &&
    legacyRootInTestRuntime &&
    boolEnv("AXIGNAL_CANONICAL_LEGACY_ROOT_TEST_ENABLED");

  if (canonicalLegacyRoot) return legacyShell();

  const authRequired = isAuthenticationRequired();
  const identity = authRequired ? await getAuthenticatedIdentity() : null;

  if (authRequired && !identity) {
    const cookieStore = await cookies();
    const storedLocale = cookieStore.get("axignal_locale")?.value;
    const locale = isShellLocale(storedLocale) ? storedLocale : "en";
    const turnstileSiteKey =
      process.env.NEXT_PUBLIC_AXIGNAL_TURNSTILE_SITE_KEY;

    return (
      <AuthGate
        passwordless={isPasswordlessIdentityEnabled()}
        testRuntime={testRuntime}
        locale={locale}
        {...(turnstileSiteKey ? { turnstileSiteKey } : {})}
      />
    );
  }

  if (!subscriberWorkspaceEnabled()) return legacyShell();

  const explicitFixture =
    (process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_FIXTURE_MODE ?? "")
      .trim()
      .toLowerCase() === "explicit";

  return (
    <SubscriberWorkspaceApp
      serverIdentity={
        identity
          ? {
              name: identity.email.split("@")[0] ?? "Subscriber",
              email: identity.email,
              organisation: "AXIGNAL Pilot Organisation",
              roles: identity.roles?.length ? identity.roles : ["OWNER"],
              entitlementLabel: "Professional · candidate",
            }
          : explicitFixture
            ? {
                name: "Alex Morgan",
                email: "alex.morgan@example.invalid",
                organisation: "Northstar Public Systems",
                roles: ["OWNER", "BID_MANAGER"],
                entitlementLabel: "Professional · engineering fixture",
              }
            : null
      }
    />
  );
}
