import { NextResponse } from "next/server";

import {
  createInitialInvestigation,
  type Locale,
  type PrototypeInvestigationPayload
} from "../../../../lib/investigation-context";
import { executeSyntheticResearchRun } from "../../../../lib/research-fixture";
import {
  buildApiIdentityAssertion,
  getAuthenticatedIdentity,
  isPersistentResearchUiEnabled
} from "../../../../lib/server-auth";

const supportedLocales = new Set<Locale>(["en", "es", "fr", "de", "pt-BR", "zh-Hans"]);

type ResearchMode = "STRUCTURED_SOURCE_OBSERVATION" | "DOCUMENT_PROPOSAL";

function isPayload(value: unknown): value is PrototypeInvestigationPayload {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<PrototypeInvestigationPayload>;
  return Boolean(
    candidate.context?.context_id === "ctx_moscow_real_estate_v01" &&
      Array.isArray(candidate.opportunities) &&
      Array.isArray(candidate.claims) &&
      Array.isArray(candidate.evidence)
  );
}

function requestedMode(value: unknown): ResearchMode {
  if (value === "DOCUMENT_PROPOSAL") return value;
  if (process.env.AXIGNAL_DOCUMENT_PROPOSAL_UI_ENABLED === "true") {
    return "DOCUMENT_PROPOSAL";
  }
  return "STRUCTURED_SOURCE_OBSERVATION";
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as {
    question?: unknown;
    locale?: unknown;
    includePrivateKnowledge?: unknown;
    researchMode?: unknown;
    payload?: unknown;
  } | null;

  if (!body || typeof body.question !== "string" || body.question.trim().length === 0) {
    return NextResponse.json(
      { error: "A non-empty research question is required." },
      { status: 400 }
    );
  }

  const locale: Locale =
    typeof body.locale === "string" && supportedLocales.has(body.locale as Locale)
      ? (body.locale as Locale)
      : "es";
  const payload = isPayload(body.payload) ? body.payload : createInitialInvestigation(locale);

  if (!isPersistentResearchUiEnabled()) {
    try {
      return NextResponse.json(
        executeSyntheticResearchRun({
          question: body.question.trim(),
          locale,
          includePrivateKnowledge: body.includePrivateKnowledge === true,
          payload
        })
      );
    } catch (error) {
      return NextResponse.json(
        { error: error instanceof Error ? error.message : "ResearchRun failed." },
        { status: 400 }
      );
    }
  }

  const identity = await getAuthenticatedIdentity();
  if (!identity) return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  const opportunityId = payload.context.selection.opportunity_ids[0];
  if (!opportunityId || !payload.opportunities.some((item) => item.opportunity_id === opportunityId)) {
    return NextResponse.json(
      { error: "A valid selected opportunity is required." },
      { status: 400 }
    );
  }
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!apiUrl) return NextResponse.json({ error: "AXIGNAL_API_URL is required." }, { status: 503 });

  const mode = requestedMode(body.researchMode);
  if (mode === "DOCUMENT_PROPOSAL" && body.includePrivateKnowledge === true) {
    return NextResponse.json(
      { error: "Document proposal v0.1 does not accept tenant-private knowledge." },
      { status: 400 }
    );
  }
  const endpoint =
    mode === "DOCUMENT_PROPOSAL"
      ? "/v1/research-runs/document-proposals"
      : "/v1/research-runs";

  try {
    const response = await fetch(`${apiUrl}${endpoint}`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "X-AXIGNAL-Identity-Assertion": buildApiIdentityAssertion(identity)
      },
      body: JSON.stringify({
        context_id: payload.context.context_id,
        opportunity_id: opportunityId,
        question: body.question.trim(),
        include_private_knowledge:
          mode === "DOCUMENT_PROPOSAL" ? false : body.includePrivateKnowledge === true
      }),
      cache: "no-store",
      signal: AbortSignal.timeout(8_000)
    });
    const responseBody = await response.json().catch(() => ({ error: "Invalid API response." }));
    return NextResponse.json(responseBody, {
      status: response.status,
      headers: { "cache-control": "no-store" }
    });
  } catch {
    return NextResponse.json({ error: "Persistent ResearchRun API unavailable." }, { status: 503 });
  }
}
