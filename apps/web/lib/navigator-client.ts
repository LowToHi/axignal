import type { Locale, PrototypeInvestigationPayload } from "./investigation-context";
import {
  integratePersistentResearchRun,
  isTerminalPersistentState,
  type PersistentResearchRunAccepted,
  type PersistentResearchRunView
} from "./persistent-research";

export const RESEARCH_PROGRESS_EVENT = "axignal:research-progress";

export type ResearchProgressEvent = {
  researchRunId: string;
  state: string;
  question: string;
  terminal: boolean;
  explanation: string;
};

export type NavigatorCommandRequest = {
  message: string;
  locale: Locale;
  payload: PrototypeInvestigationPayload;
};

export type ResearchRequest = {
  question: string;
  locale: Locale;
  includePrivateKnowledge: boolean;
  researchMode?:
    | "STRUCTURED_SOURCE_OBSERVATION"
    | "DOCUMENT_PROPOSAL"
    | "TED_PROCUREMENT";
  payload: PrototypeInvestigationPayload;
};

async function readJson<T>(response: Response, operation: string): Promise<T> {
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      error?: string;
      detail?: string;
    } | null;
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

function publishProgress(view: PersistentResearchRunView, explanation: string): void {
  window.dispatchEvent(
    new CustomEvent<ResearchProgressEvent>(RESEARCH_PROGRESS_EVENT, {
      detail: {
        researchRunId: view.research_run_id,
        state: view.state,
        question: view.question,
        terminal: isTerminalPersistentState(view.state),
        explanation
      }
    })
  );
}

export async function runNavigatorCommand(
  request: NavigatorCommandRequest
): Promise<PrototypeInvestigationPayload> {
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
  const created = await readJson<PrototypeInvestigationPayload | PersistentResearchRunAccepted>(
    response,
    "ResearchRun"
  );
  if (isInvestigationPayload(created)) return created;

  let view = queuedView(created, request);
  let current = integratePersistentResearchRun(request.payload, view);
  publishProgress(view, current.explanation);
  onProgress?.(current);

  for (let attempt = 0; attempt < 80; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, 750));
    const pollResponse = await fetch(`/api/research/runs/${created.research_run_id}`, {
      cache: "no-store"
    });
    view = await readJson<PersistentResearchRunView>(pollResponse, "ResearchRun polling");
    current = integratePersistentResearchRun(current, view);
    publishProgress(view, current.explanation);
    onProgress?.(current);
    if (isTerminalPersistentState(view.state)) return current;
  }

  const timedOut = {
    ...current,
    explanation:
      "La ResearchRun sigue activa en el worker; el contexto conserva su identificador " +
      "persistente para reanudar el polling."
  };
  publishProgress(view, timedOut.explanation);
  return timedOut;
}
