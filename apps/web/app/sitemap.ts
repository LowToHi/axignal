import type { MetadataRoute } from "next";

import {
  fetchDiscoverySitemap,
  isPublicOrganicIndexingEnabled
} from "@/lib/organic-server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  if (!isPublicOrganicIndexingEnabled()) return [];
  const siteUrl = (
    process.env.AXIGNAL_PUBLIC_SITE_URL ?? "https://axignal.com"
  ).replace(/\/$/, "");
  const entries = await fetchDiscoverySitemap();
  return entries.map((entry) => ({
    url: `${siteUrl}${entry.canonical_path}`,
    lastModified: new Date(entry.last_modified_at),
    changeFrequency: entry.change_frequency,
    priority: Number(entry.priority)
  }));
}
