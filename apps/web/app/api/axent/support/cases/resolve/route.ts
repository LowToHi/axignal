import { proxyOpportunityRequest } from "../../../../../../lib/opportunity-server";

export const dynamic = "force-dynamic";

/** /api/axent/support/cases/resolve — advance a case + notify. */
export async function POST(request: Request) {
  const body = await request.json();
  return proxyOpportunityRequest("/v1/axent/support/cases/resolve", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}
