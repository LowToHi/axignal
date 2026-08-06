import type { Metadata } from "next";
import { PolicyPage } from "@/components/policy-page";

export const metadata: Metadata = {
  title: "Terms",
  description: "Current public-use boundaries for the AXIGNAL landing."
};

export default function TermsPage() {
  return (
    <PolicyPage eyebrow="PUBLIC-USE BOUNDARY" title="Current landing terms summary" updated="29 July 2026">
      <h2>Information surface</h2>
      <p>
        AXIGNAL is an information, research, observation and exploration platform. It does not execute
        transactions, submit procurement responses, guarantee outcomes or provide personally suitable advice.
      </p>
      <h2>Demonstration content</h2>
      <p>
        Product examples, opportunity dossiers, values, dates and impact outputs on the landing are synthetic or
        based solely on visitor inputs. The source catalogue is research inventory, not supported coverage.
      </p>
      <h2>Commercial state</h2>
      <p>
        Packaging and prices are candidate hypotheses. No checkout, trial, subscription or entitlement is created
        by this landing.
      </p>
      <p>
        These implementation terms require independent legal review before commercial acceptance and are not
        represented as final customer terms.
      </p>
    </PolicyPage>
  );
}
