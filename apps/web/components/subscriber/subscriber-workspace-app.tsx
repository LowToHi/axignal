"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  IntelligenceWorkspace,
  type IntelligenceLens,
  type IntelligenceWorkspaceData
} from "./intelligence";
import {
  OperationsWorkspace,
  tenderSections,
  type ActionType as OperationsActionType,
  type MutationFeedback,
  type OperationsActionPayload,
  type TenderSection,
  type TenderWorkspaceData
} from "./operations";
import { GlobalDestination } from "./global-destinations";
import { PageState } from "./page-state";
import { ProductShell, type ShellIdentity, type ShellLocale, type ShellWorkspaceContext } from "./product-shell";
import { AxentHome } from "./axent-home";
import type {
  SubscriberWorkspaceActionRequest,
  SubscriberWorkspaceActionResult,
  SubscriberWorkspaceActionType,
  SubscriberWorkspaceBootstrap,
  SubscriberWorkspaceCapability,
  SubscriberWorkspaceRecord,
  SubscriberWorkspaceSurfaceState
} from "@/lib/subscriber-workspace-contract";

type AppProps = { serverIdentity: ShellIdentity | null };

const opportunityCoordinates = [
  [50.8503, 4.3517],
  [41.3874, 2.1686],
  [48.8566, 2.3522],
  [52.52, 13.405]
] as const;

