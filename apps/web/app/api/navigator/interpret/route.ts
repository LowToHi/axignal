import { NextResponse } from "next/server";

import {
  createInitialInvestigation,
  findSelectedOpportunity,
  nextHistoryEvent,
  type Locale,
  type PrototypeInvestigationPayload
} from "../../../../lib/investigation-context";

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
    message?: unknown;
    locale?: unknown;
    payload?: unknown;
  } | null;

  if (!body || typeof body.message !== "string" || body.message.trim().length === 0) {
    return NextResponse.json({ error: "A non-empty Navigator message is required." }, { status: 400 });
  }

  const locale: Locale = typeof body.locale === "string" && supportedLocales.has(body.locale as Locale)
    ? (body.locale as Locale)
    : "es";
  const current = isPayload(body.payload) ? structuredClone(body.payload) : createInitialInvestigation(locale);
  const context = structuredClone(current.context);
  const message = body.message.trim();
  const lower = message.toLocaleLowerCase(locale === "es" ? "es" : undefined);
  const planId = `plan_${String(context.version + 1).padStart(4, "0")}`;
  let eventType = "NAVIGATOR_COMMAND_EXECUTED";
  let explanation = "He conservado el contexto y añadido la orden al Investigation Trail.";
  let focus = { ...current.focus };

  if (lower.includes("grafo") || lower.includes("graph")) {
    context.lens = "GRAPH";
    context.lens_reason = "El usuario ha solicitado una lectura relacional.";
    eventType = "LENS_CHANGED";
    explanation = "He cambiado a Graph y conservado geografía, oportunidad, claims, evidencia y horizonte.";
  } else if (lower.includes("dual") || lower.includes("compara")) {
    context.lens = "DUAL";
    context.lens_reason = "El usuario ha solicitado comparar geografía y relaciones.";
    eventType = "LENS_CHANGED";
    explanation = "He activado Dual sin perder la selección ni el historial.";
  } else if (lower.includes("globo") || lower.includes("globe") || lower.includes("mapa")) {
    context.lens = "GLOBE";
    context.lens_reason = "El usuario ha solicitado una lectura geográfica.";
    eventType = "LENS_CHANGED";
    explanation = "He cambiado a Globe y mantenido el contexto de investigación.";
  } else if (lower.includes("auto")) {
    context.lens = "AUTO";
    context.lens_reason = "AXIGNAL seleccionará la lente según la intención dominante.";
    eventType = "LENS_CHANGED";
    explanation = "He activado Auto. La intención geográfica mantiene Globe como superficie efectiva.";
  }

  const requestedOpportunity = current.opportunities.find((item) => lower.includes(item.name.toLocaleLowerCase("es")));
  if (requestedOpportunity) {
    context.selection.opportunity_ids = [requestedOpportunity.opportunity_id];
    context.selection.claim_ids = [];
    context.selection.evidence_ids = [];
    context.selection.graph_node_ids = ["entity_moscow", requestedOpportunity.opportunity_id];
    context.rail_mode = "OPPORTUNITY";
    focus = { opportunity_id: requestedOpportunity.opportunity_id, claim_id: null, evidence_id: null };
    eventType = "OPPORTUNITY_SELECTED";
    explanation = `He seleccionado ${requestedOpportunity.name} y sincronizado Globe, Graph, Timeline y Evidence Rail.`;
  }

  if (lower.includes("contradic")) {
    const selected = findSelectedOpportunity({ ...current, context });
    const contradiction = current.claims.find(
      (claim) => selected.claim_ids.includes(claim.claim_id) && claim.kind === "CONTRADICCIÓN"
    );
    if (contradiction) {
      const evidenceId = contradiction.evidence_ids[0] ?? null;
      context.selection.claim_ids = [contradiction.claim_id];
      context.selection.evidence_ids = evidenceId ? [evidenceId] : [];
      context.rail_mode = "CLAIM";
      focus = { opportunity_id: selected.opportunity_id, claim_id: contradiction.claim_id, evidence_id: evidenceId };
      eventType = "CONTRADICTION_FOCUSED";
      explanation = `He aislado la contradicción material de ${selected.name} y su evidencia asociada.`;
    } else {
      context.rail_mode = "COVERAGE";
      explanation = "No existe una contradicción admitida en la fixture seleccionada; he mostrado la cobertura disponible.";
    }
  } else if (lower.includes("evidencia") || lower.includes("fuente")) {
    const selected = findSelectedOpportunity({ ...current, context });
    const claim = current.claims.find((item) => selected.claim_ids.includes(item.claim_id));
    const evidenceId = claim?.evidence_ids[0] ?? null;
    if (claim) {
      context.selection.claim_ids = [claim.claim_id];
      context.selection.evidence_ids = evidenceId ? [evidenceId] : [];
      context.rail_mode = "EVIDENCE";
      focus = { opportunity_id: selected.opportunity_id, claim_id: claim.claim_id, evidence_id: evidenceId };
      eventType = "EVIDENCE_FOCUSED";
      explanation = "He abierto la evidencia seleccionada sin convertirla en una recomendación ni en un claim nuevo.";
    }
  }

  if (lower.includes("guardar") || lower.includes("save trail")) {
    context.saved_trail_id = context.saved_trail_id ?? `trail_${context.context_id.slice(4)}`;
    eventType = "TRAIL_SAVED";
    explanation = "He guardado el Investigation Trail con el contexto, la selección, el horizonte y el historial actuales.";
  }

  if (lower.includes("36")) {
    context.time.horizon_label = "36M";
    context.filters.horizon = "36 meses";
    eventType = "TIME_HORIZON_CHANGED";
    explanation = "He ampliado el horizonte a 36 meses y conservado el resto del contexto.";
  } else if (lower.includes("12") && !lower.includes("12–24")) {
    context.time.horizon_label = "12M";
    context.filters.horizon = "12 meses";
    eventType = "TIME_HORIZON_CHANGED";
    explanation = "He reducido el horizonte a 12 meses y conservado el resto del contexto.";
  }

  context.locale = locale;
  context.version += 1;
  context.updated_at = new Date().toISOString();
  context.history.push(nextHistoryEvent({ ...context, version: context.version - 1 }, eventType, planId));

  return NextResponse.json({ ...current, context, explanation, focus });
}
