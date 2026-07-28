"use client";

import { useEffect, useMemo, useState } from "react";

import {
  applyHumanReviewAction,
  listHumanReviewCases,
  type HumanReviewAction,
  type HumanReviewCase
} from "../lib/human-review-client";

const actions: Array<{
  action: HumanReviewAction;
  label: string;
  reason: string;
}> = [
  {
    action: "ACCEPT_AS_CONTEXT",
    label: "Aceptar como contexto",
    reason: "LIMITATION_CONFIRMED"
  },
  {
    action: "REQUEST_MORE_EVIDENCE",
    label: "Solicitar evidencia",
    reason: "MORE_EVIDENCE_REQUIRED"
  },
  {
    action: "REJECT_PROPOSAL",
    label: "Rechazar propuesta",
    reason: "PROPOSAL_REJECTED"
  },
  {
    action: "CONFIRM_CONTESTED",
    label: "Confirmar controversia",
    reason: "CONTESTED_CONFIRMED"
  }
];

export function HumanReviewBridge() {
  const [cases, setCases] = useState<HumanReviewCase[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void listHumanReviewCases().then((items) => {
      if (cancelled) return;
      setCases(items);
      setSelectedId((current) => current ?? items[0]?.human_review_case_id ?? null);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = useMemo(
    () => cases.find((item) => item.human_review_case_id === selectedId) ?? cases[0] ?? null,
    [cases, selectedId]
  );

  if (!selected) return null;

  async function runAction(action: HumanReviewAction, reason: string) {
    if (!selected || busy) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await applyHumanReviewAction(
        selected.human_review_case_id,
        action,
        reason,
        action === "ACCEPT_AS_CONTEXT"
          ? "Limitación conservada como contexto no canónico."
          : undefined
      );
      setCases((current) =>
        current.map((item) =>
          item.human_review_case_id === updated.human_review_case_id ? updated : item
        )
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Human-review action failed");
    } finally {
      setBusy(false);
    }
  }

  const canResolve = selected.state !== "RESOLVED" && selected.state !== "CANCELLED";

  return (
    <aside
      className="human-review-bridge"
      aria-label="Human Review"
      data-state={selected.state}
      data-case-type={selected.case_type}
    >
      <header>
        <div>
          <span>HUMAN REVIEW</span>
          <strong>{selected.case_type}</strong>
        </div>
        <select
          aria-label="Seleccionar expediente de revisión"
          value={selected.human_review_case_id}
          onChange={(event) => setSelectedId(event.target.value)}
        >
          {cases.map((item) => (
            <option key={item.human_review_case_id} value={item.human_review_case_id}>
              {item.priority} · {item.state}
            </option>
          ))}
        </select>
      </header>

      <div className="human-review-authority-grid">
        <article data-authority="MODEL_PROPOSAL">
          <span>MODEL PROPOSAL</span>
          <p>{selected.candidate_claim.statement}</p>
          <small>
            {selected.candidate_claim.producer_type} · canonical_claim_id:{" "}
            {selected.candidate_claim.canonical_claim_id ?? "null"}
          </small>
        </article>
        <article data-authority="DETERMINISTIC_DECISION">
          <span>DETERMINISTIC DECISION</span>
          <p>{selected.deterministic_decision.outcome}</p>
          <small>
            {selected.deterministic_decision.policy_version} · canonical_claim_id:{" "}
            {selected.deterministic_decision.canonical_claim_id ?? "null"}
          </small>
        </article>
        <article data-authority="HUMAN_REVIEW">
          <span>HUMAN REVIEW</span>
          <p>{selected.resolution ?? selected.state}</p>
          <small>
            reviewer: {selected.assigned_reviewer_subject ?? "unassigned"} · events:{" "}
            {selected.events.length}
          </small>
        </article>
      </div>

      <details>
        <summary>Evidencia y gates</summary>
        <p>
          Fuente: {selected.source?.name ?? "sin fuente"} · derechos:{" "}
          {selected.source?.rights_status ?? "desconocidos"}
        </p>
        {selected.evidence.map((item) => (
          <blockquote key={item.evidence_id}>{item.text ?? item.title}</blockquote>
        ))}
        <small>
          Gates válidos:{" "}
          {Object.values(selected.deterministic_decision.gate_results).filter(Boolean).length}
        </small>
      </details>

      {error && <p className="human-review-error">{error}</p>}
      {canResolve && (
        <div className="human-review-actions">
          {actions.map((item) => (
            <button
              key={item.action}
              type="button"
              disabled={busy}
              onClick={() => runAction(item.action, item.reason)}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
      {selected.state === "RESOLVED" && (
        <p className="human-review-resolution">
          Resolución: <strong>{selected.resolution}</strong> · no se creó ningún claim canónico.
        </p>
      )}
    </aside>
  );
}
