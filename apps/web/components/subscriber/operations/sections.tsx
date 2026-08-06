"use client";

import { useState, type ReactNode } from "react";

import styles from "./operations.module.css";
import type {
  ActionType,
  Capability,
  MutationFeedback as MutationFeedbackValue,
  TenderOperationAction,
  TenderOperationsWorkspaceProps,
  TenderWorkspaceData
} from "./types";

type SectionProps = Pick<
  TenderOperationsWorkspaceProps,
  "capabilities" | "mutationFeedback" | "onAction" | "onNavigate" | "onViewChange" | "selectedId" | "state" | "view"
> & { data: TenderWorkspaceData };

function can(capabilities: ReadonlySet<Capability>, capability: Capability): boolean {
  return capabilities.has(capability);
}

function feedbackFor(
  feedback: TenderOperationsWorkspaceProps["mutationFeedback"],
  actionType: ActionType
): MutationFeedbackValue {
  return feedback?.[actionType] ?? { state: "idle" };
}

function isPending(feedback: TenderOperationsWorkspaceProps["mutationFeedback"], actionType: ActionType): boolean {
  return feedbackFor(feedback, actionType).state === "pending";
}

function routeMutationDisabled(props: SectionProps): boolean {
  return props.state === "read_only" || props.state === "stale";
}

function canMutate(props: SectionProps, capability: Capability): boolean {
  return !routeMutationDisabled(props) && can(props.capabilities, capability);
}

