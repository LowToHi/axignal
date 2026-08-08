import type { Metadata } from "next";
import { LandingExperience } from "@/components/landing-experience";
import { getMessages } from "@/lib/i18n";
import { buildLandingMetadata, buildStructuredData } from "@/lib/metadata";

export const metadata: Metadata = buildLandingMetadata("en");

export default async function LandingPage() {
  const structuredData = buildStructuredData("en");
  const { cookies } = await import("next/headers");
  const session = (await cookies()).get("axignal_session")?.value;

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData).replace(/</g, "\\u003c") }}
      />
      <LandingExperience
        locale="en"
        messages={getMessages("en")}
        hasSession={Boolean(session)}
      />
    </>
  );
}
