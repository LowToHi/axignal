import { proxyOpportunityRequest } from "../../../../../lib/opportunity-server";

export const dynamic = "force-dynamic";

/** /api/axent/support/cases — list cases (optionally by status). */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const status = url.searchParams.get("status") ?? undefined;
  return proxyOpportunityRequest(
    `/v1/axent/support/cases${status ? `?status=${status}` : ""}`
  );
}

/** /api/axent/support/cases — create a support case (round-trip). */
export async function POST(request: Request) {
  const body = await request.json();
  return proxyOpportunityRequest("/v1/axent/support/cases", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}
