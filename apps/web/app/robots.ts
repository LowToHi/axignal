import type { MetadataRoute } from "next";

import { isPublicOrganicIndexingEnabled } from "@/lib/organic-server";

export default function robots(): MetadataRoute.Robots {
  const siteUrl = (process.env.AXIGNAL_PUBLIC_SITE_URL ?? "https://axignal.com").replace(/\/$/, "");
  const privatePaths = ["/admin/", "/api/", "/search/", "/workspace/", "/account/"];
  if (!isPublicOrganicIndexingEnabled()) {
    return { rules: { userAgent: "*", disallow: "/" }, host: siteUrl };
  }
  return {
    rules: [
      { userAgent: ["Googlebot", "Bingbot", "OAI-SearchBot"], allow: "/", disallow: privatePaths },
      { userAgent: "GPTBot", disallow: "/" },
      { userAgent: "*", allow: "/", disallow: privatePaths }
    ],
    sitemap: `${siteUrl}/sitemap.xml`,
    host: siteUrl
  };
}
