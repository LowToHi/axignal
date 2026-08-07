import { proxyOpportunityRequest } from "../../../../../../lib/opportunity-server";

type Params = { params: Promise<{ opportunityRef: string }> };

/** /api/opportunities/opportunities/[opportunityRef]/qualify — POST bid/no-bid. */
export async function POST(request: Request, { params }: Params) {
  const { opportunityRef } = await params;
  const body = await request.text();
  return proxyOpportunityRequest(
    `/v1/opportunities/opportunities/${opportunityRef}/qualify`,
    { method: "POST", body }
  );
}
