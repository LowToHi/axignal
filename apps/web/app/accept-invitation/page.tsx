import { AuthGate } from "@/components/auth-gate";
import { AcceptInvitationClient } from "@/components/accept-invitation-client";
import { getAuthenticatedIdentity } from "@/lib/server-auth";

export const dynamic = "force-dynamic";

export default async function AcceptInvitationPage({
  searchParams
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const { token } = await searchParams;
  if (!token) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <h1>Invitation token missing</h1>
        </section>
      </main>
    );
  }
  const identity = await getAuthenticatedIdentity();
  if (!identity) return <AuthGate />;
  return <AcceptInvitationClient token={token} />;
}