function ActionFeedback({ value }: { value: MutationFeedbackValue }) {
  if (value.state === "idle") return null;
  const failed = ["partial_failure", "rejected", "recovery_available"].includes(value.state);
  const defaults: Record<MutationFeedbackValue["state"], string> = {
    idle: "",
    pending: "Saving through the tenant-scoped service…",
    persisted: "Saved and reconciled with the server revision.",
    partial_failure: "Some changes were not persisted. Review before retrying.",
    rejected: "The server rejected this action.",
    recovery_available: "Recovery is available. No external action was taken."
  };
  return (
    <p className={styles.feedback} data-state={value.state} role={failed ? "alert" : "status"} aria-live="polite">
      {value.message ?? defaults[value.state]}
    </p>
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

function Heading({ title, description, actions }: { title: string; description: string; actions?: ReactNode }) {
  return (
    <header className={styles.sectionHeading}>
      <div><h2>{title}</h2><p>{description}</p></div>
      {actions ? <div className={styles.toolbar}>{actions}</div> : null}
    </header>
  );
}

function Status({ value, tone = "neutral" }: { value: string; tone?: "neutral" | "positive" | "warning" | "critical" }) {
  return <span className={styles.status} data-tone={tone}>{value.replaceAll("_", " ")}</span>;
}

function dispatch(
  props: SectionProps,
  actionType: ActionType,
  subjectId?: string,
  payload?: TenderOperationAction["payload"],
  confirmation?: TenderOperationAction["confirmation"]
) {
  const action: TenderOperationAction = { actionType, workspaceId: props.data.workspaceId };
  if (subjectId !== undefined) action.subjectId = subjectId;
  if (payload !== undefined) action.payload = payload;
  if (confirmation !== undefined) action.confirmation = confirmation;
  void props.onAction(action);
}

export function OverviewSection(props: SectionProps) {
  const { data } = props;
  const metrics = data.metrics ?? [
    { label: "Requirements", value: String(data.requirements?.length ?? 0), detail: "Structured obligations" },
    { label: "Evidence", value: String(data.evidence?.length ?? 0), detail: "Linked evidence records" },
    { label: "Open work", value: String(data.workItems?.filter((item) => item.status !== "done").length ?? 0), detail: "Tasks not completed" },
    { label: "Readiness", value: `${data.readiness?.score ?? 0}%`, detail: "Not a submission state" }
  ];
  return (
    <>
      <Heading title="Workspace overview" description="Current tender position, deadlines and governed next actions." />
      <AuthorityNotice>AXIGNAL organises research and preparation. Pursuit, signature and submission decisions remain with authorised subscribers.</AuthorityNotice>
      <div className={styles.grid}>
        {metrics.map((metric) => (
          <article className={styles.card} key={metric.label}>
            <span className={styles.label}>{metric.label}</span>
            <strong className={styles.metricValue}>{metric.value}</strong>
            <span className={styles.metricDetail}>{metric.detail}</span>
          </article>
        ))}
        <article className={`${styles.card} ${styles.cardWide}`}>
          <h3>Opportunity context</h3>
          <p>{data.summary ?? "No approved summary is available. Review the original notice and admitted evidence before making a decision."}</p>
        </article>
        <article className={styles.card}>
          <h3>Official source</h3>
          <p>{data.sourceUrl ? "An official-source link is available. Opening it is not a submission." : "No official-source adapter is available for this record."}</p>
        </article>
      </div>
    </>
  );
}

export function QualificationSection(props: SectionProps) {
  const [decision, setDecision] = useState("review");
  const action = "workspace.qualify" as const;
  const permitted = canMutate(props, "workspace:qualify");
  return (
    <>
      <Heading title="Qualification" description="Record an explicit, reversible pursue decision with rationale." />
      <AuthorityNotice critical>An AI signal or high opportunity score does not authorise a bid/no-bid decision. An authorised person must record it.</AuthorityNotice>
      <div className={styles.grid}>
        <article className={`${styles.card} ${styles.cardWide}`}>
          <h3>Decision record</h3>
          <div className={styles.formRow}>
            <label className={styles.field}>Decision
              <select value={decision} onChange={(event) => setDecision(event.target.value)} disabled={!permitted || isPending(props.mutationFeedback, action)}>
                <option value="review">Continue review</option><option value="pursue">Pursue</option><option value="no_bid">Do not pursue</option>
              </select>
            </label>
            <label className={styles.field}>Rationale
              <input id="qualification-rationale" placeholder="Required decision rationale" disabled={!permitted || isPending(props.mutationFeedback, action)} />
            </label>
          </div>
          <button className={styles.primary} data-testid="qualification-decision-submit" type="button" disabled={!permitted || isPending(props.mutationFeedback, action)} onClick={() => {
            const rationale = (document.getElementById("qualification-rationale") as HTMLInputElement | null)?.value ?? "";
            dispatch(props, action, undefined, { decision, rationale });
          }}>{isPending(props.mutationFeedback, action) ? "Recording…" : "Record qualification decision"}</button>
          {!permitted ? <p className={styles.feedback} role="status">You can review this section, but your server-resolved capabilities do not permit qualification.</p> : null}
          <ActionFeedback value={feedbackFor(props.mutationFeedback, action)} />
        </article>
        <article className={styles.card}><h3>Known blockers</h3><p>{props.data.readiness?.blockingItems.length ?? 0} current blockers. Unknowns remain explicit and are not treated as zero.</p></article>
      </div>
    </>
  );
}

export function RequirementsSection(props: SectionProps) {
  const records = props.data.requirements ?? [];
  const view = props.view ?? "table";
  const action = "requirement.update" as const;
  const permitted = canMutate(props, "requirement:edit");
  const controls = <><button className={styles.button} type="button" aria-pressed={view === "table"} onClick={() => props.onViewChange?.("table")}>Table</button><button className={styles.button} type="button" aria-pressed={view === "cards"} onClick={() => props.onViewChange?.("cards")}>Cards</button></>;
  return (
    <>
      <Heading title="Requirements" description="Trace every obligation to source, owner and evidence." actions={controls} />
      {view === "table" ? (
        <div className={styles.tableWrap} data-testid="requirements-table">
          <table className={styles.table}>
            <caption>{records.length} requirements. Mandatory status, ownership and evidence are available without visual encoding.</caption>
            <thead><tr><th scope="col">Requirement</th><th scope="col">Category</th><th scope="col">Status</th><th scope="col">Owner / due</th><th scope="col">Evidence</th><th scope="col">Action</th></tr></thead>
            <tbody>{records.map((record) => <tr key={record.id}>
              <td><strong>{record.code} · {record.title}</strong><span className={styles.subtle}>{record.mandatory ? "Mandatory" : "Optional"} · {record.sourceReference ?? "Source reference unknown"}</span></td>
              <td>{record.category}</td><td><Status value={record.status} tone={record.status === "blocked" ? "critical" : record.status === "satisfied" ? "positive" : "neutral"} /></td>
              <td>{record.owner ?? "Unassigned"}<span className={styles.subtle}>{record.dueAt ?? "No due date"}</span></td><td>{record.evidenceCount}</td>
              <td><button type="button" data-testid={`requirement-status-${record.id}`} className={`${styles.button} ${styles.rowAction}`} disabled={!permitted || isPending(props.mutationFeedback, action)} onClick={() => dispatch(props, action, record.id, { status: record.status === "satisfied" ? "in_progress" : "satisfied" })}>{record.status === "satisfied" ? "Reopen" : "Satisfy"}</button></td>
            </tr>)}</tbody>
          </table>
        </div>
      ) : <div className={styles.grid}>{records.map((record) => <article className={styles.card} key={record.id}><Status value={record.status} /><h3>{record.code} · {record.title}</h3><p>{record.category} · {record.mandatory ? "Mandatory" : "Optional"}<br />Owner: {record.owner ?? "Unassigned"}<br />Evidence: {record.evidenceCount}</p><button type="button" className={styles.button} disabled={!permitted || isPending(props.mutationFeedback, action)} onClick={() => dispatch(props, action, record.id, { status: "satisfied" })}>Update requirement</button></article>)}</div>}
      {!permitted ? <p className={styles.feedback}>Read-only: requirement edits are not included in your server-resolved capabilities.</p> : null}
      <ActionFeedback value={feedbackFor(props.mutationFeedback, action)} />
    </>
  );
}

export function EvidenceSection(props: SectionProps) {
  const records = props.data.evidence ?? [];
  const action = "evidence.attach" as const;
  const permitted = canMutate(props, "evidence:attach");
  return <><Heading title="Evidence" description="Candidate and admitted evidence, with provenance and freshness preserved." actions={<button className={styles.primary} type="button" disabled={!permitted || isPending(props.mutationFeedback, action)} onClick={() => dispatch(props, action, undefined, { source: "user_selected", status: "candidate" })}>Attach evidence</button>} />
    <AuthorityNotice>Attaching a file creates candidate evidence. It does not admit a claim, prove a requirement or replace source validation.</AuthorityNotice>
    <div className={styles.list}>{records.map((record) => <article className={styles.listItem} key={record.id}><div><h3>{record.title}</h3><p>{record.source} · {record.freshness ?? "Freshness unknown"} · linked to {record.requirementIds.length} requirements</p></div><div className={styles.toolbar}><Status value={record.kind} tone={record.kind === "contradiction" ? "critical" : record.kind === "unknown" ? "warning" : "neutral"} /><Status value={record.status} tone={record.status === "verified" ? "positive" : record.status === "expired" ? "warning" : "neutral"} /></div></article>)}</div>
    <ActionFeedback value={feedbackFor(props.mutationFeedback, action)} /></>;
}

export function DocumentsSection(props: SectionProps) {
  const action = "document.create" as const;
  const permitted = canMutate(props, "document:manage");
  return <><Heading title="Documents" description="Versioned bid artefacts with explicit review and ownership." actions={<button className={styles.primary} type="button" disabled={!permitted || isPending(props.mutationFeedback, action)} onClick={() => dispatch(props, action, undefined, { template: "blank" })}>Create draft</button>} />
    <AuthorityNotice>AXIGNAL stores preparation state only. Document approval does not sign, transmit or submit any artefact.</AuthorityNotice>
    <div className={styles.tableWrap}><table className={styles.table}><caption>Versioned workspace documents</caption><thead><tr><th scope="col">Document</th><th scope="col">Version</th><th scope="col">Owner</th><th scope="col">Status</th><th scope="col">Updated</th></tr></thead><tbody>{(props.data.documents ?? []).map((record) => <tr key={record.id}><td><strong>{record.title}</strong>{record.lockOwner ? <span className={styles.subtle}>Editing lock: {record.lockOwner}</span> : null}</td><td>{record.version}</td><td>{record.owner}</td><td><Status value={record.status} tone={record.status === "approved" ? "positive" : "neutral"} /></td><td>{record.updatedAt}</td></tr>)}</tbody></table></div>
    <ActionFeedback value={feedbackFor(props.mutationFeedback, action)} /></>;
}

export function WorkplanSection(props: SectionProps) {
  const action = "task.assign" as const;
  const permitted = canMutate(props, "work:assign");
  return <><Heading title="Workplan" description="Owners, dependencies and deadlines for bid preparation." />
    <div className={styles.grid}>{(["todo", "doing", "blocked", "done"] as const).map((status) => <section className={styles.card} key={status}><h3>{status.replaceAll("_", " ").toUpperCase()}</h3><div className={styles.list}>{(props.data.workItems ?? []).filter((item) => item.status === status).map((item) => <article key={item.id}><strong>{item.title}</strong><p>{item.owner ?? "Unassigned"} · {item.dueAt ?? "No due date"}{item.dependency ? ` · depends on ${item.dependency}` : ""}</p><button type="button" className={styles.button} disabled={!permitted || isPending(props.mutationFeedback, action)} onClick={() => dispatch(props, action, item.id, { owner: item.owner ?? "current_user" })}>Assign</button></article>)}</div></section>)}</div>
    <ActionFeedback value={feedbackFor(props.mutationFeedback, action)} /></>;
}

export function ClarificationsSection(props: SectionProps) {
  const draftAction = "clarification.draft" as const;
  const records = props.data.clarifications ?? [];
  return <><Heading title="Clarifications" description="Draft, approve and hand off questions through separated human authority." actions={<button type="button" className={styles.primary} disabled={!canMutate(props, "clarification:draft") || isPending(props.mutationFeedback, draftAction)} onClick={() => dispatch(props, draftAction, undefined, { body: "" })}>New draft</button>} />
    <AuthorityNotice critical>Drafting is not approval. Approval is not sending. Opening the official channel is not sending. A subscriber must separately confirm any external handoff.</AuthorityNotice>
    <div className={styles.list}>{records.map((record) => {
      const approve = "clarification.approve" as const;
      const open = "clarification.open_handoff" as const;
      const confirm = "clarification.confirm_sent" as const;
      return <article className={styles.listItem} key={record.id}><div><h3>{record.question}</h3><p>Author: {record.author} · approver: {record.approver ?? "Unassigned"} · deadline: {record.deadline ?? "Unknown"}</p><Status value={record.status} /></div><div className={styles.toolbar}>
        {record.status === "pending_approval" ? <button className={styles.button} data-testid={`clarification-approve-${record.id}`} type="button" disabled={!canMutate(props, "clarification:approve") || isPending(props.mutationFeedback, approve)} onClick={() => dispatch(props, approve, record.id, { separation_confirmed: true })}>Approve</button> : null}
        {record.status === "approved" ? <button className={styles.button} data-testid={`clarification-handoff-${record.id}`} type="button" disabled={routeMutationDisabled(props) || !record.officialUrl || isPending(props.mutationFeedback, open)} onClick={() => dispatch(props, open, record.id, { official_url: record.officialUrl ?? null })}>Open official channel</button> : null}
        {record.status === "handoff_opened" ? <button className={styles.danger} data-testid={`clarification-confirm-${record.id}`} type="button" disabled={!canMutate(props, "clarification:confirm_sent") || isPending(props.mutationFeedback, confirm)} onClick={() => dispatch(props, confirm, record.id, { sent_by_subscriber: true }, { acknowledged: true, authorityStatement: "I confirm that an authorised subscriber sent this clarification externally." })}>Confirm externally sent</button> : null}
      </div></article>;
    })}</div>
    {([draftAction, "clarification.approve", "clarification.open_handoff", "clarification.confirm_sent"] as const).map((action) => <ActionFeedback key={action} value={feedbackFor(props.mutationFeedback, action)} />)}</>;
}

export function ChangesSection(props: SectionProps) {
  const action = "amendment.acknowledge" as const;
  const permitted = canMutate(props, "workspace:edit");
  return <><Heading title="Changes" description="Buyer amendments and their effect on validated workspace state." />
    <AuthorityNotice>Acknowledging an amendment records review only. Affected requirements and readiness must be revalidated.</AuthorityNotice>
    <div className={styles.list}>{(props.data.amendments ?? []).map((record) => <article className={styles.listItem} key={record.id}><div><h3>{record.title}</h3><p>Published {record.publishedAt} · {record.affectedRequirements} requirements affected</p><Status value={`${record.impact} impact`} tone={record.impact === "high" ? "critical" : record.impact === "medium" ? "warning" : "neutral"} /></div><button className={styles.button} data-testid={`amendment-acknowledge-${record.id}`} type="button" disabled={!permitted || Boolean(record.acknowledgedAt) || isPending(props.mutationFeedback, action)} onClick={() => dispatch(props, action, record.id, { revalidation_required: true })}>{record.acknowledgedAt ? "Acknowledged" : "Acknowledge & revalidate"}</button></article>)}</div>
    <ActionFeedback value={feedbackFor(props.mutationFeedback, action)} /></>;
}

export function CommercialSection(props: SectionProps) {
  const update = "commercial.update" as const;
  const approve = "commercial.approve" as const;
  const viewPermitted = can(props.capabilities, "commercial:view");
  if (!viewPermitted) return <AuthorityNotice critical>Commercial values are restricted by server-resolved capability. No amount metadata is exposed.</AuthorityNotice>;
  return <><Heading title="Commercial" description="Cost and pricing assumptions with explicit unknown, redacted and approval states." />
    <AuthorityNotice>Estimated values are not approved commercial commitments. Approval requires a server-authorised finance role.</AuthorityNotice>
    <div className={styles.tableWrap}><table className={styles.table}><caption>Commercial lines; unknown, zero, not applicable and redacted remain distinct.</caption><thead><tr><th scope="col">Line</th><th scope="col">Amount</th><th scope="col">Owner</th><th scope="col">Status</th><th scope="col">Action</th></tr></thead><tbody>{(props.data.commercial ?? []).map((record) => <tr key={record.id}><td><strong>{record.label}</strong></td><td>{record.amount ?? record.status.replaceAll("_", " ")}</td><td>{record.owner ?? "Unassigned"}</td><td><Status value={record.status} /></td><td><button className={styles.button} type="button" disabled={!canMutate(props, "commercial:edit") || isPending(props.mutationFeedback, update)} onClick={() => dispatch(props, update, record.id, { status: "reviewed" })}>Mark reviewed</button></td></tr>)}</tbody></table></div>
    <button className={styles.primary} type="button" disabled={!canMutate(props, "commercial:approve") || isPending(props.mutationFeedback, approve)} onClick={() => dispatch(props, approve, undefined, { scope: "workspace_commercial" }, { acknowledged: true, authorityStatement: "I am authorised to approve this commercial baseline." })}>Approve commercial baseline</button>
    <ActionFeedback value={feedbackFor(props.mutationFeedback, update)} /><ActionFeedback value={feedbackFor(props.mutationFeedback, approve)} /></>;
}

export function TeamSection(props: SectionProps) {
  const action = "approval.record" as const;
  return <><Heading title="Team & approvals" description="Workspace responsibility and separated approval state." />
    <div className={styles.grid}><section className={`${styles.card} ${styles.cardWide}`}><h3>Workspace team</h3><div className={styles.list}>{(props.data.team ?? []).map((member) => <article className={styles.listItem} key={member.id}><div><h3>{member.name}</h3><p>{member.role} · {member.responsibility}</p></div><Status value={member.status} tone={member.status === "active" ? "positive" : "warning"} /></article>)}</div></section>
      <section className={styles.card}><h3>Approvals</h3><div className={styles.list}>{(props.data.approvals ?? []).map((approval) => <article key={approval.id}><strong>{approval.subject}</strong><p>Requested from {approval.requestedFrom}</p><Status value={approval.status} tone={approval.status === "approved" ? "positive" : approval.status === "rejected" ? "critical" : "warning"} />{approval.status === "pending" ? <button className={styles.button} type="button" disabled={routeMutationDisabled(props) || isPending(props.mutationFeedback, action)} onClick={() => dispatch(props, action, approval.id, { decision: "approved" }, { acknowledged: true, authorityStatement: "I am authorised to record this approval." })}>Record approval</button> : null}</article>)}</div></section></div>
    <ActionFeedback value={feedbackFor(props.mutationFeedback, action)} /></>;
}

export function SubmissionSection(props: SectionProps) {
  const readiness = props.data.readiness ?? { score: 0, blockingItems: ["Readiness unavailable"], packagePrepared: false, subscriberApproved: false, handoffOpened: false, externalSubmissionConfirmed: false };
  const prepare = "submission.prepare" as const;
  const approve = "submission.approve" as const;
  const open = "submission.open_handoff" as const;
  const confirm = "submission.confirm_external" as const;
  return <><Heading title="Submission" description="Readiness preflight and controlled handoff to the buyer's official channel." />
    <AuthorityNotice critical>AXIGNAL cannot sign or submit. Ready is not submitted; opening the official portal is not submission; subscriber confirmation records an external act but cannot prove buyer acceptance.</AuthorityNotice>
    <div className={styles.grid}>
      <article className={`${styles.card} ${styles.cardWide}`}><span className={styles.label}>Readiness preflight</span><strong className={styles.metricValue}>{readiness.score}%</strong><div className={styles.progress} aria-label={`Readiness ${readiness.score} percent`}><span style={{ width: `${Math.max(0, Math.min(100, readiness.score))}%` }} /></div><ul className={styles.checklist}>{readiness.blockingItems.length ? readiness.blockingItems.map((item) => <li key={item}>{item}</li>) : <li>No known blockers. This is not a submission status.</li>}</ul></article>
      <article className={styles.card}><h3>Governed sequence</h3><ol className={styles.checklist}><li>Prepare package</li><li>Subscriber approval</li><li>Open official portal</li><li>Subscriber confirms external action</li></ol></article>
      <article className={styles.card}><h3>1 · Package</h3><Status value={readiness.packagePrepared ? "prepared" : "not prepared"} tone={readiness.packagePrepared ? "positive" : "warning"} /><button className={styles.button} data-testid="submission-prepare" type="button" disabled={!canMutate(props, "submission:prepare") || readiness.blockingItems.length > 0 || isPending(props.mutationFeedback, prepare)} onClick={() => dispatch(props, prepare)}>Prepare package</button><ActionFeedback value={feedbackFor(props.mutationFeedback, prepare)} /></article>
      <article className={styles.card}><h3>2 · Approval</h3><Status value={readiness.subscriberApproved ? "approved" : "not approved"} tone={readiness.subscriberApproved ? "positive" : "warning"} /><button className={styles.button} data-testid="submission-approve" type="button" disabled={!canMutate(props, "submission:approve") || !readiness.packagePrepared || isPending(props.mutationFeedback, approve)} onClick={() => dispatch(props, approve, undefined, undefined, { acknowledged: true, authorityStatement: "I am authorised to approve this prepared package for external handoff." })}>Approve package</button><ActionFeedback value={feedbackFor(props.mutationFeedback, approve)} /></article>
      <article className={styles.card}><h3>3 · Official handoff</h3><Status value={readiness.handoffOpened ? "portal opened" : "not opened"} /><button className={styles.button} data-testid="submission-open-handoff" type="button" disabled={routeMutationDisabled(props) || !readiness.subscriberApproved || !props.data.sourceUrl || isPending(props.mutationFeedback, open)} onClick={() => dispatch(props, open, undefined, { official_url: props.data.sourceUrl ?? null })}>Open official portal</button><ActionFeedback value={feedbackFor(props.mutationFeedback, open)} /></article>
      <article className={styles.card}><h3>4 · External confirmation</h3><Status value={readiness.externalSubmissionConfirmed ? "subscriber confirmed" : "unconfirmed"} tone={readiness.externalSubmissionConfirmed ? "positive" : "warning"} /><button className={styles.danger} data-testid="submission-confirm-external" type="button" disabled={!canMutate(props, "submission:confirm_external") || !readiness.handoffOpened || isPending(props.mutationFeedback, confirm)} onClick={() => dispatch(props, confirm, undefined, { submitted_by_subscriber: true }, { acknowledged: true, authorityStatement: "I confirm an authorised subscriber completed the external submission. This does not assert buyer acceptance." })}>Confirm external submission</button><ActionFeedback value={feedbackFor(props.mutationFeedback, confirm)} /></article>
    </div></>;
}

export function OutcomeSection(props: SectionProps) {
  const [status, setStatus] = useState(props.data.outcome?.status ?? "unknown");
  const action = "outcome.record" as const;
  const permitted = canMutate(props, "outcome:record");
  return <><Heading title="Outcome & learning" description="Observed procurement outcome, separated from prediction and signed-contract status." />
    <AuthorityNotice>An award notice is not a signed contract. Record only observed outcomes and preserve the source and uncertainty.</AuthorityNotice>
    <div className={styles.grid}><article className={`${styles.card} ${styles.cardWide}`}><h3>Observed outcome</h3><div className={styles.formRow}><label className={styles.field}>Status<select value={status} onChange={(event) => setStatus(event.target.value as typeof status)} disabled={!permitted}><option value="unknown">Unknown</option><option value="submitted">Submitted</option><option value="shortlisted">Shortlisted</option><option value="not_selected">Not selected</option><option value="awarded">Award notice observed</option><option value="cancelled">Cancelled</option></select></label><label className={styles.field}>Source note<input id="outcome-note" placeholder="Observed source and limitations" disabled={!permitted} /></label></div><button className={styles.primary} type="button" disabled={!permitted || isPending(props.mutationFeedback, action)} onClick={() => dispatch(props, action, undefined, { status, note: (document.getElementById("outcome-note") as HTMLInputElement | null)?.value ?? "" })}>Record observed outcome</button><ActionFeedback value={feedbackFor(props.mutationFeedback, action)} /></article><article className={styles.card}><h3>Current record</h3><Status value={props.data.outcome?.status ?? "unknown"} /><p>{props.data.outcome?.note ?? "No observed outcome has been recorded."}</p></article></div></>;
}

export function AuditSection(props: SectionProps) {
  if (!can(props.capabilities, "audit:view")) return <AuthorityNotice critical>Audit access is restricted by a server-resolved capability.</AuthorityNotice>;
  const action = "export.create" as const;
  return <><Heading title="Audit" description="Tenant-scoped, append-only operational history." actions={<button className={styles.button} type="button" disabled={!canMutate(props, "export:create") || isPending(props.mutationFeedback, action)} onClick={() => dispatch(props, action, undefined, { format: "csv", scope: "workspace_audit" })}>Create export</button>} />
    <div className={styles.tableWrap}><table className={styles.table}><caption>Audit events for this workspace revision</caption><thead><tr><th scope="col">Time</th><th scope="col">Event</th><th scope="col">Actor</th><th scope="col">Detail</th><th scope="col">Outcome</th></tr></thead><tbody>{(props.data.audit ?? []).map((record) => <tr key={record.id}><td>{record.occurredAt}</td><td><strong>{record.event}</strong></td><td>{record.actor}</td><td>{record.detail}</td><td><Status value={record.outcome} tone={record.outcome === "denied" ? "critical" : "positive"} /></td></tr>)}</tbody></table></div>
    <ActionFeedback value={feedbackFor(props.mutationFeedback, action)} /></>;
}
