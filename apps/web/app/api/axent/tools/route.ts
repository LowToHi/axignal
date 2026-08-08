import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

/** /api/axent/tools — typed tool registry. */
export async function GET() {
  return proxyOpportunityRequest("/v1/axent/tools");
}
