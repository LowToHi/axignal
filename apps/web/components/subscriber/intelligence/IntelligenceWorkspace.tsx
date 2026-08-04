"use client";

import { FormEvent, useCallback, useMemo, useRef, useState } from "react";

import { GraphSurface } from "./GraphSurface";
import { SemanticGlobe } from "./ReducedMotionSemanticGlobe";
import { Timeline } from "./Timeline";
import type { ClaimKind, IntelligenceLens, IntelligenceViewState, IntelligenceWorkspaceCopy, IntelligenceWorkspaceProps } from "./types";
import styles from "./intelligence-workspace.module.css";

const LENSES: readonly IntelligenceLens[] = ["AUTO", "GLOBE", "GRAPH", "DUAL"];
const CLAIM_FILTERS: readonly ("all" | ClaimKind)[] = ["all", "fact", "inference", "prediction", "contradiction", "unknown"];
const DEFAULT_COPY: IntelligenceWorkspaceCopy = {
  navigatorTitle: "AXIGNAL NAVIGATOR",
  online: "ONLINE",
  composerPlaceholder: "Write a command or question…",
  send: "Send",
  lensLabel: "Select intelligence lens",
  opportunitiesTitle: "OPPORTUNITIES",
  orderByPotential: "Order by: Potential",
  expectedReturn: "Expected return",
  confidence: "Confidence",
  claimsTitle: "CLAIM & EVIDENCE RAIL",
  allClaims: "All",
  fact: "Fact",
  inference: "Inference",
  prediction: "Prediction",
  contradiction: "Contradiction",
  unknown: "Unknown",
  view: "View",
  fixtureNotice: "ENGINEERING FIXTURE · NOT LIVE DATA",
  stateTitle: "This intelligence view is not available",
  retry: "Retry"
};

const BLOCKING_STATES = new Set<IntelligenceViewState>([
  "loading", "empty", "restricted", "source_unavailable", "recoverable_error", "terminal_error"
]);

const STATE_DETAILS: Record<IntelligenceViewState, string> = {
  loading: "Loading the server-resolved investigation context.",
  empty: "No opportunities match the current investigation context.",
  ready: "",
  partial: "Some sources are unavailable. Available evidence remains visible and explicitly bounded.",
  stale: "The current view is stale. Refresh before making a consequential decision.",
  restricted: "Your server-resolved capabilities do not grant access to this investigation.",
  read_only: "This investigation is read-only. Selection remains available; mutations are disabled.",
  source_unavailable: "The real data adapter is unavailable. Engineering fixtures were not loaded automatically.",
  recoverable_error: "The context could not be reconciled. Retry without losing your safe selection.",
  terminal_error: "The investigation cannot be rendered safely. Contact an administrator with the trace reference."
};

function confidenceDots(value: number | null) {
  if (value === null) return <span className={styles.unknownValue}>Unknown</span>;
  const filled = Math.round(Math.min(1, Math.max(0, value)) * 5);
  return <span className={styles.confidenceDots} aria-label={`${Math.round(value * 100)}%`}>
    {Array.from({ length: 5 }, (_, index) => <i key={index} data-filled={index < filled} />)}
  </span>;
}

function Sparkline({ values }: { values: readonly number[] }) {
  if (values.length < 2) return <span className={styles.noTrend}>No trend</span>;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1);
  return (
    <span className={styles.sparkline} aria-hidden="true">
      {values.map((value, index) => <i key={index} style={{ height: `${18 + ((value - min) / range) * 82}%` }} />)}
    </span>
  );
}

function PageState({ state, title, onRetry, retryLabel }: { state: IntelligenceViewState; title: string; onRetry: (() => void) | undefined; retryLabel: string }) {
  return (
    <section className={styles.pageState} role={state === "loading" ? "status" : "alert"} aria-busy={state === "loading"}>
      <span>{state.replaceAll("_", " ").toUpperCase()}</span>
      <h2>{title}</h2>
      <p>{STATE_DETAILS[state]}</p>
      {state === "recoverable_error" || state === "source_unavailable" ? <button type="button" onClick={onRetry} disabled={!onRetry}>{retryLabel}</button> : null}
    </section>
  );
}

