import { NextResponse } from "next/server";

import { proxySubscriberJson } from "@/lib/subscriber-live-server";

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function GET(
  _request: Request,
  context: { params: Promise<{ researchRunId: string }> }
) {
  const { researchRunId } = await context.params;
  if (!uuidPattern.test(researchRunId)) {
    return NextResponse.json(
      { error: "Invalid ResearchRun identifier." },
      { status: 400 }
    );
  }
  return proxySubscriberJson(`/v1/research-runs/${researchRunId}`);
}
