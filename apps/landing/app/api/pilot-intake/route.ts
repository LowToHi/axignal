import { createHash, randomUUID } from "node:crypto";
import { appendFile, chmod, mkdir } from "node:fs/promises";
import { dirname } from "node:path";

import { NextResponse } from "next/server";
import { getMessages, isLocale, type Locale } from "@/lib/i18n";

export const runtime = "nodejs";

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const schema = "axignal.design-partner-intake.v2" as const;
const allowedTopLevel = new Set([
  "schema",
  "idempotencyKey",
  "email",
  "organisation",
  "role",
  "countries",
  "monthlyVolume",
  "currentProcess",
  "useCase",
  "expensiveProblem",
  "timeframe",
  "consent",
  "website",
  "system"
]);
const allowedSystemFields = new Set([
  "locale",
  "utmSource",
  "utmMedium",
  "utmCampaign",
  "landingVariant",
  "referrer",
  "selectedPlan",
  "ctaOrigin",
  "clientTimestamp",
  "consentVersion"
]);
const requestBuckets = new Map<string, { count: number; resetAt: number }>();
const acceptedKeys = new Map<string, number>();
const RATE_WINDOW_MS = 10 * 60 * 1000;
const RATE_LIMIT = 5;
const DEDUPE_WINDOW_MS = 24 * 60 * 60 * 1000;

type IntakePayload = {
  schema?: unknown;
  idempotencyKey?: unknown;
  email?: unknown;
  organisation?: unknown;
  role?: unknown;
  countries?: unknown;
  monthlyVolume?: unknown;
  currentProcess?: unknown;
  useCase?: unknown;
  expensiveProblem?: unknown;
  timeframe?: unknown;
  consent?: unknown;
  website?: unknown;
  system?: unknown;
};

type IntakeRecord = {
  schema: typeof schema;
  submissionId: string;
  submittedAt: string;
  idempotencyKeyHash: string;
  email: string;
  organisation: string;
  role: string;
  countries: string;
  monthlyVolume: number;
  currentProcess: string;
  useCase: string;
  expensiveProblem: string;
  timeframe: string;
  consent: true;
  system: {
    locale: Locale;
    utmSource: string | null;
    utmMedium: string | null;
    utmCampaign: string | null;
    landingVariant: "b2g_v1";
    referrerOrigin: string | null;
    selectedPlan: string;
    ctaOrigin: "direct" | "pricing";
    clientTimestamp: string;
    consentVersion: "design-partner-intake-2026-07-29";
  };
};

function hash(value: string) {
  return createHash("sha256").update(value).digest("hex");
}

