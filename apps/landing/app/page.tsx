import type { Metadata } from "next";
import { LandingExperience } from "@/components/landing-experience";
import { getMessages } from "@/lib/i18n";
import { buildLandingMetadata, buildStructuredData } from "@/lib/metadata";

export const metadata: Metadata = buildLandingMetadata("en");

export default function LandingPage() {
  const structuredData = buildStructuredData("en");

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData).replace(/</g, "\\u003c") }}
      />
      <LandingExperience locale="en" messages={getMessages("en")} />
    </>
  );
}
