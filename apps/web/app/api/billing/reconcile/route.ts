import { proxyBillingRequest } from "../../../../lib/billing-server";

export async function POST() {
  return proxyBillingRequest("/v1/billing/subscription/reconcile", {
    method: "POST"
  });
}
