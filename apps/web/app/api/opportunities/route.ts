import { NextResponse } from "next/server";

import { proxyOpportunityRequest } from "../../../lib/opportunity-server";

export async function GET() {
  return proxyOpportunityRequest("/v1/opportunities/sources");
}

export async function POST(request: Request) {
  const body = await request.text();
  const path = new URL(request.url).pathname.replace(
    /^\/api\/opportunities/,
    "/v1/opportunities"
  );
  return proxyOpportunityRequest(path, { method: "POST", body });
}
