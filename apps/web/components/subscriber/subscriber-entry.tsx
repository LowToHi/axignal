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
  isSeatGovernanceUiEnabled
} from "@/lib/server-auth";

import { SubscriberWorkspaceApp } from "./subscriber-workspace-app";

function boolEnv(name: string): boolean {
  return ["1", "true", "yes", "on", "explicit"].includes((process.env[name] ?? "").trim().toLowerCase());
}

function subscriberWorkspaceEnabled(): boolean {
  return boolEnv("AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED");
}

function legacyShell() {
  return <><ResearchProgressBridge /><HumanReviewBridge /><BillingBridge />{isSeatGovernanceUiEnabled() && <SeatGovernanceBridge />}<InvestigationShell /></>;
}

export async function SubscriberEntry() {
  if (!subscriberWorkspaceEnabled()) return legacyShell();
  const authRequired = isAuthenticationRequired();
  const identity = authRequired ? await getAuthenticatedIdentity() : null;
  const explicitFixture = (process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_FIXTURE_MODE ?? "").trim().toLowerCase() === "explicit";

  if (authRequired && !identity) {
    const turnstileSiteKey = process.env.NEXT_PUBLIC_AXIGNAL_TURNSTILE_SITE_KEY;
    return <AuthGate passwordless={isPasswordlessIdentityEnabled()} testRuntime={boolEnv("AXIGNAL_TEST_RUNTIME_ENABLED")} {...(turnstileSiteKey ? { turnstileSiteKey } : {})} />;
  }

  return <SubscriberWorkspaceApp
    serverIdentity={identity ? {
      name: identity.email.split("@")[0] ?? "Subscriber",
      email: identity.email,
      organisation: "AXIGNAL Pilot Organisation",
      roles: identity.roles?.length ? identity.roles : ["OWNER"],
      entitlementLabel: "Professional · candidate"
    } : explicitFixture ? {
      name: "Alex Morgan",
      email: "alex.morgan@example.invalid",
      organisation: "Northstar Public Systems",
      roles: ["OWNER", "BID_MANAGER"],
      entitlementLabel: "Professional · engineering fixture"
    } : null}
  />;
}
