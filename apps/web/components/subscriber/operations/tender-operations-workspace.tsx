"use client";

import styles from "./operations.module.css";
import {
  AuditSection,
  ChangesSection,
  ClarificationsSection,
  CommercialSection,
  DocumentsSection,
  EvidenceSection,
  OutcomeSection,
  OverviewSection,
  QualificationSection,
  RequirementsSection,
  SubmissionSection,
  TeamSection,
  WorkplanSection
} from "./sections-closure";
import { tenderSections, type ActionType, type TenderOperationAction, type TenderOperationsWorkspaceProps, type TenderRouteState, type TenderSection } from "./types";

const labels: Record<TenderSection, string> = {
  overview: "Overview",
  qualification: "Qualification",
  requirements: "Requirements",
  evidence: "Evidence",
  documents: "Documents",
  workplan: "Workplan",
  clarifications: "Clarifications",
  changes: "Changes",
  commercial: "Commercial",
  team: "Team & approvals",
  submission: "Submission",
  outcome: "Outcome",
  audit: "Audit"
};

const stateContent: Record<Exclude<TenderRouteState, "ready" | "partial" | "stale" | "read_only">, { title: string; body: string; retry?: boolean }> = {
  loading: { title: "Loading workspace", body: "Resolving tenant, capabilities and the current server revision." },
  empty: { title: "Nothing here yet", body: "This section has no records. Empty is not the same as unavailable or restricted." },
  restricted: { title: "Access restricted", body: "The server did not grant the capability required for this route. No protected object details were exposed." },
  source_unavailable: { title: "Source unavailable", body: "The real data adapter is unavailable. AXIGNAL did not replace it with fixtures.", retry: true },
  recoverable_error: { title: "Workspace needs recovery", body: "The last operation did not reconcile cleanly. No external action was taken.", retry: true },
  terminal_error: { title: "Workspace cannot be loaded", body: "A terminal server error prevented a safe workspace response. Contact support with the audit correlation ID." }
};

function RouteState({ state, message, onRetry }: { state: keyof typeof stateContent; message?: string | undefined; onRetry?: (() => void) | undefined }) {
  const content = stateContent[state];
  if (state === "loading") {
    return <section className={styles.statePanel} aria-busy="true" aria-live="polite"><div><span className={styles.label}>TENANT-SCOPED LOAD</span><h2>{content.title}</h2><p>{message ?? content.body}</p><div className={styles.skeleton} /><div className={styles.skeleton} /></div></section>;
  }
  return <section className={styles.statePanel} role={state.includes("error") ? "alert" : "status"}><div><span className={styles.label}>{state.replaceAll("_", " ")}</span><h2>{content.title}</h2><p>{message ?? content.body}</p>{content.retry && onRetry ? <button className={styles.button} type="button" onClick={onRetry}>Retry safely</button> : null}</div></section>;
}

function StateBanner({ state, message }: { state: "partial" | "stale" | "read_only"; message?: string | undefined }) {
  const copy = {
    partial: "Some workspace records are unavailable. Visible records preserve their own freshness and source state.",
    stale: "This view is older than the current tenant revision. Consequential actions will fail closed until reconciled.",
    read_only: "This workspace is read-only. Controls remain visible where useful, but the server will not accept mutations."
  }[state];
  return <aside className={styles.notice} data-tone={state === "stale" ? "critical" : "default"}><strong>{state.replaceAll("_", " ")}</strong><p>{message ?? copy}</p></aside>;
}

function SectionRenderer(props: TenderOperationsWorkspaceProps & { data: NonNullable<TenderOperationsWorkspaceProps["data"]> }) {
  switch (props.section) {
    case "overview": return <OverviewSection {...props} />;
    case "qualification": return <QualificationSection {...props} />;
    case "requirements": return <RequirementsSection {...props} />;
    case "evidence": return <EvidenceSection {...props} />;
    case "documents": return <DocumentsSection {...props} />;
    case "workplan": return <WorkplanSection {...props} />;
    case "clarifications": return <ClarificationsSection {...props} />;
    case "changes": return <ChangesSection {...props} />;
    case "commercial": return <CommercialSection {...props} />;
    case "team": return <TeamSection {...props} />;
    case "submission": return <SubmissionSection {...props} />;
    case "outcome": return <OutcomeSection {...props} />;
    case "audit": return <AuditSection {...props} />;
  }
}

/**
 * Pure UI boundary for the thirteen tender workspace routes.
 * The host owns routing, persistence, capability resolution and confirmation dialogs.
 */
export function TenderOperationsWorkspace(props: TenderOperationsWorkspaceProps) {
  const blockingState = !["ready", "partial", "stale", "read_only"].includes(props.state)
    ? props.state as keyof typeof stateContent
    : null;

  if (blockingState || !props.data) {
    return <main className={styles.workspace} data-testid={`tender-workspace-${props.section}`}><RouteState state={blockingState ?? "empty"} message={props.stateMessage} onRetry={props.onRetry} /></main>;
  }

  const { data } = props;
  return (
    <main className={styles.workspace} data-testid={`tender-workspace-${props.section}`}>
      {data.fixtureMode ? <div className={styles.fixture} role="status">ENGINEERING FIXTURE · NOT LIVE DATA</div> : null}
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}>{data.jurisdiction} · {data.procedure}</span>
          <h1>{data.title}</h1>
          <p>{data.buyer} · Tender {data.tenderId} · Updated {data.updatedAt}</p>
        </div>
        <div className={styles.headerMeta} aria-label="Workspace status">
          <span className={styles.status}>{data.status.replaceAll("_", " ")}</span>
          <span className={styles.count}>REV {data.revision}</span>
          {data.dueAt ? <span className={styles.count}>DUE {data.dueAt}</span> : null}
        </div>
      </header>
      <nav className={styles.sectionNav} aria-label="Tender workspace sections">
        {tenderSections.map((section) => <button key={section} type="button" aria-current={props.section === section ? "page" : undefined} onClick={() => props.onNavigate(section)}>{labels[section]}</button>)}
      </nav>
      <div className={styles.content}>
        {props.state !== "ready" ? <StateBanner state={props.state as "partial" | "stale" | "read_only"} message={props.stateMessage} /> : null}
        <SectionRenderer {...props} data={data} />
      </div>
    </main>
  );
}

export type OperationsActionPayload = Omit<TenderOperationAction, "actionType">;

export interface OperationsWorkspaceProps extends Omit<TenderOperationsWorkspaceProps, "onAction"> {
  onAction: (actionType: ActionType, payload: OperationsActionPayload) => void | Promise<void>;
}

/** Integration-friendly facade using a generic action-type plus payload callback. */
export function OperationsWorkspace({ onAction, ...props }: OperationsWorkspaceProps) {
  return (
    <TenderOperationsWorkspace
      {...props}
      onAction={(action) => {
        const { actionType, ...payload } = action;
        return onAction(actionType, payload);
      }}
    />
  );
}
