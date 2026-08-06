import { NextResponse } from "next/server";

import { proxySubscriberDownload } from "@/lib/subscriber-live-server";

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function GET(
  _request: Request,
  context: { params: Promise<{ exportId: string }> }
) {
  const { exportId } = await context.params;
  if (!uuidPattern.test(exportId)) {
    return NextResponse.json(
      { error: "Invalid export identifier." },
      { status: 400 }
    );
  }
  return proxySubscriberDownload(
    `/v1/subscriber-workspace/exports/${exportId}/download`
  );
}
