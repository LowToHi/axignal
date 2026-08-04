"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { IntelligenceWorkspace as BaseIntelligenceWorkspace } from "./IntelligenceWorkspace";
import type {
  IntelligenceWorkspaceData,
  IntelligenceWorkspaceProps
} from "./types";

const REAL_ADAPTER_BOUNDARY =
  "Live-adapter mode exposes only provenance-complete investigation projections. Fixture messages, claims, graph relationships, timeline points, metrics and synthetic coordinates are withheld.";

const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function provenanceSafeData(data: IntelligenceWorkspaceData): IntelligenceWorkspaceData {
  return {
    context: {
      ...data.context,
      selectedOpportunityId: null,
      coverageLabel: "Live adapter connected · provenance-complete investigation projection pending"
    },
    messages: [],
    opportunities: [],
    claims: [],
    graphEntities: [],
    graphRelationships: [],
    timeline: [],
    metrics: [
      {
        id: "projection-boundary",
        label: "Investigation projection",
        value: "WITHHELD",
        detail: "No synthetic investigation data is substituted for missing server-backed evidence."
      }
    ]
  };
}

function researchLocale(): "en" | "es" | "fr" | "de" | "pt-BR" {
  const locale = document.documentElement.lang;
  if (locale === "es" || locale === "fr" || locale === "de") return locale;
  if (locale === "pt") return "pt-BR";
  return "en";
}

/**
 * Prevents engineering-only intelligence projections from leaking into a real-adapter session.
 * In explicit fixture mode, Navigator still requires a persistent ResearchRun and never falls
 * back to synthetic execution.
 */
export function IntelligenceWorkspace(props: IntelligenceWorkspaceProps) {
  const router = useRouter();
  const [navigatorError, setNavigatorError] = useState<string | null>(null);
  const data = props.fixtureMode === true ? props.data : provenanceSafeData(props.data);
  const selectedOpportunityId = data.context.selectedOpportunityId;
  const effectiveState =
    props.fixtureMode === true
      ? props.state
      : props.state === "ready"
        ? "partial"
        : props.state;
  const effectiveReadOnlyReason =
    props.fixtureMode === true
      ? props.readOnlyReason
      : props.readOnlyReason ?? REAL_ADAPTER_BOUNDARY;
  const {
    readOnlyReason: _readOnlyReason,
    onNavigatorSubmit: _onNavigatorSubmit,
    ...baseProps
  } = props;

  async function submitPersistentResearch(message: string) {
    if (!selectedOpportunityId) {
      setNavigatorError(
        "Select a server-resolved opportunity before starting persistent research."
      );
      return;
    }
    setNavigatorError(null);
    const response = await fetch("/api/research/runs", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        question: message,
        locale: researchLocale(),
        includePrivateKnowledge: false,
        researchMode: "STRUCTURED_SOURCE_OBSERVATION",
        subscriberOpportunityId: selectedOpportunityId
      })
    });
    const body = (await response.json().catch(() => null)) as {
      research_run_id?: unknown;
      error?: unknown;
    } | null;
    if (!response.ok) {
      setNavigatorError(
        typeof body?.error === "string"
          ? body.error
          : "The persistent ResearchRun could not be created."
      );
      return;
    }
    const researchRunId =
      typeof body?.research_run_id === "string" ? body.research_run_id : "";
    if (!uuidPattern.test(researchRunId)) {
      setNavigatorError("The ResearchRun API returned an invalid identifier.");
      return;
    }
    await props.onNavigatorSubmit?.(
      `ResearchRun ${researchRunId} accepted for ${selectedOpportunityId}`
    );
    router.push(`/research-runs/${researchRunId}`);
  }

  return (
    <>
      {navigatorError ? (
        <div role="alert" data-testid="navigator-research-error">
          {navigatorError}
        </div>
      ) : null}
      <BaseIntelligenceWorkspace
        {...baseProps}
        data={data}
        state={effectiveState}
        {...(effectiveReadOnlyReason
          ? { readOnlyReason: effectiveReadOnlyReason }
          : {})}
        {...(selectedOpportunityId
          ? { onNavigatorSubmit: submitPersistentResearch }
          : {})}
      />
    </>
  );
}
