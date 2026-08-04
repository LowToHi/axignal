"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { PersistentResearchRunView } from "@/lib/persistent-research";

import styles from "./research-run-page.module.css";

const terminalStates = new Set([
  "COMPLETED",
  "COMPLETED_PROVISIONAL",
  "QUARANTINED",
  "FAILED",
  "CANCELLED",
  "BUDGET_EXHAUSTED",
  "RIGHTS_BLOCKED",
  "INSUFFICIENT_EVIDENCE"
]);

const canonicalStages = [
  "QUEUED",
  "RETRIEVING",
  "CLAIMS_PROPOSED",
  "ADMISSION_QUEUED",
  "COMPLETED"
] as const;

function stageIndex(state: string): number {
  if (["DOCUMENT_PARSING", "SECURITY_SCANNING"].includes(state)) return 1;
  if (["PROPOSING", "EVIDENCE_BINDING"].includes(state)) return 2;
  if (["ADMISSION_PENDING", "HANDOFF_PENDING"].includes(state)) return 3;
  if (["COMPLETED", "COMPLETED_PROVISIONAL"].includes(state)) return 4;
  return Math.max(0, canonicalStages.indexOf(state as (typeof canonicalStages)[number]));
}

async function readView(researchRunId: string): Promise<PersistentResearchRunView> {
  const response = await fetch(`/api/research/runs/${researchRunId}`, {
    cache: "no-store"
  });
  const body = (await response.json().catch(() => null)) as
    | PersistentResearchRunView
    | { error?: unknown }
    | null;
  if (!response.ok) {
    throw new Error(
      body && "error" in body && typeof body.error === "string"
        ? body.error
        : `ResearchRun status failed with ${response.status}.`
    );
  }
  return body as PersistentResearchRunView;
}

export function ResearchRunPage({ researchRunId }: { researchRunId: string }) {
  const [view, setView] = useState<PersistentResearchRunView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    async function poll() {
      try {
        const next = await readView(researchRunId);
        if (cancelled) return;
        setView(next);
        setError(null);
        const terminal = terminalStates.has(next.state);
        setRefreshing(!terminal);
        if (!terminal) timer = setTimeout(() => void poll(), 1_000);
      } catch (cause) {
        if (cancelled) return;
        setError(
          cause instanceof Error
            ? cause.message
            : "ResearchRun status is unavailable."
        );
        setRefreshing(false);
      }
    }

    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [researchRunId]);

  const currentStage = view ? stageIndex(view.state) : 0;

  return (
    <main className={styles.page} data-testid="research-run-page">
      <header className={styles.header}>
        <div>
          <span>AXIGNAL PERSISTENT RESEARCH</span>
          <h1>ResearchRun</h1>
          <p>
            Server-authoritative worker state. No synthetic result is substituted
            when the persistent API is unavailable.
          </p>
        </div>
        <nav aria-label="Research run navigation">
          <Link href="/investigations">Back to investigations</Link>
          {view?.opportunity_id ? (
            <Link href={`/investigations?opportunity=${encodeURIComponent(view.opportunity_id)}`}>
              Open opportunity
            </Link>
          ) : null}
        </nav>
      </header>

      <section className={styles.status} aria-live="polite" aria-busy={refreshing}>
        <span>RUN ID</span>
        <code>{researchRunId}</code>
        <strong>{view?.state ?? (error ? "UNAVAILABLE" : "LOADING")}</strong>
        <small>{refreshing ? "Polling persistent worker state…" : "Polling stopped."}</small>
      </section>

      {error ? (
        <section className={styles.error} role="alert">
          <h2>ResearchRun unavailable</h2>
          <p>{error}</p>
          <button
            type="button"
            onClick={() => {
              setError(null);
              setRefreshing(true);
              void readView(researchRunId)
                .then((next) => {
                  setView(next);
                  setRefreshing(!terminalStates.has(next.state));
                })
                .catch((cause) => {
                  setError(cause instanceof Error ? cause.message : "ResearchRun status is unavailable.");
                  setRefreshing(false);
                });
            }}
          >
            Retry once
          </button>
        </section>
      ) : null}

      <section className={styles.progress} aria-label="ResearchRun progress">
        {canonicalStages.map((stage, index) => (
          <article key={stage} data-state={index < currentStage ? "complete" : index === currentStage ? "current" : "pending"}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{stage.replaceAll("_", " ")}</strong>
          </article>
        ))}
      </section>

      {view ? (
        <>
          <section className={styles.summary}>
            <article><span>QUESTION</span><strong>{view.question}</strong></article>
            <article><span>OPPORTUNITY</span><strong>{view.opportunity_id}</strong></article>
            <article><span>CONTEXT</span><strong>{view.context_id}</strong></article>
            <article><span>PRIVATE KNOWLEDGE</span><strong>{view.private_knowledge_authorised ? "AUTHORISED" : "NOT AUTHORISED"}</strong></article>
          </section>

          <div className={styles.grid}>
            <section>
              <header><h2>Sources</h2><span>{view.source_plan.length}</span></header>
              {view.source_plan.length ? view.source_plan.map((source, index) => (
                <pre key={String(source.source_id ?? index)}>{JSON.stringify(source, null, 2)}</pre>
              )) : <p>No source plan has been published yet.</p>}
            </section>
            <section>
              <header><h2>Evidence</h2><span>{view.evidence.length}</span></header>
              {view.evidence.length ? view.evidence.map((item) => (
                <article key={item.evidence_id}>
                  <strong>{item.title}</strong>
                  <small>{item.source_id} · {item.rights_status} · {item.relationship}</small>
                </article>
              )) : <p>No evidence has been persisted yet.</p>}
            </section>
            <section>
              <header><h2>Candidate Claims</h2><span>{view.candidate_claims.length}</span></header>
              {view.candidate_claims.length ? view.candidate_claims.map((item) => (
                <article key={item.candidate_claim_id}>
                  <strong>{item.statement}</strong>
                  <small>{item.state} · {item.producer_type} · {item.method_version}</small>
                </article>
              )) : <p>No Candidate Claims have been proposed yet.</p>}
            </section>
            <section>
              <header><h2>Admitted Claims</h2><span>{view.canonical_claims.length}</span></header>
              {view.canonical_claims.length ? view.canonical_claims.map((item) => (
                <article key={item.canonical_claim_id}>
                  <strong>{item.statement}</strong>
                  <small>{item.state} · {item.epistemic_class}</small>
                </article>
              )) : <p>No canonical claim has been admitted yet.</p>}
            </section>
          </div>

          <section className={styles.dossier}>
            <header><h2>Dossier</h2><span>{view.dossier?.status ?? "NOT AVAILABLE"}</span></header>
            {view.dossier ? (
              <>
                <h3>{view.dossier.title}</h3>
                <p>{view.dossier.summary}</p>
                <small>{view.dossier.dossier_id}</small>
              </>
            ) : <p>The worker has not produced a dossier.</p>}
          </section>

          {view.error_code ? (
            <section className={styles.error} role="alert">
              <h2>{view.error_code}</h2>
              <p>{view.error_detail ?? "The persistent run failed closed without additional detail."}</p>
            </section>
          ) : null}
        </>
      ) : null}
    </main>
  );
}
