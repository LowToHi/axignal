import { proxySubscriberJson } from "@/lib/subscriber-live-server";

export async function POST(
  request: Request,
  context: { params: Promise<{ conversationId: string }> }
) {
  const { conversationId } = await context.params;
  const body = await request.text();
  return proxySubscriberJson(
    `/v1/axent/conversations/${encodeURIComponent(conversationId)}/feedback`,
    { method: "POST", body }
  );
}
