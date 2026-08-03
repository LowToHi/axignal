"use client";

import { useEffect, useState, type ReactNode } from "react";

import styles from "./operations.module.css";
import type {
  AuditRecord,
  Capability,
  TenderOperationsWorkspaceProps,
  TenderWorkspaceData
} from "./types";

export {
  ChangesSection,
  ClarificationsSection,
  CommercialSection,
  EvidenceSection,
  OutcomeSection,
  OverviewSection,
  RequirementsSection,
  SubmissionSection,
  WorkplanSection
} from "./sections";

type SectionProps = Pick<
  TenderOperationsWorkspaceProps,
  "capabilities" | "mutationFeedback" | "onAction" | "state"
> & { data: TenderWorkspaceData };

type AuditApiEvent = {
  id: string;
  workspace_id: string | null;
  actor_id: string;
  type: string;
  object_type: string;
  object_id: string;
  occurred_at: string;
  details: Record<string, string | number | boolean | null>;
};

type AuditApiResponse = {
  events?: AuditApiEvent[];
  next_cursor?: number;
};

function can(capabilities: ReadonlySet<Capability>, capability: Capability): boolean {
  return capabilities.has(capability);
}

function routeMutationDisabled(props: SectionProps): boolean {
  return props.state === "read_only" || props.state === "stale";
}

function canMutate(props: SectionProps, capability: Capability): boolean {
  return !routeMutationDisabled(props) && can(props.capabilities, capability);
}

function Heading({ title, description, actions }: { title: string; description: string; actions?: ReactNode }) {
  return (
    <header className={styles.sectionHeading}>
      <div><h2>{title}</h2><p>{description}</p></div>
      {actions ? <div className={styles.toolbar}>{actions}</div> : null}
    </header>
  );
}

function AuthorityNotice({ children, critical = false }: { children: ReactNode; critical?: boolean }) {
  return (
    <aside className={styles.notice} data-tone={critical ? "critical" : "default"}>
      <strong>{critical ? "HUMAN AUTHORITY REQUIRED" : "AUTHORITY BOUNDARY"}</strong>
      <p>{children}</p>
    </aside>
  );
}

function Status({ value, tone = "neutral" }: { value: string; tone?: "neutral" | "positive" | "warning" | "critical" }) {
  return <span className={styles.status} data-tone={tone}>{value.replaceAll("_", " ")}</span>;
}

export function QualificationSection(props: SectionProps) {
  const [decision, setDecision] = useState<"review" | "pursue" | "no_bid">("review");
  const [rationale, setRationale] = useState("");
  const pending = props.mutationFeedback?.["workspace.qualify"]?.state === "pending";
  const permitted = canMutate(props, "workspace:qualify");
  const hasDecision = decision !== "review";
  const hasRationale = rationale.trim().length >= 10;
  const canSubmit = permitted && hasDecision && hasRationale && !pending;

  return (
    <>
      <Heading title="Qualification" description="Record an explicit, reversible pursue decision with rationale." />
      <AuthorityNotice critical>
        An AI signal or high opportunity score does not authorise a bid/no-bid decision. Continue review preserves the undecided state and never records pursue.
      </AuthorityNotice>
      <div className={styles.grid}>
        <article className={`${styles.card} ${styles.cardWide}`}>
          <h3>Decision record</h3>
          <div className={styles.formRow}>
            <label className={styles.field}>Decision
              <select
                value={decision}
                onChange={(event) => setDecision(event.target.value as typeof decision)}
                disabled={!permitted || pending}
              >
                <option value="review">Continue review — no decision</option>
                <option value="pursue">Pursue</option>
                <option value="no_bid">Do not pursue</option>
              </select>
            </label>
            <label className={styles.field}>Rationale
              <input
                value={rationale}
                onChange={(event) => setRationale(event.target.value)}
                placeholder="Required decision rationale (minimum 10 characters)"
                disabled={!permitted || pending}
              />
            </label>
          </div>
          <button
            className={styles.primary}
            data-testid="qualification-decision-submit"
            type="button"
            disabled={!canSubmit}
            onClick={() => {
              if (!canSubmit || decision === "review") return;
              void props.onAction({
                actionType: "workspace.qualify",
                workspaceId: props.data.workspaceId,
                payload: { decision, rationale: rationale.trim() }
              });
            }}
          >
            {pending ? "Recording…" : hasDecision ? "Record qualification decision" : "Select pursue or do not pursue"}
          </button>
          {!permitted ? <p className={styles.feedback} role="status">You can review this section, but your server-resolved capabilities do not permit qualification.</p> : null}
          {permitted && !hasDecision ? <p className={styles.feedback} role="status">Continue review is intentionally non-mutating. Select an explicit decision to persist it.</p> : null}
          {permitted && hasDecision && !hasRationale ? <p className={styles.feedback} role="status">Add a rationale of at least 10 characters before recording the decision.</p> : null}
        </article>
        <article className={styles.card}>
          <h3>Known blockers</h3>
          <p>{props.data.readiness?.blockingItems.length ?? 0} current blockers. Unknowns remain explicit and are not treated as zero.</p>
        </article>
      </div>
    </>
  );
}

