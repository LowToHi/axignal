import { AuthGate } from "@/components/auth-gate";
import { HumanReviewBridge } from "@/components/human-review-bridge";
import { InvestigationShell } from "@/components/investigation-shell";
import { ResearchProgressBridge } from "@/components/research-progress-bridge";
import { getAuthenticatedIdentity, isAuthenticationRequired } from "@/lib/server-auth";

function authenticatedShell() {
  return (
    <>
      <ResearchProgressBridge />
      <HumanReviewBridge />
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
