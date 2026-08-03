import { proxySubscriberJson } from "@/lib/subscriber-live-server";

export async function POST(
  _request: Request,
  context: { params: Promise<{ notificationId: string }> }
) {
  const { notificationId } = await context.params;
  return proxySubscriberJson(
    `/v1/axent/notifications/${encodeURIComponent(notificationId)}/acknowledge`,
    { method: "POST", body: "{}" }
  );
}
