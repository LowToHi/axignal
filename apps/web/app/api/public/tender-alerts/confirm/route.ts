import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!apiUrl || process.env.AXIGNAL_TENDER_ALERTS_ENABLED !== "true") {
    return NextResponse.json(
      { error: "Tender alerts are unavailable." },
      { status: 503 }
    );
  }
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }
  try {
    const upstream = await fetch(
      `${apiUrl}/v1/public/tender-alerts/confirm`,
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
        cache: "no-store",
        signal: AbortSignal.timeout(10_000)
      }
    );
    const payload = await upstream
      .json()
      .catch(() => ({ error: "Invalid API response." }));
    return NextResponse.json(payload, {
      status: upstream.status,
      headers: { "cache-control": "no-store" }
    });
  } catch {
    return NextResponse.json(
      { error: "Tender alert confirmation is unavailable." },
      { status: 503 }
    );
  }
}
