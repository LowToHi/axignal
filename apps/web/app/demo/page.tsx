import { AuthGate } from "@/components/auth-gate";
import { DemoGuide } from "@/components/demo-guide";
import { HumanReviewBridge } from "@/components/human-review-bridge";
import { InvestigationShell } from "@/components/investigation-shell";
import { ResearchProgressBridge } from "@/components/research-progress-bridge";
import { getAuthenticatedIdentity, isAuthenticationRequired } from "@/lib/server-auth";

function demoShell() {
  return (
    <main>
      <DemoGuide />
      <ResearchProgressBridge />
      <HumanReviewBridge />
      <InvestigationShell />
    </main>
  );
}

export default async function DemoPage() {
  if (!isAuthenticationRequired()) return demoShell();
  const identity = await getAuthenticatedIdentity();
  if (!identity) return <AuthGate />;
  return demoShell();
}
