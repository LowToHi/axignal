import { AuthGate } from "@/components/auth-gate";
import { InvestigationShell } from "@/components/investigation-shell";
import { ResearchProgressBridge } from "@/components/research-progress-bridge";
import { getAuthenticatedIdentity, isAuthenticationRequired } from "@/lib/server-auth";

function authenticatedShell() {
  return (
    <>
      <ResearchProgressBridge />
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
