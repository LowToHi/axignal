import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

/** /api/opportunities/portfolio — GET list, POST add. */
export async function GET() {
  return proxyOpportunityRequest("/v1/opportunities/portfolio");
}

export async function POST(request: Request) {
  const body = await request.text();
  return proxyOpportunityRequest("/v1/opportunities/portfolio", {
    method: "POST",
    body
  });
}
