import type { Metadata } from "next";
import { PolicyPage } from "@/components/policy-page";

export const metadata: Metadata = {
  title: "Accessibility",
  description: "AXIGNAL landing accessibility commitment and current implementation."
};

export default function AccessibilityPage() {
  return (
    <PolicyPage eyebrow="ACCESSIBILITY" title="Designed for equivalent access" updated="29 July 2026">
      <h2>Current implementation</h2>
      <p>
        The landing targets WCAG 2.2 AA with semantic headings, keyboard-operable controls, visible focus, native
        form fields, live status messages, reduced-motion support and text labels in addition to colour.
      </p>
      <h2>Globe alternative</h2>
      <p>
        The WebGL Globe has a source-state table carrying the same source, jurisdiction and state information.
        Low-capability devices receive a static poster and retain all surrounding content.
      </p>
      <h2>Report a barrier</h2>
      <p>
        Accessibility review is continuous. The public contact channel must be configured and independently
        verified before this page is treated as a final conformance statement.
      </p>
    </PolicyPage>
  );
}
