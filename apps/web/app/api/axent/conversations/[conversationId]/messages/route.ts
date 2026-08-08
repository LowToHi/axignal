import { proxyOpportunityRequest } from "../../../../../../lib/opportunity-server";

type Params = { params: Promise<{ conversationId: string }> };

/** /api/axent/conversations/[conversationId]/messages — GET + POST. */
export async function GET(_request: Request, { params }: Params) {
  const { conversationId } = await params;
  return proxyOpportunityRequest(
    `/v1/axent/conversations/${conversationId}/messages`
  );
}

export async function POST(request: Request, { params }: Params) {
  const { conversationId } = await params;
  return proxyOpportunityRequest(
    `/v1/axent/conversations/${conversationId}/messages`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(await request.json()),
    }
  );
}
