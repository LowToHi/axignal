import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { QualificationForm } from "@/components/opportunities/qualification-form";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Opportunity — AXIGNAL",
  description: "Evidence, claims and qualification.",
  robots: { index: false, follow: false }
};

type Opportunity = {
  opportunity_ref: string;
  library_id: string;
  publication_number: string | null;
  version: number;
  content_hash: string;
  source_id: string;
  produced_by: string;
  produced_at: string;
  state: string;
  payload: Record<string, unknown> | null;
};

type ClaimsBundle = {
  notices: Array<Record<string, unknown>>;
  evidence: Array<Record<string, unknown>>;
  canonical_claims: Array<Record<string, unknown>>;
};

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(
      `${process.env.AXIGNAL_PUBLIC_ORIGIN ?? "http://localhost:18080"}${path}`,
      { cache: "no-store", signal: AbortSignal.timeout(8_000) }
    );
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export default async function OpportunityDetailPage({
  params
}: {
  params: Promise<{ opportunityRef: string }>;
}) {
  const { opportunityRef } = await params;
  const opportunity = await fetchJson<Opportunity>(
    `/api/opportunities/opportunities/${opportunityRef}`
  );
  if (!opportunity) {
    notFound();
  }
  const claims = await fetchJson<ClaimsBundle>(
    `/api/opportunities/opportunities/${opportunityRef}/claims`
  );

  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1rem" }}>
      <p>
        <a href="/opportunity-intelligence/opportunities">← Opportunities</a>
      </p>
      <h1>{opportunity.opportunity_ref}</h1>
      <dl>
        <dt>Library</dt>
        <dd>{opportunity.library_id}</dd>
        <dt>Notice</dt>
        <dd>{opportunity.publication_number ?? "—"}</dd>
        <dt>Version</dt>
        <dd>{opportunity.version}</dd>
        <dt>State</dt>
        <dd>{opportunity.state}</dd>
        <dt>Source</dt>
        <dd>{opportunity.source_id}</dd>
        <dt>Content hash</dt>
        <dd>
          <code>{opportunity.content_hash}</code>
        </dd>
        <dt>Produced by</dt>
        <dd>{opportunity.produced_by}</dd>
      </dl>

      <h2>Qualification</h2>
      <QualificationForm
        opportunityRef={opportunity.opportunity_ref}
        currentState={opportunity.state}
      />

      <h2>Evidence</h2>
      {claims && claims.evidence.length > 0 ? (
        <ul>
          {claims.evidence.map((evidence) => (
            <li key={String(evidence.evidence_id)}>
              <strong>{String(evidence.title ?? evidence.predicate)}</strong>{" "}
              ({String(evidence.relationship)}) — {String(evidence.subject_id)}
            </li>
          ))}
        </ul>
      ) : (
        <p>Sin evidencia persistida para esta oportunidad.</p>
      )}

      <h2>Canonical claims</h2>
      {claims && claims.canonical_claims.length > 0 ? (
        <ul>
          {claims.canonical_claims.map((claim) => (
            <li key={String(claim.canonical_claim_id)}>
              <code>{String(claim.predicate)}</code>: {String(claim.statement)}
            </li>
          ))}
        </ul>
      ) : (
        <p>Sin claims canónicos para esta oportunidad.</p>
      )}

      <h2>Notices</h2>
      {claims && claims.notices.length > 0 ? (
        <ul>
          {claims.notices.map((notice) => (
            <li key={String(notice.publication_number)}>
              {String(notice.publication_number)} — version{" "}
              {String(notice.current_version)} ({String(notice.state)})
            </li>
          ))}
        </ul>
      ) : (
        <p>Sin notices asociados.</p>
      )}
    </main>
  );
}
