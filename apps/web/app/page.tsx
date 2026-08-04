import type { Metadata } from "next";

import { SubscriberEntry } from "@/components/subscriber/subscriber-entry";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "AXIGNAL Workspace",
  description: "Private AXIGNAL B2G investigation workspace.",
  robots: {
    index: false,
    follow: false,
    noarchive: true,
    noimageindex: true
  }
};

export default async function HomePage() {
  return <SubscriberEntry legacyRootInTestRuntime />;
}
