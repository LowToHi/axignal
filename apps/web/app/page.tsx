import { AuthGate } from "@/components/auth-gate";
import { InvestigationShell } from "@/components/investigation-shell";
import { getAuthenticatedIdentity, isAuthenticationRequired } from "@/lib/server-auth";

export default async function HomePage() {
  if (!isAuthenticationRequired()) return <InvestigationShell />;
  const identity = await getAuthenticatedIdentity();
  if (!identity) return <AuthGate />;
  return <InvestigationShell />;
}
