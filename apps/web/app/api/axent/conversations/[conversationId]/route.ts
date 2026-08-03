import { proxyAxentJson } from "@/lib/axent-server";

export async function GET(
  _request: Request,
  context: { params: Promise<{ conversationId: string }> }
) {
  const { conversationId } = await context.params;
  return proxyAxentJson(`/v1/axent/conversations/${conversationId}`);
}
