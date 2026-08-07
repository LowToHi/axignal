import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

/** /api/opportunities/outcomes — GET list, POST create. */
export async function GET() {
  return proxyOpportunityRequest("/v1/opportunities/outcomes");
}

export async function POST(request: Request) {
  const body = await request.text();
  return proxyOpportunityRequest("/v1/opportunities/outcomes", {
    method: "POST",
    body
  });
}
