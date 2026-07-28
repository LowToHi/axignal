export type HumanReviewAction =
  | "ACCEPT_AS_CONTEXT"
  | "REJECT_PROPOSAL"
  | "CONFIRM_CONTESTED"
  | "REQUEST_MORE_EVIDENCE"
  | "RETURN_TO_DETERMINISTIC_REVIEW"
  | "MARK_OUT_OF_SCOPE";

export type HumanReviewEvent = {
  human_review_event_id: string;
  event_type: string;
  actor_subject: string | null;
  actor_email: string | null;
  reason_code: string | null;
  payload: Record<string, unknown>;
  occurred_at: string;
};

export type HumanReviewCase = {
  human_review_case_id: string;
  tenant_id: string;
  research_run_id: string;
  admission_handoff_id: string;
  admission_decision_id: string;
  candidate_claim_id: string;
  case_type: "HUMAN_REVIEW_REQUIRED" | "CONTESTED";
  state: "OPEN" | "IN_REVIEW" | "MORE_EVIDENCE_REQUIRED" | "RESOLVED" | "CANCELLED";
  priority: "LOW" | "NORMAL" | "HIGH";
  assigned_reviewer_subject: string | null;
  assigned_reviewer_email: string | null;
  opened_reason: string;
  resolution: HumanReviewAction | null;
  resolution_reason_code: string | null;
  resolution_note: string | null;
  deterministic_decision: {
    outcome: string;
    policy_version: string;
    gate_results: Record<string, boolean>;
    rejection_reasons: string[];
    canonical_claim_id: string | null;
  };
  candidate_claim: {
    statement: string;
    kind: string;
    state: string;
    producer_type: string;
    producer_id: string;
    method_version: string;
    assumptions: string[];
    unknowns: string[];
    canonical_claim_id: string | null;
  };
  source: {
    source_id: string;
    name: string;
    rights_status: string;
    license_id: string | null;
    admission_state: string;
    kill_switch: boolean;
  } | null;
  evidence: Array<{
    evidence_id: string;
    title: string;
    relationship: string;
    source_id: string;
    rights_status: string;
    fragment_id: string | null;
    quote_hash: string | null;
    text: string | null;
  }>;
  events: HumanReviewEvent[];
};

export async function listHumanReviewCases(): Promise<HumanReviewCase[]> {
  const response = await fetch("/api/human-review/cases", { cache: "no-store" });
  if (!response.ok) return [];
  const body = (await response.json()) as { cases?: HumanReviewCase[] };
  return Array.isArray(body.cases) ? body.cases : [];
}

export async function applyHumanReviewAction(
  humanReviewCaseId: string,
  action: HumanReviewAction,
  reasonCode: string,
  note?: string
): Promise<HumanReviewCase> {
  const response = await fetch(
    `/api/human-review/cases/${humanReviewCaseId}/actions`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action, reason_code: reasonCode, note: note || null })
    }
  );
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      error?: string;
      detail?: string;
    } | null;
    throw new Error(body?.error ?? body?.detail ?? "Human-review action failed");
  }
  return (await response.json()) as HumanReviewCase;
}
