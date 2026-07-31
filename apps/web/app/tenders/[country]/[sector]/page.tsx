import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { DiscoveryView } from "@/components/discovery-view";
import { fetchPublicDiscoveryPage } from "@/lib/organic-server";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params
}: {
  params: Promise<{ country: string; sector: string }>;
}): Promise<Metadata> {
  const { country, sector } = await params;
  const page = await fetchPublicDiscoveryPage("TENDER_HUB", country, sector);
  if (!page) {
    return {
      title: "Not found — AXIGNAL",
      robots: { index: false, follow: false }
    };
  }
  const siteUrl = (
    process.env.AXIGNAL_PUBLIC_SITE_URL ?? "https://axignal.com"
  ).replace(/\/$/, "");
  return {
    title: page.title,
    description: page.description,
    alternates: { canonical: `${siteUrl}${page.canonical_path}` },
    robots: {
      index: true,
      follow: true,
      googleBot: {
        index: true,
        follow: true,
        "max-snippet": -1,
        "max-image-preview": "large"
      }
    },
    openGraph: {
      type: "website",
      title: page.title,
      description: page.description,
      url: `${siteUrl}${page.canonical_path}`,
      siteName: "AXIGNAL"
    }
  };
}

export default async function TenderHubPage({
  params
}: {
  params: Promise<{ country: string; sector: string }>;
}) {
  const { country, sector } = await params;
  const page = await fetchPublicDiscoveryPage("TENDER_HUB", country, sector);
  if (!page) notFound();
  return <DiscoveryView page={page} />;
}