function intelligenceData(bootstrap: SubscriberWorkspaceBootstrap | null, selectedOpportunityId: string | null): IntelligenceWorkspaceData {
  const opportunities = bootstrap?.route_data.opportunities ?? [];
  const selected = opportunities.find((item) => item.id === selectedOpportunityId) ?? opportunities[0];
  return {
    context: {
      geography: "European Union",
      universe: "Public Procurement",
      horizon: "12–24 months",
      selectedOpportunityId: selected?.id ?? null,
      asOf: bootstrap?.generated_at ?? null,
      coverageLabel: bootstrap ? `${opportunities.length} version-pinned candidate records` : "Coverage unavailable"
    },
    messages: [
      { id: "axfx_msg_001", actor: "subscriber", body: "Show public procurement opportunities aligned with our mobility data capability.", occurredAt: "2026-08-02T08:21:00Z" },
      { id: "axfx_msg_002", actor: "axignal", body: "I found four engineering-fixture candidates. I kept official facts, fit inference, contradictions and unknowns separate.", occurredAt: "2026-08-02T08:21:08Z", actionLabel: "Review interpretation" },
      { id: "axfx_msg_003", actor: "axignal", body: `${selected?.title ?? "The selected opportunity"} has the strongest current evidence coverage, but mandatory requirements remain blocked.`, occurredAt: "2026-08-02T08:22:00Z", actionLabel: "Open requirements" }
    ],
    opportunities: opportunities.map((item, index) => {
      const coordinate = opportunityCoordinates[index % opportunityCoordinates.length]!;
      return { id: item.id, name: item.title, level: item.fit === "high" ? "HIGH" : item.fit === "medium" ? "MEDIUM" : "REVIEW", expectedReturn: item.confidence === null ? null : `${Math.round(item.confidence * 100)}% evidence`, confidence: item.confidence, trend: [42,46,44,53,57,55,64,68,72], latitude: coordinate[0], longitude: coordinate[1] };
    }),
    claims: [
      { id: "axfx_claim_001", kind: "fact", statement: "The contracting authority published a 28 August 2026 deadline at 12:00 CEST.", sourceLabel: "TED notice · version 4", asOf: "2026-07-30", supportCount: 1, originalLanguage: "en", translationStatus: "original" },
      { id: "axfx_claim_002", kind: "inference", statement: "Northstar's governed data-platform references may cover the interoperability criterion.", sourceLabel: "AXIGNAL fit assessment · candidate", asOf: "2026-08-02", supportCount: 3, originalLanguage: "en", translationStatus: "original" },
      { id: "axfx_claim_003", kind: "contradiction", statement: "The current ISO 27001 certificate expires before the planned contract start date.", sourceLabel: "Tenant evidence library", asOf: "2026-08-01", supportCount: 2, originalLanguage: "en", translationStatus: "original" },
      { id: "axfx_claim_004", kind: "prediction", statement: "An amendment may require rework; this is a scenario, not an observed buyer decision.", sourceLabel: "AXIGNAL scenario · proposal only", asOf: "2026-08-02", supportCount: 2, originalLanguage: "en", translationStatus: "original" },
      { id: "axfx_claim_005", kind: "unknown", statement: "The authority has not disclosed whether equivalent cybersecurity certification will be accepted.", sourceLabel: null, asOf: null, supportCount: null, originalLanguage: "en", translationStatus: "unavailable" }
    ],
    graphEntities: [
      { id: "eu", label: "European Union", kind: "geography" },
      { id: "opportunity", label: selected?.title ?? "Selected opportunity", kind: "opportunity" },
      { id: "interoperability", label: "Interoperability", kind: "driver" },
      { id: "certification", label: "Certification expiry", kind: "risk" },
      { id: "ted", label: "TED notice v4", kind: "source" }
    ],
    graphRelationships: [
      { id: "rel_1", from: "ted", to: "opportunity", label: "publishes", epistemicStatus: "support" },
      { id: "rel_2", from: "opportunity", to: "interoperability", label: "requires", epistemicStatus: "support" },
      { id: "rel_3", from: "certification", to: "opportunity", label: "may block", epistemicStatus: "contradiction" },
      { id: "rel_4", from: "eu", to: "opportunity", label: "jurisdiction", epistemicStatus: "support" }
    ],
    timeline: [
      { id: "notice", label: "Notice published", date: "2026-06-18", status: "observed" },
      { id: "amendment", label: "Amendment 4", date: "2026-07-30", status: "observed" },
      { id: "today", label: "Current knowledge", date: "2026-08-02", status: "current" },
      { id: "deadline", label: "Submission deadline", date: "2026-08-28", status: "forecast" },
      { id: "award", label: "Award timing unknown", date: "2026-11-01", status: "unknown" }
    ],
    metrics: [
      { id: "opportunities", label: "Opportunities detected", value: String(opportunities.length), detail: "Version-pinned engineering fixture" },
      { id: "coverage", label: "Evidence coverage", value: "72%", detail: "2 blocking gaps" },
      { id: "confidence", label: "Assessment confidence", value: "68%", detail: "Candidate · not a recommendation" },
      { id: "signals", label: "Signals reviewed", value: "328", detail: "Across admitted and candidate sources" },
      { id: "sources", label: "Sources traced", value: "142", detail: "Rights state preserved" }
    ]
  };
}

