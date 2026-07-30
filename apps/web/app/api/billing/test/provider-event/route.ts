import { proxyBillingRequest } from "../../../../../lib/billing-server";

export async function POST(request: Request) {
  const body = await request.text();
  return proxyBillingRequest("/v1/billing/test/provider-event", {
    method: "POST",
    body
  });
}
