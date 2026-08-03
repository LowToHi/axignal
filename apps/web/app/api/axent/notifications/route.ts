import { proxySubscriberJson } from "@/lib/subscriber-live-server";

export async function GET() {
  return proxySubscriberJson("/v1/axent/notifications");
}
