import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  return NextResponse.json(
    {
      status: "ok",
      service: "axignal-landing",
      buildSha: process.env.AXIGNAL_BUILD_SHA ?? "unknown",
      intakeConfigured: Boolean(
        process.env.AXIGNAL_PILOT_INTAKE_FILE || process.env.AXIGNAL_PILOT_INTAKE_WEBHOOK_URL
      )
    },
    { headers: { "cache-control": "no-store" } }
  );
}
