import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

/** /api/axent/query — standalone RAG query. */
export async function POST(request: Request) {
  return proxyOpportunityRequest("/v1/axent/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(await request.json()),
  });
}
