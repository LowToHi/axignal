import { createHash } from "node:crypto";

import {
  buildApiIdentityAssertion,
  type AuthenticatedIdentity
} from "./server-auth";

export type DiscoveryPageKind =
  | "TENDER_HUB"
  | "MARKET_INTELLIGENCE"
  | "TENDER_DETAIL";

export type PublicDiscoveryPage = {
  page_id: string;
  page_kind: DiscoveryPageKind;
  locale: string;
  country_code: string;
  country_slug: string;
  sector_slug: string;
  canonical_path: string;
  title: string;
  description: string;
  state: "PUBLISHED";
  active_opportunity_count: number;
  unique_buyer_count: number;
  known_value_microunits: number;
  freshness_at: string;
  methodology_version: string;
  source_count: number;
  metrics: Record<string, unknown>;
  source_urls: string[];
  snapshot_version: number;
  published_at: string;
  expires_at: string;
};

export type SeoPageCandidate = {
  page_id: string;
  page_kind: DiscoveryPageKind;
  locale: string;
  country_code: string;
  country_slug: string;
  sector_slug: string;
  canonical_path: string;
  title: string;
  state: string;
  active_opportunity_count: number;
  unique_buyer_count: number;
  demand_score: number | string;
  data_quality_score: number | string;
  uniqueness_score: number | string;
  source_coverage_score: number | string;
  content_depth_score: number | string;
  freshness_at: string;
  is_synthetic: boolean;
  updated_at: string;
};

export type FounderOverview = {
  seo: Record<string, number>;
  crm: Record<string, number>;
  alerts: Record<string, number>;
  citations: Record<string, number>;
  truth_boundaries: string[];
};

export type FounderAdminData = {
  overview: FounderOverview;
  pages: SeoPageCandidate[];
  contacts: Array<Record<string, unknown>>;
  alerts: Array<Record<string, unknown>>;
  generatedAt: string;
};

function apiUrl(): string | null {
  return process.env.AXIGNAL_API_URL?.replace(/\/$/, "") ?? null;
}

function boolEnv(name: string): boolean {
  return ["1", "true", "yes", "on"].includes(
    (process.env[name] ?? "").trim().toLowerCase()
  );
}

export function isPublicOrganicIndexingEnabled(): boolean {
  return boolEnv("AXIGNAL_ORGANIC_PUBLIC_INDEXING_ENABLED");
}

export function isFounderIdentity(identity: AuthenticatedIdentity): boolean {
  const subjects = new Set(
    (process.env.AXIGNAL_FOUNDER_SUBJECTS ?? "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
  );
  return subjects.has(identity.subject) && identity.assuranceLevel === "AAL2";
}

async function publicJson<T>(path: string): Promise<T | null> {
  const base = apiUrl();
  if (!base || !isPublicOrganicIndexingEnabled()) return null;
  try {
    const response = await fetch(`${base}${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5_000)
    });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function fetchPublicDiscoveryPage(
  kind: DiscoveryPageKind,
  countrySlug: string,
  sectorSlug: string,
  locale = "en"
): Promise<PublicDiscoveryPage | null> {
  const safeSlug = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  if (!safeSlug.test(countrySlug) || !safeSlug.test(sectorSlug)) return null;
  return publicJson<PublicDiscoveryPage>(
    `/v1/public/discovery/${kind}/${countrySlug}/${sectorSlug}?locale=${encodeURIComponent(locale)}`
  );
}

export async function fetchDiscoverySitemap(): Promise<
  Array<{
    canonical_path: string;
    locale: string;
    change_frequency: "hourly" | "daily" | "weekly" | "monthly";
    priority: number | string;
    last_modified_at: string;
  }>
> {
  return (
    (await publicJson<
      Array<{
        canonical_path: string;
        locale: string;
        change_frequency: "hourly" | "daily" | "weekly" | "monthly";
        priority: number | string;
        last_modified_at: string;
      }>
    >("/v1/public/discovery-sitemap")) ?? []
  );
}

async function founderJson<T>(
  identity: AuthenticatedIdentity,
  path: string,
  init?: RequestInit
): Promise<T> {
  if (!isFounderIdentity(identity)) throw new Error("FOUNDER_ADMIN_REQUIRED");
  const base = apiUrl();
  if (!base) throw new Error("AXIGNAL_API_URL_REQUIRED");
  const headers = new Headers(init?.headers);
  headers.set("X-AXIGNAL-Identity-Assertion", buildApiIdentityAssertion(identity));
  if (init?.body) headers.set("content-type", "application/json");
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers,
    cache: "no-store",
    signal: AbortSignal.timeout(10_000)
  });
  if (!response.ok) throw new Error(`FOUNDER_API_${response.status}`);
  return (await response.json()) as T;
}

export async function fetchFounderAdminData(
  identity: AuthenticatedIdentity
): Promise<FounderAdminData> {
  const [overview, pages, contacts, alerts] = await Promise.all([
    founderJson<FounderOverview>(identity, "/v1/admin/overview"),
    founderJson<SeoPageCandidate[]>(identity, "/v1/admin/seo/pages"),
    founderJson<Array<Record<string, unknown>>>(identity, "/v1/admin/crm/contacts"),
    founderJson<Array<Record<string, unknown>>>(identity, "/v1/admin/tender-alerts")
  ]);
  return {
    overview,
    pages,
    contacts,
    alerts,
    generatedAt: new Date().toISOString()
  };
}

export async function mutateFounderAdmin(
  identity: AuthenticatedIdentity,
  action: "evaluate" | "publish" | "record-citation" | "test-bootstrap",
  payload: Record<string, unknown>
): Promise<Record<string, unknown>> {
  if (action === "test-bootstrap") {
    return founderJson(identity, "/v1/admin/test/bootstrap-founder", {
      method: "POST",
      body: "{}"
    });
  }
  if (action === "record-citation") {
    return founderJson(identity, "/v1/admin/ai-citations", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }
  const pageId = typeof payload.pageId === "string" ? payload.pageId : "";
  if (!/^[0-9a-f-]{36}$/i.test(pageId)) throw new Error("INVALID_PAGE_ID");
  if (action === "evaluate") {
    return founderJson(identity, `/v1/admin/seo/pages/${pageId}/evaluate`, {
      method: "POST",
      body: "{}"
    });
  }
  const contentHash = createHash("sha256")
    .update(JSON.stringify(payload.snapshot ?? {}))
    .digest("hex");
  return founderJson(identity, `/v1/admin/seo/pages/${pageId}/publish`, {
    method: "POST",
    body: JSON.stringify({
      content_hash: contentHash,
      ttl_hours: 24,
      confirm_publication: true
    })
  });
}
