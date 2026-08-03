import type { Metadata } from "next";

import { AxentHelpEntry } from "@/components/axent/axent-help-entry";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Axent Help — AXIGNAL",
  description: "Server-authoritative customer support for AXIGNAL subscribers.",
  robots: { index: false, follow: false, noarchive: true, noimageindex: true }
};

export default function AxentHelpPage() {
  return <AxentHelpEntry />;
}
