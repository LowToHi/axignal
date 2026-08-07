import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

/** /api/opportunities/learnings — GET list, POST create. */
export async function GET() {
  return proxyOpportunityRequest("/v1/opportunities/learnings");
}

export async function POST(request: Request) {
  const body = await request.text();
  return proxyOpportunityRequest("/v1/opportunities/learnings", {
    method: "POST",
    body
  });
}
