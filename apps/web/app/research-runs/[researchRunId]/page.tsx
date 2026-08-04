import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { AuthGate } from "@/components/auth-gate";
import { ResearchRunPage } from "@/components/subscriber/research-run-page";
import {
  getAuthenticatedIdentity,
  isAuthenticationRequired,
  isPasswordlessIdentityEnabled
} from "@/lib/server-auth";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Persistent ResearchRun · AXIGNAL",
  description: "Server-authoritative AXIGNAL ResearchRun status and evidence.",
  robots: { index: false, follow: false, noarchive: true, noimageindex: true }
};

const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function boolEnv(name: string): boolean {
  return ["1", "true", "yes", "on"].includes(
    (process.env[name] ?? "").trim().toLowerCase()
  );
}

export default async function PersistentResearchRunRoute({
  params
}: {
  params: Promise<{ researchRunId: string }>;
}) {
  const { researchRunId } = await params;
  if (!uuidPattern.test(researchRunId)) notFound();

  const authRequired = isAuthenticationRequired();
  const identity = authRequired ? await getAuthenticatedIdentity() : null;
  if (authRequired && !identity) {
    const turnstileSiteKey = process.env.NEXT_PUBLIC_AXIGNAL_TURNSTILE_SITE_KEY;
    return (
      <AuthGate
        passwordless={isPasswordlessIdentityEnabled()}
        testRuntime={boolEnv("AXIGNAL_TEST_RUNTIME_ENABLED")}
        {...(turnstileSiteKey ? { turnstileSiteKey } : {})}
      />
    );
  }

  return <ResearchRunPage researchRunId={researchRunId} />;
}
