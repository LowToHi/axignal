import { AuthGate } from "@/components/auth-gate";
import { BillingBridge } from "@/components/billing-bridge";
import { HumanReviewBridge } from "@/components/human-review-bridge";
import { InvestigationShell } from "@/components/investigation-shell";
import { ResearchProgressBridge } from "@/components/research-progress-bridge";
import { SeatGovernanceBridge } from "@/components/seat-governance-bridge";
import {
  getAuthenticatedIdentity,
  isAuthenticationRequired,
  isSeatGovernanceUiEnabled
} from "@/lib/server-auth";

export const dynamic = "force-dynamic";

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
  if (!identity) return <AuthGate />;
  return authenticatedShell();
}
