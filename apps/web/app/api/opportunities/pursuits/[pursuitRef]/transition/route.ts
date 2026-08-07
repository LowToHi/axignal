import { proxyOpportunityRequest } from "../../../../../../lib/opportunity-server";

type Params = { params: Promise<{ pursuitRef: string }> };

export async function POST(request: Request, { params }: Params) {
  const { pursuitRef } = await params;
  const body = await request.text();
  return proxyOpportunityRequest(
    `/v1/opportunities/pursuits/${pursuitRef}/transition`,
    { method: "POST", body }
  );
}
