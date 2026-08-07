import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

/** /api/opportunities/workspaces — GET list, POST create. */
export async function GET() {
  return proxyOpportunityRequest("/v1/opportunities/workspaces");
}

export async function POST(request: Request) {
  const body = await request.text();
  return proxyOpportunityRequest("/v1/opportunities/workspaces", {
    method: "POST",
    body
  });
}
