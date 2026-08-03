import type { Metadata } from "next";

import { AuthGate } from "@/components/auth-gate";
import { AxentAdminConsole } from "@/components/axent/axent-admin-console";
import { getAuthenticatedIdentity, isPasswordlessIdentityEnabled } from "@/lib/server-auth";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Axent Support Console",
  description: "Human-authority support escalation console.",
  robots: { index: false, follow: false, noarchive: true, noimageindex: true }
};

export default async function SupportAdminPage() {
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    return (
      <AuthGate
        passwordless={isPasswordlessIdentityEnabled()}
        testRuntime={false}
      />
    );
  }
  return <AxentAdminConsole />;
}