function operationsData(record: SubscriberWorkspaceRecord, bootstrap: SubscriberWorkspaceBootstrap): TenderWorkspaceData {
  const opportunity = bootstrap.route_data.opportunities.find((item) => item.id === record.opportunity_id);
  const requirements = record.requirements.map((item) => ({
    id: item.id,
    code: item.id.replace("axfx_req_", "REQ-").toUpperCase(),
    title: item.title,
    category: item.category,
    status: item.status === "met" ? "satisfied" as const : item.status === "partial" ? "in_progress" as const : item.status === "blocked" ? "blocked" as const : item.status === "not_applicable" ? "not_applicable" as const : "unreviewed" as const,
    mandatory: item.blocking,
    ...(item.owner_id ? { owner: item.owner_id } : {}),
    evidenceCount: item.evidence_ids.length,
    sourceReference: item.source_reference,
    lastUpdatedAt: item.updated_at
  }));
  const blockingItems = record.requirements.filter((item) => item.blocking && !["met", "not_applicable"].includes(item.status)).map((item) => item.title);
  return {
    workspaceId: record.id,
    tenderId: opportunity?.id ?? record.opportunity_id,
    title: record.title.replace(/ bid$/i, ""),
    buyer: opportunity?.buyer ?? "Buyer unavailable",
    jurisdiction: opportunity?.jurisdiction ?? "Unknown jurisdiction",
    procedure: "Open procedure",
    ...(opportunity?.source_url ? { sourceUrl: opportunity.source_url } : {}),
    dueAt: record.deadline,
    updatedAt: bootstrap.generated_at,
    revision: bootstrap.tenant.revision,
    status: record.state === "qualifying" || record.state === "go_review" ? "qualifying" : record.state === "preparing" || record.state === "subscriber_approved" ? "preparing" : record.state === "submitted_confirmed" ? "submitted_confirmed" : record.state === "closed" ? "closed" : "pursuing",
    fixtureMode: bootstrap.fixture_boundary.active,
    summary: "Evidence-governed preparation workspace. Readiness excludes unknown and stale evidence.",
    metrics: [
      { label: "Readiness", value: blockingItems.length ? "68%" : "94%", detail: `${blockingItems.length} blocking items`, tone: blockingItems.length ? "warning" : "positive" },
      { label: "Requirements", value: String(record.requirements.length), detail: `${record.requirements.filter((item) => item.status === "met").length} satisfied` },
      { label: "Evidence", value: String(record.evidence.length), detail: `${record.evidence.filter((item) => item.status === "expired").length} expired` },
      { label: "Deadline", value: record.deadline.slice(0, 10), detail: "Source timezone preserved" }
    ],
    requirements,
    evidence: record.evidence.map((item) => ({ id: item.id, title: item.title, kind: item.evidence_type === "unknown" ? "unknown" as const : item.status === "expired" ? "contradiction" as const : "fact" as const, source: item.source_reference ?? "Subscriber-provided candidate", status: item.status, requirementIds: item.requirement_id ? [item.requirement_id] : [], freshness: item.updated_at })),
    documents: [
      { id: "axfx_doc_001", title: "Technical response", version: "0.8", owner: "Bid team", status: "draft", updatedAt: "2026-08-02 08:15" },
      { id: "axfx_doc_002", title: "ISO 27001 certificate", version: "2024", owner: "Security", status: "review", updatedAt: "2026-08-01 15:42" },
      { id: "axfx_doc_003", title: "Declaration of honour", version: "1.1", owner: "Legal", status: "approved", updatedAt: "2026-07-31 10:02" }
    ],
    workItems: record.tasks.map((item) => ({ id: item.id, title: item.title, ...(item.owner_id ? { owner: item.owner_id } : {}), ...(item.due_at ? { dueAt: item.due_at } : {}), status: item.status === "open" ? "todo" as const : item.status === "in_progress" ? "doing" as const : item.status, ...(item.status === "blocked" ? { dependency: "REQ-SEC-07" } : {}) })),
    clarifications: record.clarifications.map((item) => ({ id: item.id, question: item.question, author: item.created_by, ...(item.approved_by ? { approver: item.approved_by } : {}), status: item.state === "internal_review" ? "pending_approval" as const : item.state === "approved" ? "approved" as const : item.state === "handoff_opened" ? "handoff_opened" as const : item.state === "sent_confirmed" ? "sent_confirmed" as const : item.state === "answered" || item.state === "closed" ? "answered" as const : "draft" as const, deadline: record.deadline, ...(opportunity?.source_url ? { officialUrl: opportunity.source_url } : {}) })),
    amendments: record.amendments.map((item) => ({ id: item.id, title: item.title, publishedAt: item.observed_at, ...(item.acknowledged ? { acknowledgedAt: item.observed_at } : {}), affectedRequirements: item.acknowledged ? 0 : 7, impact: item.acknowledged ? "low" as const : "high" as const })),
    commercial: [
      { id: "axfx_com_001", label: "Candidate contract value", ...(record.commercial.candidate_value === null ? {} : { amount: `${record.commercial.currency} ${record.commercial.candidate_value.toLocaleString()}` }), status: record.commercial.candidate_value === null ? "unknown" : record.commercial.approved_by ? "approved" : "estimated", owner: "Finance" },
      { id: "axfx_com_002", label: "Target margin", ...(record.commercial.margin_percent === null ? {} : { amount: `${record.commercial.margin_percent}%` }), status: record.commercial.margin_percent === null ? "unknown" : record.commercial.approved_by ? "approved" : "estimated", owner: "Finance" },
      { id: "axfx_com_003", label: "Tax treatment", status: "not_applicable", owner: "Legal" }
    ],
    team: [{ id: record.owner_id, name: "Engineering Owner", role: "Owner", responsibility: "Pursuit authority", status: "active" }],
    approvals: [
      { id: "axfx_approval_commercial", subject: "Commercial baseline", status: record.commercial.approved_by ? "approved" : "pending", requestedFrom: "Finance approver", ...(record.commercial.approved_by ? { decidedBy: record.commercial.approved_by } : {}) },
      { id: "axfx_approval_submission", subject: "Submission package", status: record.submission.approved_by ? "approved" : "pending", requestedFrom: "Subscriber approver", ...(record.submission.approved_by ? { decidedBy: record.submission.approved_by } : {}) }
    ],
    audit: [],
    readiness: {
      score: blockingItems.length ? 68 : 94,
      blockingItems,
      packagePrepared: ["ready", "approved"].includes(record.submission.package_status),
      subscriberApproved: record.submission.package_status === "approved",
      handoffOpened: Boolean(record.submission.handoff_opened_at),
      externalSubmissionConfirmed: Boolean(record.submission.externally_confirmed_at)
    },
    outcome: {
      status: record.outcome.status === "awarded" ? "awarded" : record.outcome.status === "not_awarded" ? "not_selected" : record.outcome.status === "withdrawn" ? "cancelled" : record.outcome.status === "pending" ? "submitted" : "unknown",
      ...(record.outcome.observed_at ? { recordedAt: record.outcome.observed_at } : {}),
      ...(record.outcome.source_reference ? { note: record.outcome.source_reference } : {})
    }
  };
}

