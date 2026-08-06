import { proxySubscriberJson } from "@/lib/subscriber-live-server";

export async function POST(request: Request) {
  const body = await request.text();
  return proxySubscriberJson("/v1/subscriber-workspace/research-runs", {
    method: "POST",
    body
  });
}