export function DocumentsSection(props: SectionProps) {
  return (
    <>
      <Heading
        title="Documents"
        description="Versioned bid artefacts with explicit review and ownership."
        actions={<button className={styles.primary} type="button" disabled>Create draft unavailable</button>}
      />
      <AuthorityNotice>
        Document creation is not exposed as an operational action until the tenant-scoped persistent document contract, version ledger and recovery path are available. Existing records remain reviewable.
      </AuthorityNotice>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <caption>Versioned workspace documents</caption>
          <thead><tr><th scope="col">Document</th><th scope="col">Version</th><th scope="col">Owner</th><th scope="col">Status</th><th scope="col">Updated</th></tr></thead>
          <tbody>{(props.data.documents ?? []).map((record) => <tr key={record.id}>
            <td><strong>{record.title}</strong>{record.lockOwner ? <span className={styles.subtle}>Editing lock: {record.lockOwner}</span> : null}</td>
            <td>{record.version}</td><td>{record.owner}</td><td><Status value={record.status} tone={record.status === "approved" ? "positive" : "neutral"} /></td><td>{record.updatedAt}</td>
          </tr>)}</tbody>
        </table>
      </div>
    </>
  );
}

export function TeamSection(props: SectionProps) {
  return (
    <>
      <Heading title="Team & approvals" description="Workspace responsibility and separated approval state." />
      <div className={styles.grid}>
        <section className={`${styles.card} ${styles.cardWide}`}>
          <h3>Workspace team</h3>
          <div className={styles.list}>{(props.data.team ?? []).map((member) => <article className={styles.listItem} key={member.id}>
            <div><h3>{member.name}</h3><p>{member.role} · {member.responsibility}</p></div>
            <Status value={member.status} tone={member.status === "active" ? "positive" : "warning"} />
          </article>)}</div>
        </section>
        <section className={styles.card}>
          <h3>Approvals</h3>
          <div className={styles.list}>{(props.data.approvals ?? []).map((approval) => <article key={approval.id}>
            <strong>{approval.subject}</strong>
            <p>Requested from {approval.requestedFrom}</p>
            <Status value={approval.status} tone={approval.status === "approved" ? "positive" : approval.status === "rejected" ? "critical" : "warning"} />
            {approval.status === "pending" ? <p className={styles.subtle}>Approval recording is unavailable until the persistent approval and separation-of-duties contract is implemented.</p> : null}
          </article>)}</div>
        </section>
      </div>
    </>
  );
}

function auditDetail(event: AuditApiEvent): string {
  const entries = Object.entries(event.details);
  const detail = entries.length > 0
    ? entries.map(([key, value]) => `${key}=${String(value)}`).join(" · ")
    : "No additional detail disclosed";
  return `${event.object_type}:${event.object_id} · ${detail}`;
}

function auditRecord(event: AuditApiEvent): AuditRecord {
  return {
    id: event.id,
    event: event.type,
    actor: event.actor_id,
    occurredAt: event.occurred_at,
    detail: auditDetail(event),
    outcome: event.type === "mutation.denied" ? "denied" : "recorded"
  };
}

export function AuditSection(props: SectionProps) {
  const permitted = can(props.capabilities, "audit:view");
  const [records, setRecords] = useState<AuditRecord[]>(() => [...(props.data.audit ?? [])]);
  const [auditState, setAuditState] = useState<"loading" | "ready" | "error">(permitted ? "loading" : "ready");

  useEffect(() => {
    if (!permitted) return;
    const controller = new AbortController();
    setAuditState("loading");
    void fetch("/api/subscriber-workspace/events?after=0", {
      cache: "no-store",
      signal: controller.signal
    })
      .then(async (response) => {
        const body = await response.json().catch(() => null) as AuditApiResponse | null;
        if (!response.ok || !body || !Array.isArray(body.events)) {
          throw new Error("Audit ledger unavailable.");
        }
        const workspaceRecords = body.events
          .filter((event) => event.workspace_id === props.data.workspaceId)
          .map(auditRecord)
          .sort((left, right) => right.occurredAt.localeCompare(left.occurredAt));
        setRecords(workspaceRecords);
        setAuditState("ready");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setAuditState("error");
      });
    return () => controller.abort();
  }, [permitted, props.data.workspaceId]);

  if (!permitted) {
    return <AuthorityNotice critical>Audit access is restricted by a server-resolved capability.</AuthorityNotice>;
  }

  return (
    <>
      <Heading
        title="Audit"
        description="Tenant-scoped, append-only operational history."
        actions={<button className={styles.button} type="button" disabled>Create export unavailable</button>}
      />
      <AuthorityNotice>
        Audit export remains disabled until export rights, retention, content filtering and a persistent export receipt are implemented. The visible ledger is read-only.
      </AuthorityNotice>
      {auditState === "loading" ? <p className={styles.feedback} role="status">Loading the append-only workspace ledger…</p> : null}
      {auditState === "error" ? <p className={styles.feedback} role="alert">The audit ledger could not be loaded. No empty-state claim was substituted.</p> : null}
      {auditState === "ready" && records.length === 0 ? <p className={styles.feedback} role="status">No audit events are recorded for this workspace.</p> : null}
      {auditState === "ready" && records.length > 0 ? (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <caption>Audit events for this workspace revision</caption>
            <thead><tr><th scope="col">Time</th><th scope="col">Event</th><th scope="col">Actor</th><th scope="col">Detail</th><th scope="col">Outcome</th></tr></thead>
            <tbody>{records.map((record) => <tr key={record.id}>
              <td>{record.occurredAt}</td><td><strong>{record.event}</strong></td><td>{record.actor}</td><td>{record.detail}</td><td><Status value={record.outcome} tone={record.outcome === "denied" ? "critical" : "positive"} /></td>
            </tr>)}</tbody>
          </table>
        </div>
      ) : null}
    </>
  );
}
