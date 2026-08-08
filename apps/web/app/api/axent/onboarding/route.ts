import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

export const dynamic = "force-dynamic";

/** /api/axent/onboarding — current journey + preferences. */
export async function GET() {
  return proxyOpportunityRequest("/v1/axent/onboarding");
}

/** /api/axent/onboarding — persist an explicitly confirmed preference. */
export async function POST(request: Request) {
  const body = await request.json();
  return proxyOpportunityRequest("/v1/axent/onboarding/preferences", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}
