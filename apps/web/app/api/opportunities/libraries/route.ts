import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

export async function GET() {
  return proxyOpportunityRequest("/v1/opportunities/libraries");
}
