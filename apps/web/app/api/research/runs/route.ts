import { NextResponse } from "next/server";

import {
  createInitialInvestigation,
  type Locale,
  type PrototypeInvestigationPayload
} from "../../../../lib/investigation-context";
import { executeSyntheticResearchRun } from "../../../../lib/research-fixture";

const supportedLocales = new Set<Locale>(["en", "es", "fr", "de", "pt-BR", "zh-Hans"]);

function isPayload(value: unknown): value is PrototypeInvestigationPayload {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<PrototypeInvestigationPayload>;
  return Boolean(
    candidate.context?.context_id === "ctx_moscow_real_estate_v01" &&
      candidate.context.synthetic === true &&
      Array.isArray(candidate.opportunities) &&
      Array.isArray(candidate.claims) &&
      Array.isArray(candidate.evidence)
  );
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as {
    question?: unknown;
    locale?: unknown;
    includePrivateKnowledge?: unknown;
    payload?: unknown;
  } | null;

  if (!body || typeof body.question !== "string" || body.question.trim().length === 0) {
    return NextResponse.json({ error: "A non-empty research question is required." }, { status: 400 });
  }

  const locale: Locale = typeof body.locale === "string" && supportedLocales.has(body.locale as Locale)
    ? (body.locale as Locale)
    : "es";
  const payload = isPayload(body.payload) ? body.payload : createInitialInvestigation(locale);

  try {
    return NextResponse.json(executeSyntheticResearchRun({
      question: body.question.trim(),
      locale,
      includePrivateKnowledge: body.includePrivateKnowledge === true,
      payload
    }));
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "ResearchRun failed." },
      { status: 400 }
    );
  }
}