function operationToServer(actionType: OperationsActionType, payload: OperationsActionPayload, record: SubscriberWorkspaceRecord): { type: SubscriberWorkspaceActionType; payload: Record<string, unknown>; confirmed?: boolean } | null {
  const workspace_id = payload.workspaceId;
  const subject = payload.subjectId;
  const values = payload.payload ?? {};
  const confirmed = payload.confirmation?.acknowledged === true;
  switch (actionType) {
    case "workspace.qualify": return { type: "decision.record", payload: { workspace_id, decision: values.decision === "no_bid" ? "do_not_pursue" : "pursue", rationale: values.rationale } };
    case "requirement.update": return { type: "requirement.update", payload: { workspace_id, requirement_id: subject, status: values.status === "satisfied" ? "met" : values.status === "in_progress" ? "partial" : values.status } };
    case "evidence.attach": return { type: "evidence.attach", payload: { workspace_id, requirement_id: subject ?? record.requirements[0]?.id, title: "Subscriber evidence candidate", evidence_type: "subscriber_document", source_reference: null } };
    case "task.assign": return { type: "task.assign", payload: { workspace_id, task_id: subject, owner_id: String(values.owner ?? "current_user") } };
    case "clarification.draft": return { type: "clarification.draft", payload: { workspace_id, question: "Draft clarification — edit required", rationale: "Created from the clarification workspace" } };
    case "clarification.approve": return { type: "clarification.approve", payload: { workspace_id, clarification_id: subject } };
    case "clarification.open_handoff": return { type: "handoff.open", payload: { workspace_id, target_type: "clarification", clarification_id: subject } };
    case "clarification.confirm_sent": return { type: "external_action.confirm", payload: { workspace_id, target_type: "clarification", clarification_id: subject }, confirmed };
    case "amendment.acknowledge": return { type: "amendment.acknowledge", payload: { workspace_id, amendment_id: subject } };
    case "commercial.update": return { type: "commercial.update", payload: { workspace_id, candidate_value: record.commercial.candidate_value ?? 0, margin_percent: record.commercial.margin_percent ?? 0 } };
    case "commercial.approve": return { type: "commercial.approve", payload: { workspace_id }, confirmed };
    case "submission.prepare": return { type: "submission.prepare", payload: { workspace_id } };
    case "submission.approve": return { type: "submission.approve", payload: { workspace_id }, confirmed };
    case "submission.open_handoff": return { type: "handoff.open", payload: { workspace_id, target_type: "submission" } };
    case "submission.confirm_external": return { type: "external_action.confirm", payload: { workspace_id, target_type: "submission" }, confirmed };
    case "outcome.record": return { type: "outcome.record", payload: { workspace_id, status: values.status === "awarded" ? "awarded" : values.status === "not_selected" ? "not_awarded" : values.status === "cancelled" ? "withdrawn" : "pending", source_reference: values.note } };
    case "recovery.request": return { type: "recovery.request", payload: { workspace_id } };
    case "document.create":
    case "approval.record":
    case "export.create": return null;
  }
}

