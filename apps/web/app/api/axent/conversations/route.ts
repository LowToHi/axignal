import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

/** /api/axent/conversations — GET list, POST create. */
export async function GET() {
  return proxyOpportunityRequest("/v1/axent/conversations");
}

export async function POST(request: Request) {
  return proxyOpportunityRequest("/v1/axent/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(await request.json()),
  });
}
