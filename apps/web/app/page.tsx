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

export const dynamic = "force-dynamic";

function boolEnv(name: string): boolean {
  return ["1", "true", "yes", "on"].includes(
    (process.env[name] ?? "").trim().toLowerCase()
  );
}

function authenticatedShell() {
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

export default async function HomePage() {
  if (!isAuthenticationRequired()) return authenticatedShell();
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    const turnstileSiteKey =
      process.env.NEXT_PUBLIC_AXIGNAL_TURNSTILE_SITE_KEY;
    return (
      <AuthGate
        passwordless={isPasswordlessIdentityEnabled()}
        testRuntime={boolEnv("AXIGNAL_TEST_RUNTIME_ENABLED")}
        {...(turnstileSiteKey ? { turnstileSiteKey } : {})}
      />
    );
  }
  return authenticatedShell();
}