export function SubscriberWorkspaceApp({ serverIdentity }: AppProps) {
  const pathname = usePathname();
  const router = useRouter();
  const search = useSearchParams();
  const [bootstrap, setBootstrap] = useState<SubscriberWorkspaceBootstrap | null>(null);
  const [viewState, setViewState] = useState<SubscriberWorkspaceSurfaceState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [locale, setLocale] = useState<ShellLocale>("en");
  const [lens, setLens] = useState<IntelligenceLens>("GLOBE");
  const [selectedOpportunity, setSelectedOpportunity] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Partial<Record<OperationsActionType, MutationFeedback>>>({});

  const load = useCallback(async () => {
    setViewState("loading");
    setError(null);
    try {
      const response = await fetch("/api/subscriber-workspace/bootstrap", { cache: "no-store" });
      const body = await response.json();
      if (!response.ok) throw new Error(typeof body?.error === "string" ? body.error : "Subscriber workspace unavailable.");
      setBootstrap(body as SubscriberWorkspaceBootstrap);
      setViewState((body as SubscriberWorkspaceBootstrap).state);
      const cookiePreferences = Object.fromEntries(document.cookie.split(";").map((entry) => entry.trim().split("=").map(decodeURIComponent)));
      const savedLocale = cookiePreferences.axignal_locale ?? window.localStorage.getItem("axignal:subscriber:locale");
      const nextLocale = ["en", "es", "fr", "de", "pt", "it"].includes(savedLocale ?? "") ? savedLocale as ShellLocale : (body as SubscriberWorkspaceBootstrap).locale;
      const savedTheme = cookiePreferences.axignal_theme ?? window.localStorage.getItem("axignal:subscriber:theme");
      setLocale(nextLocale);
      const resolvedTheme = savedTheme === "light" || savedTheme === "dark" ? savedTheme : (body as SubscriberWorkspaceBootstrap).theme === "light" ? "light" : "dark";
      document.documentElement.dataset.theme = resolvedTheme;
      document.documentElement.style.colorScheme = resolvedTheme;
      setSelectedOpportunity((body as SubscriberWorkspaceBootstrap).route_data.opportunities[0]?.id ?? null);
    } catch (cause) {
      setViewState("source_unavailable");
      setError(cause instanceof Error ? cause.message : "Subscriber workspace unavailable.");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => { document.documentElement.lang = locale; }, [locale]);

  function changeTheme(nextTheme: "dark" | "light") {
    window.localStorage.setItem("axignal:subscriber:theme", nextTheme);
    document.cookie = `axignal_theme=${encodeURIComponent(nextTheme)}; Path=/; Max-Age=31536000; SameSite=Lax`;
    document.documentElement.dataset.theme = nextTheme;
    document.documentElement.style.colorScheme = nextTheme;
  }

  function changeLocale(nextLocale: ShellLocale) {
    window.localStorage.setItem("axignal:subscriber:locale", nextLocale);
    document.cookie = `axignal_locale=${encodeURIComponent(nextLocale)}; Path=/; Max-Age=31536000; SameSite=Lax`;
    setLocale(nextLocale);
  }

  const identity: ShellIdentity = bootstrap ? {
    name: bootstrap.identity.display_name,
    email: bootstrap.identity.email,
    organisation: bootstrap.tenant.name,
    roles: bootstrap.roles,
    entitlementLabel: `${bootstrap.entitlement.plan_code} · ${bootstrap.entitlement.status}`
  } : serverIdentity ?? { name: "Workspace unavailable", email: "", organisation: "AXIGNAL", roles: ["VIEWER"], entitlementLabel: "Context unavailable" };

  const postAction = useCallback(async (actionType: SubscriberWorkspaceActionType, payload: Record<string, unknown>, confirmed = false) => {
    if (!bootstrap) throw new Error("Workspace context is not loaded.");
    const request: SubscriberWorkspaceActionRequest = { action_id: `ax_action_${crypto.randomUUID().replaceAll("-", "")}`, action_type: actionType, tenant_revision: bootstrap.tenant.revision, payload, ...(confirmed ? { confirmation: { confirmed: true, authority: "subscriber" } } : {}) };
    const response = await fetch("/api/subscriber-workspace/actions", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(request) });
    const body = await response.json();
    if (!response.ok) {
      const message = typeof body?.error === "string" ? body.error : "Mutation was rejected.";
      const code = typeof body?.code === "string" ? body.code : null;
      throw new Error(code ? `${message} (${code})` : message);
    }
    const result = body as SubscriberWorkspaceActionResult;
    setBootstrap(result.bootstrap);
    setViewState(result.bootstrap.state);
    setError(null);
    return result;
  }, [bootstrap]);

  async function handleIntelligenceAction(actionType: "route.view" | "lens.change" | "opportunity.select", payload: Record<string, unknown>) {
    try {
      await postAction(actionType, payload);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The investigation action could not be persisted.");
      setViewState("partial");
    }
  }

  async function handleOperation(actionType: OperationsActionType, payload: OperationsActionPayload) {
    const record = bootstrap?.route_data.workspaces.find((item) => item.id === payload.workspaceId);
    if (!record) return;
    const mapped = operationToServer(actionType, payload, record);
    if (!mapped) {
      setFeedback((current) => ({ ...current, [actionType]: { state: "rejected", message: "This engineering revision exposes the route but the persistent mutation contract is not yet available." } }));
      return;
    }
    setFeedback((current) => ({ ...current, [actionType]: { state: "pending", message: "Persisting and reconciling with the server…" } }));
    try {
      const result = await postAction(mapped.type, mapped.payload, mapped.confirmed);
      if (actionType === "submission.prepare") await postAction("preflight.complete", { workspace_id: payload.workspaceId });
      setFeedback((current) => ({ ...current, [actionType]: { state: result.mutation_state === "persisted" ? "persisted" : result.mutation_state, message: "Persisted and reconciled with the server revision." } }));
    } catch (cause) {
      setFeedback((current) => ({ ...current, [actionType]: { state: "recovery_available", message: cause instanceof Error ? cause.message : "Mutation rejected; no success was recorded." } }));
    }
  }

  const capabilities = bootstrap?.capabilities ?? [];
  const fixtureMode = bootstrap?.fixture_boundary.active ?? false;
  let content: React.ReactNode;
  if (!bootstrap && viewState !== "loading") {
    content = <PageState state="source_unavailable" {...(error ? { detail: error } : {})} onRetry={() => void load()} />;
  } else if (!bootstrap) {
    content = <PageState state="loading" />;
  } else if (pathname === "/" || pathname === "/axent") {
    content = <AxentHome
      bootstrap={bootstrap}
      onOpenWorkspace={(workspaceId) => router.push(`/workspaces/${workspaceId}/overview`)}
      onHelp={() => router.push("/help")}
    />;
  } else if (pathname === "/investigations") {
    content = <IntelligenceWorkspace
      data={intelligenceData(bootstrap, selectedOpportunity)}
      state={viewState}
      lens={lens}
      fixtureMode={fixtureMode}
      {...(error ? { readOnlyReason: error } : {})}
      copy={{ expectedReturn: "Evidence fit", confidence: "Assessment confidence" }}
      onLensChange={(nextLens) => { setLens(nextLens); void handleIntelligenceAction("lens.change", { lens: nextLens.toLowerCase() }); }}
      onOpportunitySelect={(id) => { setSelectedOpportunity(id); void handleIntelligenceAction("opportunity.select", { opportunity_id: id }); }}
      onClaimSelect={(id) => router.push(`/investigations?claim=${encodeURIComponent(id)}`)}
      onTimelineSelect={(id) => router.push(`/investigations?as_of=${encodeURIComponent(id)}`)}
      onNavigatorSubmit={async (message) => { await handleIntelligenceAction("route.view", { route: `/investigations?command=${message.slice(0, 80)}` }); }}
      onRetry={() => void load()}
    />;
  } else {
    const match = pathname.match(/^\/workspaces\/([^/]+)\/([^/]+)$/);
    if (match && tenderSections.includes(match[2] as TenderSection)) {
      const record = bootstrap.route_data.workspaces.find((item) => item.id === match[1]);
      const selectedId = search.get("selected");
      content = <OperationsWorkspace
        section={match[2] as TenderSection}
        state={record ? viewState : "empty"}
        data={record ? operationsData(record, bootstrap) : null}
        capabilities={new Set(capabilities as SubscriberWorkspaceCapability[])}
        mutationFeedback={feedback}
        locale={locale}
        view={search.get("view") === "cards" ? "cards" : "table"}
        {...(selectedId ? { selectedId } : {})}
        onNavigate={(section, selectedId) => router.push(`/workspaces/${match[1]}/${section}${selectedId ? `?selected=${encodeURIComponent(selectedId)}` : ""}`)}
        onViewChange={(view) => router.push(`${pathname}?view=${view}`)}
        onRetry={() => void load()}
        onAction={handleOperation}
      />;
    } else {
      content = <GlobalDestination pathname={pathname} onThemeChange={changeTheme} bootstrap={bootstrap} />;
    }
  }

  const workspaceMatch = pathname.match(/^\/workspaces\/([^/]+)(?:\/|$)/);
  const activeRecord = workspaceMatch ? bootstrap?.route_data.workspaces.find((item) => item.id === workspaceMatch[1]) : undefined;
  const activeOpportunity = activeRecord ? bootstrap?.route_data.opportunities.find((item) => item.id === activeRecord.opportunity_id) : undefined;
  const workspaceContext: ShellWorkspaceContext | null = activeRecord ? {
    id: activeRecord.id,
    title: activeRecord.title,
    sourceLabel: activeOpportunity?.id ?? activeRecord.opportunity_id,
    deadlineLabel: new Date(activeRecord.deadline).toLocaleString(locale),
    readiness: activeRecord.requirements.length ? Math.round((activeRecord.requirements.filter((item) => item.status === "met").length / activeRecord.requirements.length) * 100) : 0,
    blockingRequirements: activeRecord.requirements.filter((item) => item.blocking && !["met", "not_applicable"].includes(item.status)).length
  } : null;

  return <ProductShell identity={identity} capabilities={capabilities} fixtureMode={fixtureMode} workspaceContext={workspaceContext} locale={locale} onLocaleChange={changeLocale}>{content}</ProductShell>;
}
