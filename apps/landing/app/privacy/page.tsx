import type { Metadata } from "next";
import { PolicyPage } from "@/components/policy-page";

export const metadata: Metadata = {
  title: "Privacy",
  description: "How the AXIGNAL landing handles Design Partner intake information."
};

export default function PrivacyPage() {
  return (
    <PolicyPage eyebrow="PRIVACY SUMMARY" title="Purpose-limited Design Partner intake" updated="29 July 2026">
      <h2>What we collect</h2>
      <p>
        The Design Partner form collects work contact, organisation, role and procurement-workflow fit
        information so AXIGNAL can assess and respond to the request.
      </p>
      <h2>What analytics receives</h2>
      <p>
        Landing analytics is provider-agnostic and restricted to allowlisted event properties such as locale,
        CTA origin, product chapter, plan label and result category. Form fields, email and organisation are not
        analytics properties.
      </p>
      <h2>Control and retention</h2>
      <p>
        Submitting does not create an account, subscription or standing authority. Retention and deletion are
        governed by the configured intake operator and must be finalised before public commercial operation.
      </p>
      <p>
        This page is an implementation summary and not a substitute for an independently reviewed legal privacy
        notice. Public commercial readiness remains gated.
      </p>
    </PolicyPage>
  );
}
