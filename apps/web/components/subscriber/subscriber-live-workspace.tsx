"use client";

import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import type {
  ApiError,
  LiveDocument,
  LiveResearchAccepted,
  LiveResearchRun,
  LiveWorkspace,
  SubscriberLiveBootstrap
} from "@/lib/subscriber-live-contract";

import styles from "./subscriber-live-workspace.module.css";

type Props = {
  initialIdentity: {
    email: string;
    subject: string;
    tenantId: string;
  };
};

type RequestState = "idle" | "pending" | "error";

const terminalStates = new Set([
  "COMPLETED",
  "COMPLETED_PROVISIONAL",
  "FAILED",
  "CANCELLED",
  "BUDGET_EXHAUSTED",
  "RIGHTS_BLOCKED",
  "INSUFFICIENT_EVIDENCE",
  "QUARANTINED"
]);

async function readJson<T>(response: Response, operation: string): Promise<T> {
  const body = (await response.json().catch(() => null)) as T | ApiError | null;
  if (!response.ok) {
    const error = body as ApiError | null;
    throw new Error(error?.detail ?? error?.error ?? `${operation} failed (${response.status})`);
  }
  if (!body) throw new Error(`${operation} returned an empty response.`);
  return body as T;
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function sourceId(source: Record<string, unknown>, index: number): string {
  const value = source.source_id;
  return typeof value === "string" && value ? value : `source-${index + 1}`;
}

function sectionTitle(section: Record<string, unknown>, index: number): string {
  return typeof section.title === "string" && section.title
    ? section.title
    : `Section ${index + 1}`;
}

function sectionText(section: Record<string, unknown>): string {
  return typeof section.text === "string" ? section.text : JSON.stringify(section, null, 2);
}

function mergeRun(runs: LiveResearchRun[], current: LiveResearchRun | null): LiveResearchRun[] {
  if (!current) return runs;
  return [current, ...runs.filter((item) => item.research_run_id !== current.research_run_id)];
}

export function SubscriberLiveWorkspace({ initialIdentity }: Props) {
  const [bootstrap, setBootstrap] = useState<SubscriberLiveBootstrap | null>(null);
  const [bootstrapState, setBootstrapState] = useState<RequestState>("pending");
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [researchState, setResearchState] = useState<RequestState>("idle");
  const [currentRun, setCurrentRun] = useState<LiveResearchRun | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [documentTitle, setDocumentTitle] = useState("Research response");
  const [documentBody, setDocumentBody] = useState("");
  const [mutationState, setMutationState] = useState<RequestState>("idle");
  const [downloadExportId, setDownloadExportId] = useState<string | null>(null);

  const loadBootstrap = useCallback(async () => {
    setBootstrapState("pending");
    try {
      const response = await fetch("/api/subscriber-workspace/live/bootstrap", {
        cache: "no-store"
      });
      const next = await readJson<SubscriberLiveBootstrap>(response, "Workspace bootstrap");
      if (
        next.fixture_boundary.active ||
        next.fixture_boundary.mode !== "PERSISTENT_REAL_ADAPTER" ||
        next.fixture_boundary.fallback_allowed
      ) {
        throw new Error("The visible workspace rejected a non-persistent data boundary.");
      }
      setBootstrap(next);
      setSelectedRunId((value) => value ?? next.research_runs[0]?.research_run_id ?? null);
      setSelectedWorkspaceId((value) => value ?? next.workspaces[0]?.workspace_id ?? null);
      setError(null);
      setBootstrapState("idle");
    } catch (caught) {
      setBootstrap(null);
      setBootstrapState("error");
      setError(caught instanceof Error ? caught.message : "Workspace bootstrap failed.");
    }
  }, []);

  useEffect(() => {
    void loadBootstrap();
  }, [loadBootstrap]);

  const researchRuns = useMemo(
    () => mergeRun(bootstrap?.research_runs ?? [], currentRun),
    [bootstrap?.research_runs, currentRun]
  );
  const selectedRun =
    researchRuns.find((item) => item.research_run_id === selectedRunId) ?? researchRuns[0] ?? null;
  const selectedWorkspace =
    bootstrap?.workspaces.find((item) => item.workspace_id === selectedWorkspaceId) ??
    bootstrap?.workspaces[0] ??
    null;
  const selectedDocuments = useMemo(
    () =>
      (bootstrap?.documents ?? []).filter(
        (item) => item.workspace_id === selectedWorkspace?.workspace_id
      ),
    [bootstrap?.documents, selectedWorkspace?.workspace_id]
  );
  const selectedAudit = useMemo(
    () =>
      (bootstrap?.audit ?? []).filter(
        (item) => !selectedWorkspace || item.workspace_id === selectedWorkspace.workspace_id
      ),
    [bootstrap?.audit, selectedWorkspace]
  );
  const capabilities = new Set(bootstrap?.capabilities ?? []);

  const pollRun = useCallback(
    async (runId: string) => {
      for (let attempt = 0; attempt < 100; attempt += 1) {
        const response = await fetch(
          `/api/subscriber-workspace/live/research-runs/${runId}`,
          { cache: "no-store" }
        );
        const view = await readJson<LiveResearchRun>(response, "ResearchRun polling");
        if (view.synthetic !== false) {
          throw new Error("Synthetic ResearchRun data is forbidden in the main workspace.");
        }
        setCurrentRun(view);
        setSelectedRunId(view.research_run_id);
        if (terminalStates.has(view.state)) {
          await loadBootstrap();
          return view;
        }
        await new Promise((resolve) => window.setTimeout(resolve, 750));
      }
      throw new Error("ResearchRun is still active; polling limit reached without a terminal state.");
    },
    [loadBootstrap]
  );

  async function submitResearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || researchState === "pending") return;
    setResearchState("pending");
    setError(null);
    setCurrentRun(null);
    try {
      const response = await fetch("/api/subscriber-workspace/live/research-runs", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question: trimmed })
      });
      const accepted = await readJson<LiveResearchAccepted>(response, "ResearchRun creation");
      if (accepted.synthetic !== false || accepted.source_ids.length === 0) {
        throw new Error("ResearchRun was not bound to a real admitted source.");
      }
      setSelectedRunId(accepted.research_run_id);
      await pollRun(accepted.research_run_id);
      setQuestion("");
      setResearchState("idle");
    } catch (caught) {
      setResearchState("error");
      setError(caught instanceof Error ? caught.message : "ResearchRun failed.");
    }
  }

  async function createWorkspace(run: LiveResearchRun) {
    setMutationState("pending");
    setError(null);
    try {
      const response = await fetch("/api/subscriber-workspace/live/workspaces", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ research_run_id: run.research_run_id })
      });
      const result = await readJson<{ workspace: LiveWorkspace }>(response, "Workspace creation");
      setSelectedWorkspaceId(result.workspace.workspace_id);
      await loadBootstrap();
      setMutationState("idle");
    } catch (caught) {
      setMutationState("error");
      setError(caught instanceof Error ? caught.message : "Workspace creation failed.");
    }
  }

  async function createDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedWorkspace || !documentTitle.trim() || !documentBody.trim()) return;
    setMutationState("pending");
    setError(null);
    try {
      const response = await fetch("/api/subscriber-workspace/live/documents", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          workspace_id: selectedWorkspace.workspace_id,
          title: documentTitle.trim(),
          body: documentBody.trim()
        })
      });
      await readJson<{ document: LiveDocument }>(response, "Document creation");
      setDocumentBody("");
      await loadBootstrap();
      setMutationState("idle");
    } catch (caught) {
      setMutationState("error");
      setError(caught instanceof Error ? caught.message : "Document creation failed.");
    }
  }

  async function createExport(document: LiveDocument | null) {
    if (!selectedWorkspace) return;
    setMutationState("pending");
    setError(null);
    try {
      const response = await fetch("/api/subscriber-workspace/live/exports", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          workspace_id: selectedWorkspace.workspace_id,
          document_id: document?.document_id ?? null,
          format: "MARKDOWN"
        })
      });
      const result = await readJson<{ export: { export_id: string } }>(
        response,
        "Export creation"
      );
      setDownloadExportId(result.export.export_id);
      await loadBootstrap();
      setMutationState("idle");
    } catch (caught) {
      setMutationState("error");
      setError(caught instanceof Error ? caught.message : "Export creation failed.");
    }
  }

  if (bootstrapState === "pending" && !bootstrap) {
    return (
      <main className={styles.statePage} aria-live="polite" data-e2e-no-fixtures="true">
        <strong>Connecting to the persistent AXIGNAL workspace…</strong>
        <span>{initialIdentity.email}</span>
      </main>
    );
  }

  if (!bootstrap) {
    return (
      <main className={styles.statePage} role="alert" data-e2e-terminal-error="true">
        <strong>Persistent workspace unavailable</strong>
        <p>{error ?? "The authenticated workspace could not be loaded."}</p>
        <button type="button" onClick={() => void loadBootstrap()}>Retry</button>
      </main>
    );
  }

  return (
    <main className={styles.root} data-e2e-no-fixtures="true" data-adapter="persistent-real">
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}>AXIGNAL · SUBSCRIBER WORKSPACE</span>
          <h1>Persistent opportunity intelligence</h1>
          <p>No fixture fallback. Every visible record is tenant-scoped and server-resolved.</p>
        </div>
        <dl className={styles.identityGrid}>
          <div><dt>Identity</dt><dd>{bootstrap.identity.email}</dd></div>
          <div><dt>Organisation</dt><dd>{bootstrap.organisation.display_name}</dd></div>
          <div><dt>Plan</dt><dd>{bootstrap.entitlement?.plan_code ?? bootstrap.identity.seat_plan_code ?? "No active plan"}</dd></div>
          <div><dt>Entitlement</dt><dd>{bootstrap.entitlement?.state ?? bootstrap.identity.seat_state ?? "READ_ONLY"}</dd></div>
          <div><dt>Assurance</dt><dd>{bootstrap.identity.assurance_level ?? "Unspecified"}</dd></div>
          <div><dt>Tenant</dt><dd><code>{bootstrap.identity.tenant_id}</code></dd></div>
        </dl>
      </header>

      {error && <div className={styles.error} role="alert">{error}</div>}

      <section className={styles.navigator} aria-labelledby="navigator-title">
        <div>
          <span className={styles.eyebrow}>NAVIGATOR</span>
          <h2 id="navigator-title">Create a persistent TED ResearchRun</h2>
          <p>The worker retrieves an admitted source, persists evidence and claims, executes deterministic admission and materialises a dossier.</p>
        </div>
        <form onSubmit={submitResearch} className={styles.navigatorForm}>
          <label htmlFor="live-research-question">Research question</label>
          <textarea
            id="live-research-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={3}
            maxLength={8000}
            placeholder="Find active public procurement opportunities relevant to our governed data platform."
            disabled={!capabilities.has("research:create") || researchState === "pending"}
          />
          <button
            type="submit"
            disabled={!capabilities.has("research:create") || !question.trim() || researchState === "pending"}
          >
            {researchState === "pending" ? "Researching…" : "Start ResearchRun"}
          </button>
        </form>
      </section>

      <div className={styles.layout}>
        <aside className={styles.rail} aria-label="Persistent ResearchRuns">
          <div className={styles.railHeader}>
            <h2>ResearchRuns</h2>
            <span>{researchRuns.length}</span>
          </div>
          {researchRuns.length === 0 ? (
            <p className={styles.empty}>No persistent research exists for this tenant.</p>
          ) : (
            researchRuns.map((run) => (
              <button
                type="button"
                key={run.research_run_id}
                className={run.research_run_id === selectedRun?.research_run_id ? styles.selectedItem : styles.railItem}
                onClick={() => setSelectedRunId(run.research_run_id)}
              >
                <strong>{run.question}</strong>
                <span>{run.state}</span>
                <small>{formatDate(run.updated_at)}</small>
              </button>
            ))
          )}
        </aside>

        <section className={styles.canvas} aria-label="InvestigationContext">
          {!selectedRun ? (
            <div className={styles.emptyPanel}>
              <h2>InvestigationContext is empty</h2>
              <p>Start a ResearchRun. No synthetic opportunity is inserted automatically.</p>
            </div>
          ) : (
            <>
              <div className={styles.runHeader}>
                <div>
                  <span className={styles.status} data-state={selectedRun.state}>{selectedRun.state}</span>
                  <h2>{selectedRun.question}</h2>
                  <code>{selectedRun.research_run_id}</code>
                </div>
                {selectedRun.dossier && terminalStates.has(selectedRun.state) && capabilities.has("workspace:create") && (
                  <button
                    type="button"
                    onClick={() => void createWorkspace(selectedRun)}
                    disabled={mutationState === "pending"}
                  >
                    Open persistent workspace
                  </button>
                )}
              </div>

              <div className={styles.metricGrid}>
                <div><span>Sources</span><strong>{selectedRun.source_plan.length}</strong></div>
                <div><span>Evidence</span><strong>{selectedRun.evidence.length}</strong></div>
                <div><span>Candidate claims</span><strong>{selectedRun.candidate_claims.length}</strong></div>
                <div><span>Admitted claims</span><strong>{selectedRun.canonical_claims.length}</strong></div>
              </div>

              <section className={styles.panel}>
                <h3>Source acquisition</h3>
                {selectedRun.source_plan.length === 0 ? <p className={styles.empty}>No source plan persisted.</p> : (
                  <ul>{selectedRun.source_plan.map((source, index) => <li key={`${sourceId(source, index)}-${index}`}><code>{sourceId(source, index)}</code></li>)}</ul>
                )}
              </section>

              <section className={styles.panel}>
                <h3>Persistent evidence</h3>
                {selectedRun.evidence.length === 0 ? <p className={styles.empty}>Evidence has not been persisted yet.</p> : (
                  <div className={styles.cardGrid}>{selectedRun.evidence.map((item) => (
                    <article key={item.evidence_id} className={styles.card}>
                      <span>{item.relationship}</span>
                      <h4>{item.title}</h4>
                      <p><code>{item.source_id}</code></p>
                      <small>{item.rights_status} · {formatDate(item.observed_at)}</small>
                    </article>
                  ))}</div>
                )}
              </section>

              <section className={styles.panel}>
                <h3>Claims and deterministic admission</h3>
                {selectedRun.candidate_claims.length === 0 ? <p className={styles.empty}>Claims have not been proposed yet.</p> : (
                  <div className={styles.cardGrid}>{selectedRun.candidate_claims.map((claim) => (
                    <article key={claim.candidate_claim_id} className={styles.card}>
                      <span>{claim.kind} · {claim.state}</span>
                      <p>{claim.statement}</p>
                      <small>{claim.producer_type} · {claim.method_version}</small>
                      {claim.canonical_claim_id && <code>{claim.canonical_claim_id}</code>}
                    </article>
                  ))}</div>
                )}
              </section>

              <section className={styles.panel}>
                <h3>Persistent dossier</h3>
                {!selectedRun.dossier ? <p className={styles.empty}>The worker has not materialised a dossier yet.</p> : (
                  <article className={styles.dossier}>
                    <span>{selectedRun.dossier.status}</span>
                    <h4>{selectedRun.dossier.title}</h4>
                    <p>{selectedRun.dossier.summary}</p>
                    {selectedRun.dossier.sections.map((section, index) => (
                      <details key={`${sectionTitle(section, index)}-${index}`}>
                        <summary>{sectionTitle(section, index)}</summary>
                        <pre>{sectionText(section)}</pre>
                      </details>
                    ))}
                  </article>
                )}
              </section>
            </>
          )}
        </section>
      </div>

      <section className={styles.workspaceSection} aria-labelledby="workspace-title">
        <div className={styles.workspaceHeader}>
          <div>
            <span className={styles.eyebrow}>OPERATIONS</span>
            <h2 id="workspace-title">Persistent workspace, document and export</h2>
          </div>
          <select
            aria-label="Select persistent workspace"
            value={selectedWorkspace?.workspace_id ?? ""}
            onChange={(event) => setSelectedWorkspaceId(event.target.value || null)}
          >
            <option value="">No workspace selected</option>
            {bootstrap.workspaces.map((workspace) => (
              <option key={workspace.workspace_id} value={workspace.workspace_id}>{workspace.title}</option>
            ))}
          </select>
        </div>

        {!selectedWorkspace ? (
          <p className={styles.emptyPanel}>A workspace can be opened only from a completed ResearchRun with a persistent dossier.</p>
        ) : (
          <div className={styles.operationsGrid}>
            <article className={styles.panel}>
              <h3>{selectedWorkspace.title}</h3>
              <dl className={styles.details}>
                <div><dt>Workspace</dt><dd><code>{selectedWorkspace.workspace_id}</code></dd></div>
                <div><dt>ResearchRun</dt><dd><code>{selectedWorkspace.research_run_id}</code></dd></div>
                <div><dt>Revision</dt><dd>{selectedWorkspace.revision}</dd></div>
                <div><dt>Owner</dt><dd>{selectedWorkspace.owner_subject}</dd></div>
              </dl>
            </article>

            <form className={styles.panel} onSubmit={createDocument}>
              <h3>Create persistent document</h3>
              <label htmlFor="document-title">Title</label>
              <input id="document-title" value={documentTitle} onChange={(event) => setDocumentTitle(event.target.value)} maxLength={300} disabled={!capabilities.has("document:create")} />
              <label htmlFor="document-body">Body</label>
              <textarea id="document-body" value={documentBody} onChange={(event) => setDocumentBody(event.target.value)} rows={7} maxLength={200000} disabled={!capabilities.has("document:create")} />
              <button type="submit" disabled={!capabilities.has("document:create") || mutationState === "pending" || !documentTitle.trim() || !documentBody.trim()}>Persist document</button>
            </form>

            <article className={styles.panel}>
              <div className={styles.panelHeader}>
                <h3>Documents</h3>
                <button type="button" disabled={!capabilities.has("export:create") || mutationState === "pending"} onClick={() => void createExport(selectedDocuments[0] ?? null)}>Create Markdown export</button>
              </div>
              {selectedDocuments.length === 0 ? <p className={styles.empty}>No persistent document exists.</p> : selectedDocuments.map((document) => (
                <div key={document.document_id} className={styles.document}>
                  <strong>{document.title}</strong>
                  <span>v{document.version} · {document.status}</span>
                  <p>{document.body}</p>
                </div>
              ))}
              {downloadExportId && (
                <a className={styles.download} href={`/api/subscriber-workspace/live/exports/${downloadExportId}/download`}>Download verified Markdown export</a>
              )}
            </article>

            <article className={styles.panel}>
              <h3>Append-only audit</h3>
              {selectedAudit.length === 0 ? <p className={styles.empty}>No workspace audit event exists.</p> : (
                <ol className={styles.audit}>{selectedAudit.map((event) => (
                  <li key={event.audit_event_id}>
                    <strong>{event.event_type}</strong>
                    <span>{event.actor_subject}</span>
                    <small>{formatDate(event.occurred_at)}</small>
                  </li>
                ))}</ol>
              )}
            </article>
          </div>
        )}
      </section>
    </main>
  );
}
