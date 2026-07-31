import {
  fetchDiscoverySitemap,
  isPublicOrganicIndexingEnabled
} from "@/lib/organic-server";

export async function GET() {
  const siteUrl = (
    process.env.AXIGNAL_PUBLIC_SITE_URL ?? "https://axignal.com"
  ).replace(/\/$/, "");
  if (!isPublicOrganicIndexingEnabled()) {
    return new Response(
      "# AXIGNAL\n\nPublic organic discovery is not currently authorised.\n",
      {
        status: 200,
        headers: {
          "content-type": "text/plain; charset=utf-8",
          "cache-control": "no-store",
          "x-robots-tag": "noindex, nofollow"
        }
      }
    );
  }
  const entries = await fetchDiscoverySitemap();
  const urls = entries
    .slice(0, 200)
    .map((entry) => `- ${siteUrl}${entry.canonical_path}`)
    .join("\n");
  const body = `# AXIGNAL

AXIGNAL publishes governed Business-to-Government opportunity intelligence.

## Public information contract

- Every listed page has passed indexability-gate@1.0.0.
- Every public metric belongs to a versioned, expiring snapshot.
- Source coverage and freshness limits remain visible.
- Missing values are not silently estimated.
- AI-generated summaries do not replace source records.
- Citation of AXIGNAL content does not imply endorsement by AXIGNAL.
- Public alert subscriptions do not create accounts, tenants or trials.

## Crawl and use

- OAI-SearchBot, Googlebot and Bingbot may discover public intelligence pages.
- GPTBot is disallowed by robots.txt for model-training access.
- Private product, admin, API, account and workspace routes are excluded.

## Current admitted public pages

${urls || "- No public snapshots are currently admitted."}

## Sitemap

- ${siteUrl}/sitemap.xml
`;
  return new Response(body, {
    status: 200,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "public, max-age=300, stale-while-revalidate=3600"
    }
  });
}
