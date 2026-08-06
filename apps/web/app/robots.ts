import type { MetadataRoute } from "next";

import { isPublicOrganicIndexingEnabled } from "@/lib/organic-server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function robots(): MetadataRoute.Robots {
  const siteUrl = (
    process.env.AXIGNAL_PUBLIC_SITE_URL ?? "https://axignal.com"
  ).replace(/\/$/, "");
  const privatePaths = [
    "/admin/",
    "/api/",
    "/search/",
    "/workspace/",
    "/account/",
    "/accept-invitation/",
    "/verify-email/",
    "/alerts/confirm/"
  ];
  if (!isPublicOrganicIndexingEnabled()) {
    return {
      rules: { userAgent: "*", disallow: "/" },
      host: siteUrl
    };
  }
  return {
    rules: [
      {
        userAgent: "Googlebot",
        allow: "/",
        disallow: privatePaths
      },
      {
        userAgent: "Bingbot",
        allow: "/",
        disallow: privatePaths
      },
      {
        userAgent: "OAI-SearchBot",
        allow: "/",
        disallow: privatePaths
      },
      { userAgent: "GPTBot", disallow: "/" },
      { userAgent: "*", allow: "/", disallow: privatePaths }
    ],
    sitemap: `${siteUrl}/sitemap.xml`,
    host: siteUrl
  };
}
