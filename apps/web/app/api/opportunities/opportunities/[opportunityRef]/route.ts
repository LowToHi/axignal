import { proxyOpportunityRequest } from "../../../../../lib/opportunity-server";

type Params = { params: Promise<{ opportunityRef: string }> };

/** /api/opportunities/opportunities/[opportunityRef] — GET detail. */
export async function GET(_request: Request, { params }: Params) {
  const { opportunityRef } = await params;
  return proxyOpportunityRequest(`/v1/opportunities/opportunities/${opportunityRef}`);
}