function rawString(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function boundedString(value: unknown, minimum: number, maximum: number, label: string, errors: string[]) {
  const result = rawString(value);
  if (result.length < minimum || result.length > maximum) {
    errors.push(`${label} must contain between ${minimum} and ${maximum} characters.`);
  }
  return result;
}

function optionalString(value: unknown, maximum: number) {
  const result = rawString(value);
  return result ? result.slice(0, maximum) : null;
}

function referrerOrigin(value: unknown) {
  const referrer = rawString(value);
  if (!referrer) return null;
  try {
    return new URL(referrer).origin.slice(0, 200);
  } catch {
    return null;
  }
}

function getClientKey(request: Request) {
  const forwarded = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim();
  const address = request.headers.get("x-real-ip")?.trim() || forwarded || "unknown";
  return hash(address);
}

function consumeRateLimit(key: string) {
  const now = Date.now();
  const current = requestBuckets.get(key);
  if (!current || current.resetAt <= now) {
    requestBuckets.set(key, { count: 1, resetAt: now + RATE_WINDOW_MS });
    return { allowed: true, retryAfter: 0 };
  }
  if (current.count >= RATE_LIMIT) {
    return { allowed: false, retryAfter: Math.max(1, Math.ceil((current.resetAt - now) / 1000)) };
  }
  current.count += 1;
  return { allowed: true, retryAfter: 0 };
}

function pruneAcceptedKeys(now: number) {
  for (const [key, acceptedAt] of acceptedKeys) {
    if (acceptedAt + DEDUPE_WINDOW_MS <= now) acceptedKeys.delete(key);
  }
}

function noStoreHeaders(extra: Record<string, string> = {}) {
  return {
    "cache-control": "no-store, max-age=0",
    "x-content-type-options": "nosniff",
    ...extra
  };
}

function logOutcome(result: string, submissionId: string | null, locale: string | null) {
  console.info(
    JSON.stringify({
      event: "design_partner_intake",
      result,
      submission_id: submissionId,
      locale,
      at: new Date().toISOString()
    })
  );
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
  const contentType = request.headers.get("content-type") ?? "";
  const contentLength = Number(request.headers.get("content-length") ?? "0");
  if (!contentType.toLowerCase().startsWith("application/json")) {
    return NextResponse.json(
      { status: "rejected", message: "JSON content is required." },
      { status: 415, headers: noStoreHeaders() }
    );
  }
  if (!Number.isFinite(contentLength) || contentLength > 16_000) {
    return NextResponse.json(
      { status: "rejected", message: "The request exceeds the permitted size." },
      { status: 413, headers: noStoreHeaders() }
    );
  }

  const origin = request.headers.get("origin");
  if (origin && new URL(origin).host !== new URL(request.url).host) {
    logOutcome("origin_rejected", null, null);
    return NextResponse.json(
      { status: "rejected", message: "The request origin is not permitted." },
      { status: 403, headers: noStoreHeaders() }
    );
  }

  const rate = consumeRateLimit(getClientKey(request));
  if (!rate.allowed) {
    logOutcome("rate_limited", null, null);
    return NextResponse.json(
      { status: "rate_limited", message: "Too many requests. Try again later." },
      { status: 429, headers: noStoreHeaders({ "retry-after": String(rate.retryAfter) }) }
    );
  }

  let payload: IntakePayload;
  try {
    payload = (await request.json()) as IntakePayload;
  } catch {
    return NextResponse.json(
      { status: "rejected", message: "A valid JSON request is required." },
      { status: 400, headers: noStoreHeaders() }
    );
  }

  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return NextResponse.json(
      { status: "rejected", message: "A JSON object is required." },
      { status: 400, headers: noStoreHeaders() }
    );
  }
  const topLevelKeys = Object.keys(payload);
  if (topLevelKeys.some((key) => !allowedTopLevel.has(key))) {
    return NextResponse.json(
      { status: "rejected", message: "The request contains unsupported fields." },
      { status: 422, headers: noStoreHeaders() }
    );
  }

  const website = rawString(payload.website);
  if (website) {
    logOutcome("honeypot", null, null);
    return NextResponse.json(
      { status: "received", message: "Request received." },
      { status: 202, headers: noStoreHeaders() }
    );
  }

  const system =
    payload.system && typeof payload.system === "object" && !Array.isArray(payload.system)
      ? (payload.system as Record<string, unknown>)
      : null;
  const errors: string[] = [];
  if (!system || Object.keys(system).some((key) => !allowedSystemFields.has(key))) {
    errors.push("A valid system context is required.");
  }

  const localeValue = rawString(system?.locale);
  const locale = isLocale(localeValue) ? localeValue : null;
  if (!locale) errors.push("A supported locale is required.");

  const email = boundedString(payload.email, 5, 254, "Work email", errors).toLowerCase();
  if (!emailPattern.test(email)) errors.push("A valid work email is required.");
  const organisation = boundedString(payload.organisation, 2, 120, "Organisation", errors);
  const role = boundedString(payload.role, 2, 80, "Role", errors);
  const countries = boundedString(payload.countries, 2, 180, "Countries", errors);
  const currentProcess = boundedString(payload.currentProcess, 10, 600, "Current process", errors);
  const useCase = boundedString(payload.useCase, 20, 800, "Use case", errors);
  const expensiveProblem = boundedString(payload.expensiveProblem, 20, 800, "Expensive problem", errors);
  const timeframe = boundedString(payload.timeframe, 2, 80, "Timeframe", errors);
  const monthlyVolume =
    typeof payload.monthlyVolume === "number" && Number.isInteger(payload.monthlyVolume)
      ? payload.monthlyVolume
      : Number.NaN;
  if (!Number.isFinite(monthlyVolume) || monthlyVolume < 1 || monthlyVolume > 10_000) {
    errors.push("Monthly volume must be an integer from 1 to 10000.");
  }

  if (locale) {
    const formMessages = getMessages(locale).form;
    if (!formMessages.roles.includes(role)) errors.push("Select a supported role.");
    if (!formMessages.timeframes.includes(timeframe)) errors.push("Select a supported timeframe.");
  }
  if (payload.consent !== true) errors.push("Consent is required to process the request.");
  if (payload.schema !== schema) errors.push("The intake schema is not supported.");

  const payloadKey = rawString(payload.idempotencyKey);
  const headerKey = rawString(request.headers.get("idempotency-key"));
  if (
    payloadKey.length < 16 ||
    payloadKey.length > 120 ||
    headerKey !== payloadKey ||
    !/^[a-zA-Z0-9-]+$/.test(payloadKey)
  ) {
    errors.push("A matching idempotency key is required.");
  }

  const clientTimestamp = rawString(system?.clientTimestamp);
  if (!clientTimestamp || Number.isNaN(Date.parse(clientTimestamp))) {
    errors.push("A valid client timestamp is required.");
  }
  if (system?.landingVariant !== "b2g_v1") errors.push("The landing variant is not supported.");
  if (!["direct", "pricing"].includes(rawString(system?.ctaOrigin))) errors.push("CTA origin is invalid.");
  if (system?.consentVersion !== "design-partner-intake-2026-07-29") {
    errors.push("The consent version is not supported.");
  }

  if (errors.length) {
    logOutcome("validation_rejected", null, locale);
    return NextResponse.json(
      { status: "rejected", message: errors.join(" ") },
      { status: 422, headers: noStoreHeaders() }
    );
  }

  const keyHash = hash(payloadKey);
  const now = Date.now();
  pruneAcceptedKeys(now);
  if (acceptedKeys.has(keyHash)) {
    logOutcome("duplicate_accepted", null, locale);
    return NextResponse.json(
      { status: "received", message: "Request already received." },
      { status: 202, headers: noStoreHeaders() }
    );
  }

  const submissionId = randomUUID();
  const record: IntakeRecord = {
    schema,
    submissionId,
    submittedAt: new Date().toISOString(),
    idempotencyKeyHash: keyHash,
    email,
    organisation,
    role,
    countries,
    monthlyVolume,
    currentProcess,
    useCase,
    expensiveProblem,
    timeframe,
    consent: true,
    system: {
      locale: locale!,
      utmSource: optionalString(system?.utmSource, 120),
      utmMedium: optionalString(system?.utmMedium, 120),
      utmCampaign: optionalString(system?.utmCampaign, 120),
      landingVariant: "b2g_v1",
      referrerOrigin: referrerOrigin(system?.referrer),
      selectedPlan: rawString(system?.selectedPlan).slice(0, 80),
      ctaOrigin: rawString(system?.ctaOrigin) as "direct" | "pricing",
      clientTimestamp,
      consentVersion: "design-partner-intake-2026-07-29"
    }
  };

  const contactEmail = process.env.AXIGNAL_PILOT_CONTACT_EMAIL;
  const intakeFile = process.env.AXIGNAL_PILOT_INTAKE_FILE;
  const webhook = process.env.AXIGNAL_PILOT_INTAKE_WEBHOOK_URL;

  try {
    if (intakeFile) {
      await persistLocally(intakeFile, record);
    } else if (webhook) {
      const headers: Record<string, string> = { "content-type": "application/json" };
      const token = process.env.AXIGNAL_PILOT_INTAKE_BEARER_TOKEN;
      if (token) headers.authorization = `Bearer ${token}`;
      const response = await fetch(webhook, {
        method: "POST",
        headers,
        body: JSON.stringify(record),
        signal: AbortSignal.timeout(8_000),
        cache: "no-store"
      });
      if (!response.ok) throw new Error("delivery rejected");
    } else {
      logOutcome("unconfigured", submissionId, locale);
      return NextResponse.json(
        {
          status: "unavailable",
          message: "The Design Partner intake channel is not configured. No request was stored.",
          contactEmail
        },
        { status: 503, headers: noStoreHeaders() }
      );
    }
  } catch {
    logOutcome("delivery_failed", submissionId, locale);
    return NextResponse.json(
      {
        status: "unavailable",
        message: "The Design Partner intake channel could not persist the request. No success was recorded.",
        contactEmail
      },
      { status: 502, headers: noStoreHeaders() }
    );
  }

  acceptedKeys.set(keyHash, now);
  logOutcome("accepted", submissionId, locale);
  return NextResponse.json(
    {
      status: "received",
      message: "Request received. AXIGNAL will review the fit for the Design Partner programme."
    },
    { status: 202, headers: noStoreHeaders() }
  );
}
