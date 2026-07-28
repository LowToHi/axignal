import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    service: "axignal-web",
    pilotMode: process.env.AXIGNAL_PILOT_MODE === "true",
    buildSha: process.env.AXIGNAL_BUILD_SHA ?? "unknown"
  });
}
