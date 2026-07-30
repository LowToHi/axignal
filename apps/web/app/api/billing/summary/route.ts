import { proxyBillingRequest } from "../../../../lib/billing-server";

export async function GET() {
  return proxyBillingRequest("/v1/billing/summary");
}