export function IntelligenceWorkspace({
  data,
  state,
  lens,
  fixtureMode = false,
  readOnlyReason,
  copy: copyOverrides,
  className,
  onLensChange,
  onOpportunitySelect,
  onClaimSelect,
  onTimelineSelect,
  onNavigatorSubmit,
  onRetry
}: IntelligenceWorkspaceProps) {
  const copy = { ...DEFAULT_COPY, ...copyOverrides };
  const [claimFilter, setClaimFilter] = useState<"all" | ClaimKind>("all");
  const [draft, setDraft] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [selectedTimelineId, setSelectedTimelineId] = useState<string | null>(null);
  const selectedOpportunity = data.opportunities.find((item) => item.id === data.context.selectedOpportunityId) ?? data.opportunities[0];
  const visibleClaims = useMemo(() => claimFilter === "all" ? data.claims : data.claims.filter((claim) => claim.kind === claimFilter), [claimFilter, data.claims]);
  const effectiveLens = lens === "AUTO" ? "GLOBE" : lens;
  const opportunitySelectRef = useRef(onOpportunitySelect);
  opportunitySelectRef.current = onOpportunitySelect;
  const selectOpportunity = useCallback((id: string) => {
    opportunitySelectRef.current(id);
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || !onNavigatorSubmit || submitting || state === "read_only") return;
    setSubmitting(true);
    try {
      await onNavigatorSubmit(message);
      setDraft("");
    } finally {
      setSubmitting(false);
    }
  }

  if (BLOCKING_STATES.has(state)) {
    return <div className={`${styles.root} ${className ?? ""}`} data-view-state={state}><PageState state={state} title={copy.stateTitle} onRetry={onRetry} retryLabel={copy.retry} /></div>;
  }

  return (
    <section className={`${styles.root} ${className ?? ""}`} data-view-state={state} data-testid="intelligence-workspace">
      {fixtureMode ? <div className={styles.fixtureBanner} role="status">{copy.fixtureNotice}</div> : null}
      {state !== "ready" ? <div className={styles.stateBanner} role="status"><strong>{state.replaceAll("_", " ")}</strong><span>{readOnlyReason || STATE_DETAILS[state]}</span></div> : null}

      <div className={styles.lensBar}>
        <div className={styles.contextPath} aria-label="Investigation context">
          <strong>{data.context.geography}</strong><span>/</span><strong>{data.context.universe}</strong><span>/</span><strong>{data.context.horizon}</strong>
        </div>
        <nav className={styles.lensSwitcher} aria-label={copy.lensLabel}>
          {LENSES.map((item) => <button key={item} type="button" aria-pressed={lens === item} onClick={() => onLensChange(item)}>{item}</button>)}
        </nav>
      </div>

      <aside className={styles.navigator} aria-label={copy.navigatorTitle}>
        <header><strong>{copy.navigatorTitle}</strong><span><i />{submitting ? "PROCESSING" : copy.online}</span></header>
        <div className={styles.messageList} aria-live="polite">
          {data.messages.map((message) => (
            <article key={message.id} data-actor={message.actor}>
              <div><strong>{message.actor === "subscriber" ? "YOU" : "AXIGNAL"}</strong><time dateTime={message.occurredAt}>{new Date(message.occurredAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time></div>
              <p>{message.body}</p>
              {message.actionLabel ? <button type="button">{message.actionLabel}</button> : null}
            </article>
          ))}
        </div>
        <form className={styles.composer} onSubmit={submit}>
          <label className={styles.srOnly} htmlFor="axignal-navigator-command">{copy.composerPlaceholder}</label>
          <input id="axignal-navigator-command" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={copy.composerPlaceholder} disabled={submitting || state === "read_only" || !onNavigatorSubmit} />
          <button type="submit" disabled={!draft.trim() || submitting || state === "read_only" || !onNavigatorSubmit}>{copy.send}</button>
        </form>
      </aside>

      <section className={styles.primary} aria-label="Intelligence visualization and metrics">
        <div className={styles.canvasArea} data-lens={effectiveLens}>
          {effectiveLens === "GLOBE" ? <SemanticGlobe opportunities={data.opportunities} selectedOpportunityId={data.context.selectedOpportunityId} label={data.context.geography} onSelect={selectOpportunity} /> : null}
          {effectiveLens === "GRAPH" ? <GraphSurface entities={data.graphEntities} relationships={data.graphRelationships} selectedOpportunityId={data.context.selectedOpportunityId} /> : null}
          {effectiveLens === "DUAL" ? <div className={styles.dual}><SemanticGlobe opportunities={data.opportunities} selectedOpportunityId={data.context.selectedOpportunityId} label={data.context.geography} onSelect={selectOpportunity} /><GraphSurface entities={data.graphEntities} relationships={data.graphRelationships} selectedOpportunityId={data.context.selectedOpportunityId} /></div> : null}
        </div>
        <Timeline points={data.timeline} selectedId={selectedTimelineId} onSelect={(id) => { setSelectedTimelineId(id); onTimelineSelect?.(id); }} />
        <section className={styles.metrics} aria-label="Investigation metrics">
          {data.metrics.map((metric) => <article key={metric.id}><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.detail}</small>{metric.trend ? <Sparkline values={metric.trend} /> : null}</article>)}
        </section>
      </section>

      <aside className={styles.rightRail}>
        <section className={styles.opportunityRail} aria-label={copy.opportunitiesTitle}>
          <header><strong>{copy.opportunitiesTitle} ({data.opportunities.length})</strong><span>{copy.orderByPotential}</span></header>
          <div className={styles.opportunityList}>
            {data.opportunities.map((opportunity) => (
              <button type="button" key={opportunity.id} aria-current={opportunity.id === selectedOpportunity?.id ? "true" : undefined} onClick={() => onOpportunitySelect(opportunity.id)}>
                <span><strong>{opportunity.name}</strong><em>{opportunity.level}</em></span>
                <span><small>{copy.expectedReturn}</small><b>{opportunity.expectedReturn ?? copy.unknown}</b><Sparkline values={opportunity.trend} /></span>
                <span><small>{copy.confidence}</small>{confidenceDots(opportunity.confidence)}</span>
              </button>
            ))}
          </div>
        </section>
        <section className={styles.claimRail} aria-label={copy.claimsTitle}>
          <header><strong>{copy.claimsTitle}</strong><span>{data.context.coverageLabel}</span></header>
          <div className={styles.claimFilters} role="toolbar" aria-label="Filter claims by epistemic status">
            {CLAIM_FILTERS.map((filter) => <button key={filter} type="button" aria-pressed={claimFilter === filter} onClick={() => setClaimFilter(filter)}>{filter === "all" ? copy.allClaims : copy[filter]}</button>)}
          </div>
          <div className={styles.claimList}>
            {visibleClaims.map((claim) => (
              <article key={claim.id} data-kind={claim.kind}>
                <span>{copy[claim.kind]}</span><p>{claim.statement}</p>
                <small>{claim.sourceLabel ?? copy.unknown}{claim.asOf ? ` · ${claim.asOf}` : ""}{claim.translationStatus ? ` · ${claim.translationStatus.replaceAll("_", " ")}` : ""}</small>
                <button type="button" onClick={() => onClaimSelect?.(claim.id)} disabled={!onClaimSelect}>{copy.view}</button>
              </article>
            ))}
            {visibleClaims.length === 0 ? <p className={styles.emptyClaims}>No claims in this epistemic category.</p> : null}
          </div>
        </section>
      </aside>
    </section>
  );
}
