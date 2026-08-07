import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

/** /api/opportunities/pursuits — GET list, POST create. */
export async function GET() {
  return proxyOpportunityRequest("/v1/opportunities/pursuits");
}

export async function POST(request: Request) {
  const body = await request.text();
  return proxyOpportunityRequest("/v1/opportunities/pursuits", {
    method: "POST",
    body
  });
}
