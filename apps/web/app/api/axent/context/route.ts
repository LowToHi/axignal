import { proxyOpportunityRequest } from "../../../../lib/opportunity-server";

/** /api/axent/context — server-authoritative context. */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const route = url.searchParams.get("route") ?? undefined;
  const opportunityRef = url.searchParams.get("opportunity_ref") ?? undefined;
  const pursuitRef = url.searchParams.get("pursuit_ref") ?? undefined;
  const params = new URLSearchParams();
  if (route) params.set("route", route);
  if (opportunityRef) params.set("opportunity_ref", opportunityRef);
  if (pursuitRef) params.set("pursuit_ref", pursuitRef);
  const query = params.toString();
  return proxyOpportunityRequest(`/v1/axent/context${query ? `?${query}` : ""}`);
}
