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
import type { SubscriberWorkspaceBootstrap } from "../../../../lib/subscriber-workspace-contract";
import {
  subscriberWorkspaceBootstrapResult,
  subscriberWorkspaceEnabled
} from "../../../../lib/subscriber-workspace-server";

const supportedLocales = new Set<Locale>(["en", "es", "fr", "de", "pt-BR", "zh-Hans"]);

type ResearchMode =
  | "STRUCTURED_SOURCE_OBSERVATION"
  | "DOCUMENT_PROPOSAL"
  | "TED_PROCUREMENT";

type ResearchRequestBody = {
  question?: unknown;
  locale?: unknown;
  includePrivateKnowledge?: unknown;
  researchMode?: unknown;
  payload?: unknown;
  subscriberOpportunityId?: unknown;
};

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
  if (value === "TED_PROCUREMENT") return value;
  if (value === "DOCUMENT_PROPOSAL") return value;
  if (process.env.AXIGNAL_TED_PROCUREMENT_UI_ENABLED === "true") {
    return "TED_PROCUREMENT";
  }
  if (process.env.AXIGNAL_DOCUMENT_PROPOSAL_UI_ENABLED === "true") {
    return "DOCUMENT_PROPOSAL";
  }
  return "STRUCTURED_SOURCE_OBSERVATION";
}

function localeValue(value: unknown): Locale {
  return typeof value === "string" && supportedLocales.has(value as Locale)
    ? (value as Locale)
    : "es";
}

async function subscriberTarget(opportunityId: string): Promise<
  | { contextId: string; opportunityId: string }
  | { response: NextResponse }
> {
  if (!subscriberWorkspaceEnabled()) {
    return {
      response: NextResponse.json(
        { error: "Subscriber workspace is disabled." },
        { status: 404, headers: { "cache-control": "no-store" } }
      )
    };
  }
  const result = await subscriberWorkspaceBootstrapResult();
  if (result.status < 200 || result.status >= 300) {
    return {
      response: NextResponse.json(result.body, {
        status: result.status,
        headers: { "cache-control": "no-store" }
      })
    };
  }
  const bootstrap = result.body as SubscriberWorkspaceBootstrap;
  const opportunity = bootstrap.route_data.opportunities.find(
    (item) => item.id === opportunityId
  );
  if (!opportunity) {
    return {
      response: NextResponse.json(
        { error: "The selected subscriber opportunity is not available in the server-resolved tenant context." },
        { status: 400, headers: { "cache-control": "no-store" } }
      )
    };
  }
  return {
    contextId: `subscriber:${bootstrap.tenant.id}:${opportunity.id}`,
    opportunityId: opportunity.id
  };
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as ResearchRequestBody | null;

  if (!body || typeof body.question !== "string" || body.question.trim().length === 0) {
    return NextResponse.json(
      { error: "A non-empty research question is required." },
      { status: 400, headers: { "cache-control": "no-store" } }
    );
  }

  const subscriberOpportunityId =
    typeof body.subscriberOpportunityId === "string" && body.subscriberOpportunityId.trim()
      ? body.subscriberOpportunityId.trim()
      : null;
  const locale = localeValue(body.locale);
  const payload = isPayload(body.payload) ? body.payload : createInitialInvestigation(locale);

  if (!isPersistentResearchUiEnabled()) {
    if (subscriberOpportunityId) {
      return NextResponse.json(
        {
          error: "Persistent ResearchRun execution is required for the subscriber Navigator; synthetic fallback is forbidden."
        },
        { status: 503, headers: { "cache-control": "no-store" } }
      );
    }
    try {
      return NextResponse.json(
        executeSyntheticResearchRun({
          question: body.question.trim(),
          locale,
          includePrivateKnowledge: body.includePrivateKnowledge === true,
          payload
        }),
        { headers: { "cache-control": "no-store" } }
      );
    } catch (error) {
      return NextResponse.json(
        { error: error instanceof Error ? error.message : "ResearchRun failed." },
        { status: 400, headers: { "cache-control": "no-store" } }
      );
    }
  }

  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    return NextResponse.json(
      { error: "Authentication required." },
      { status: 401, headers: { "cache-control": "no-store" } }
    );
  }

  let contextId: string;
  let opportunityId: string;
  if (subscriberOpportunityId) {
    const target = await subscriberTarget(subscriberOpportunityId);
    if ("response" in target) return target.response;
    contextId = target.contextId;
    opportunityId = target.opportunityId;
  } else {
    contextId = payload.context.context_id;
    opportunityId = payload.context.selection.opportunity_ids[0] ?? "";
    if (!opportunityId || !payload.opportunities.some((item) => item.opportunity_id === opportunityId)) {
      return NextResponse.json(
        { error: "A valid selected opportunity is required." },
        { status: 400, headers: { "cache-control": "no-store" } }
      );
    }
  }

  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!apiUrl) {
    return NextResponse.json(
      { error: "AXIGNAL_API_URL is required." },
      { status: 503, headers: { "cache-control": "no-store" } }
    );
  }

  const mode = requestedMode(body.researchMode);
  if (mode !== "STRUCTURED_SOURCE_OBSERVATION" && body.includePrivateKnowledge === true) {
    return NextResponse.json(
      { error: `${mode} v0.1 does not accept tenant-private knowledge.` },
      { status: 400, headers: { "cache-control": "no-store" } }
    );
  }
  const endpoint =
    mode === "DOCUMENT_PROPOSAL"
      ? "/v1/research-runs/document-proposals"
      : mode === "TED_PROCUREMENT"
        ? "/v1/research-runs/ted-procurement"
        : "/v1/research-runs";

  try {
    const response = await fetch(`${apiUrl}${endpoint}`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "X-AXIGNAL-Identity-Assertion": buildApiIdentityAssertion(identity)
      },
      body: JSON.stringify({
        context_id: contextId,
        opportunity_id: opportunityId,
        question: body.question.trim(),
        include_private_knowledge:
          mode === "STRUCTURED_SOURCE_OBSERVATION"
            ? body.includePrivateKnowledge === true
            : false
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
    return NextResponse.json(
      { error: "Persistent ResearchRun API unavailable." },
      { status: 503, headers: { "cache-control": "no-store" } }
    );
  }
}
