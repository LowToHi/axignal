import { randomUUID } from "node:crypto";
import { appendFile, chmod, mkdir } from "node:fs/promises";
import { dirname } from "node:path";

import { NextResponse } from "next/server";

export const runtime = "nodejs";

const roles = new Set([
  "Head of B2G or public-sector sales",
  "Business development",
  "Bid or proposal management",
  "Tender or procurement intelligence",
  "Market expansion or internationalisation",
  "Founder or executive",
  "Advisory or consulting",
  "Other"
]);

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const messageVersionPattern = /^[a-z0-9][a-z0-9._-]{2,63}$/;

type IntakePayload = {
  email?: unknown;
  role?: unknown;
  company?: unknown;
  useCase?: unknown;
  consent?: unknown;
  website?: unknown;
  messageVersion?: unknown;
};

type IntakeRecord = {
  schema: "axignal.b2g-trial-intake.v1";
  submissionId: string;
  submittedAt: string;
  source: "landing_b2g_opportunity_v1_0";
  messageVersion: string;
  email: string;
  role: string;
  company: string | null;
  useCase: string;
  consent: true;
};

function clean(value: unknown, maxLength: number) {
  return typeof value === "string" ? value.trim().slice(0, maxLength) : "";
}

async function persistLocally(filePath: string, record: IntakeRecord) {
  const directory = dirname(filePath);
  await mkdir(directory, { recursive: true, mode: 0o700 });
  await chmod(directory, 0o700);
  await appendFile(filePath, `${JSON.stringify(record)}\n`, {
    encoding: "utf8",
    flag: "a",
    mode: 0o600
  });
  await chmod(filePath, 0o600);
}

export async function POST(request: Request) {
  const contentLength = Number(request.headers.get("content-length") ?? "0");
  if (contentLength > 8_000) {
    return NextResponse.json(
      { status: "rejected", message: "The request exceeds the permitted size." },
      { status: 413 }
    );
  }

  let payload: IntakePayload;
  try {
    payload = (await request.json()) as IntakePayload;
  } catch {
    return NextResponse.json(
      { status: "rejected", message: "A valid JSON request is required." },
      { status: 400 }
    );
  }

  const website = clean(payload.website, 200);
  if (website) {
    return NextResponse.json({ status: "received", message: "Request received." }, { status: 202 });
  }

  const email = clean(payload.email, 254).toLowerCase();
  const role = clean(payload.role, 80);
  const company = clean(payload.company, 120);
  const useCase = clean(payload.useCase, 1200);
  const messageVersion = clean(payload.messageVersion, 64);
  const consent = payload.consent === true;

  const errors: string[] = [];
  if (!emailPattern.test(email)) errors.push("A valid work email is required.");
  if (!roles.has(role)) errors.push("Select a supported B2G role.");
  if (useCase.length < 20) {
    errors.push("Describe the B2G market and tender workflow in at least 20 characters.");
  }
  if (!messageVersionPattern.test(messageVersion)) {
    errors.push("A valid message version is required.");
  }
  if (!consent) errors.push("Consent is required to process the request.");

  if (errors.length) {
    return NextResponse.json(
      { status: "rejected", message: errors.join(" ") },
      { status: 422, headers: { "cache-control": "no-store" } }
    );
  }

  const record: IntakeRecord = {
    schema: "axignal.b2g-trial-intake.v1",
    submissionId: randomUUID(),
    submittedAt: new Date().toISOString(),
    source: "landing_b2g_opportunity_v1_0",
    messageVersion,
    email,
    role,
    company: company || null,
    useCase,
    consent: true
  };

  const contactEmail = process.env.AXIGNAL_PILOT_CONTACT_EMAIL;
  const intakeFile = process.env.AXIGNAL_PILOT_INTAKE_FILE;
  if (intakeFile) {
    try {
      await persistLocally(intakeFile, record);
    } catch {
      return NextResponse.json(
        {
          status: "unavailable",
          message: "The controlled B2G trial queue could not persist the request. No success was recorded.",
          contactEmail
        },
        { status: 503, headers: { "cache-control": "no-store" } }
      );
    }

    return NextResponse.json(
      {
        status: "received",
        message:
          "Request received. AXIGNAL will review the B2G market, source coverage and controlled-trial fit."
      },
      { status: 202, headers: { "cache-control": "no-store" } }
    );
  }

  const webhook = process.env.AXIGNAL_PILOT_INTAKE_WEBHOOK_URL;
  if (!webhook) {
    return NextResponse.json(
      {
        status: "unavailable",
        message: "The controlled B2G trial channel is not configured. No request was stored.",
        contactEmail
      },
      { status: 503, headers: { "cache-control": "no-store" } }
    );
  }

  const headers: Record<string, string> = { "content-type": "application/json" };
  const token = process.env.AXIGNAL_PILOT_INTAKE_BEARER_TOKEN;
  if (token) headers.authorization = `Bearer ${token}`;

  try {
    const response = await fetch(webhook, {
      method: "POST",
      headers,
      body: JSON.stringify(record),
      signal: AbortSignal.timeout(8_000),
      cache: "no-store"
    });

    if (!response.ok) {
      return NextResponse.json(
        {
          status: "unavailable",
          message: "The controlled B2G trial channel rejected the request. No success was recorded.",
          contactEmail
        },
        { status: 502, headers: { "cache-control": "no-store" } }
      );
    }
  } catch {
    return NextResponse.json(
      {
        status: "unavailable",
        message: "The controlled B2G trial channel could not be reached. No success was recorded.",
        contactEmail
      },
      { status: 502, headers: { "cache-control": "no-store" } }
    );
  }

  return NextResponse.json(
    {
      status: "received",
      message: "Request received. AXIGNAL will review the B2G market, source coverage and controlled-trial fit."
    },
    { status: 202, headers: { "cache-control": "no-store" } }
  );
}
