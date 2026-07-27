import type { Locale, PrototypeInvestigationPayload } from "./investigation-context";
import {
  integratePersistentResearchRun,
  isTerminalPersistentState,
  type PersistentResearchRunAccepted,
  type PersistentResearchRunView
} from "./persistent-research";

export type NavigatorCommandRequest = {
  message: string;
  locale: Locale;
  payload: PrototypeInvestigationPayload;
};

export type ResearchRequest = {
  question: string;
  locale: Locale;
  includePrivateKnowledge: boolean;
  payload: PrototypeInvestigationPayload;
};

async function readJson<T>(response: Response, operation: string): Promise<T> {
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { error?: string; detail?: string } | null;
    throw new Error(body?.error ?? body?.detail ?? `${operation} failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

function isInvestigationPayload(value: unknown): value is PrototypeInvestigationPayload {
  return Boolean(value && typeof value === "object" && "context" in value && "opportunities" in value);
}

function queuedView(
  accepted: PersistentResearchRunAccepted,
  request: ResearchRequest
): PersistentResearchRunView {
  const now = new Date().toISOString();
  return {
    research_run_id: accepted.research_run_id,
    context_id: request.payload.context.context_id,
    opportunity_id: request.payload.context.selection.opportunity_ids[0] ?? "unknown",
    question: request.question,
    state: accepted.state,
    private_knowledge_authorised: request.includePrivateKnowledge,
    source_plan: accepted.source_ids.map((sourceId) => ({ source_id: sourceId })),
    budgets: {},
    actual_usage: {},
    evidence: [],
    candidate_claims: [],
    canonical_claims: [],
    dossier: null,
    admission_batch_id: null,
    error_code: null,
    error_detail: null,
    created_at: now,
    updated_at: now,
    synthetic: false
  };
}

export async function runNavigatorCommand(request: NavigatorCommandRequest): Promise<PrototypeInvestigationPayload> {
  const response = await fetch("/api/navigator/interpret", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(request)
  });
  return readJson<PrototypeInvestigationPayload>(response, "Navigator request");
}

export async function runResearch(
  request: ResearchRequest,
  onProgress?: (payload: PrototypeInvestigationPayload) => void
): Promise<PrototypeInvestigationPayload> {
  const response = await fetch("/api/research/runs", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(request)
  });
  const created = await readJson<PrototypeInvestigationPayload | PersistentResearchRunAccepted>(response, "ResearchRun");
  if (isInvestigationPayload(created)) return created;

  let current = integratePersistentResearchRun(request.payload, queuedView(created, request));
  onProgress?.(current);

  for (let attempt = 0; attempt < 80; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, 750));
    const pollResponse = await fetch(`/api/research/runs/${created.research_run_id}`, {
      cache: "no-store"
    });
    const view = await readJson<PersistentResearchRunView>(pollResponse, "ResearchRun polling");
    current = integratePersistentResearchRun(current, view);
    onProgress?.(current);
    if (isTerminalPersistentState(view.state)) return current;
  }

  return {
    ...current,
    explanation: "La ResearchRun sigue activa en el worker; el contexto conserva su identificador persistente para reanudar el polling."
  };
}
