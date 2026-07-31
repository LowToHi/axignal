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
  const page = await fetchPublicDiscoveryPage("MARKET_INTELLIGENCE", country, sector);
  if (!page) {
    return { title: "Not found — AXIGNAL", robots: { index: false, follow: false } };
  }
  const siteUrl = (process.env.AXIGNAL_PUBLIC_SITE_URL ?? "https://axignal.com").replace(/\/$/, "");
  return {
    title: page.title,
    description: page.description,
    alternates: { canonical: `${siteUrl}${page.canonical_path}` },
    robots: { index: true, follow: true, googleBot: { index: true, follow: true, maxSnippet: -1, maxImagePreview: "large" } },
    openGraph: { type: "article", title: page.title, description: page.description, url: `${siteUrl}${page.canonical_path}`, siteName: "AXIGNAL", modifiedTime: page.freshness_at }
  };
}

export default async function MarketIntelligencePage({
  params
}: {
  params: Promise<{ country: string; sector: string }>;
}) {
  const { country, sector } = await params;
  const page = await fetchPublicDiscoveryPage("MARKET_INTELLIGENCE", country, sector);
  if (!page) notFound();
  return <DiscoveryView page={page} />;
}
