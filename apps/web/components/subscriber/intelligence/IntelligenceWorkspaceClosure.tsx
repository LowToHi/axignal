"use client";

import { IntelligenceWorkspace as BaseIntelligenceWorkspace } from "./IntelligenceWorkspace";
import type {
  IntelligenceWorkspaceData,
  IntelligenceWorkspaceProps
} from "./types";

const REAL_ADAPTER_BOUNDARY =
  "Live-adapter mode exposes only provenance-complete investigation projections. Fixture messages, claims, graph relationships, timeline points, metrics and synthetic coordinates are withheld.";

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

/**
 * Prevents engineering-only intelligence projections from leaking into a real-adapter session.
 * The fixture path remains fully disclosed by the existing engineering banner.
 */
export function IntelligenceWorkspace(props: IntelligenceWorkspaceProps) {
  if (props.fixtureMode === true) {
    return <BaseIntelligenceWorkspace {...props} />;
  }

  return (
    <BaseIntelligenceWorkspace
      {...props}
      data={provenanceSafeData(props.data)}
      state={props.state === "ready" ? "partial" : props.state}
      readOnlyReason={props.readOnlyReason ?? REAL_ADAPTER_BOUNDARY}
    />
  );
}
