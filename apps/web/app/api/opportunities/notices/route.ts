import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

/** /api/opportunities/notices — GET versioned notices. */
export async function GET() {
  return proxyOpportunityRequest("/v1/opportunities/notices");
}
