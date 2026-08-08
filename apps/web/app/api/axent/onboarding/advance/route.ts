import { proxyOpportunityRequest } from "../../../../../lib/opportunity-server";

export const dynamic = "force-dynamic";

/** /api/axent/onboarding/advance — advance the journey (idempotent). */
export async function POST() {
  return proxyOpportunityRequest("/v1/axent/onboarding/advance", {
    method: "POST",
  });
}
