import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

/** /api/opportunities/opportunities — GET pipeline opportunities. */
export async function GET() {
  return proxyOpportunityRequest("/v1/opportunities/opportunities");
}
