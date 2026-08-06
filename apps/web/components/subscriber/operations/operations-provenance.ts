import type { TenderWorkspaceData } from "./types";

export function provenanceSafeOperationsData(data: TenderWorkspaceData): TenderWorkspaceData {
  if (data.fixtureMode === true) return data;

  const {
    metrics,
    commercial,
    documents: _documents,
    amendments: _amendments,
    team: _team,
    approvals: _approvals,
    readiness: _readiness,
    ...persisted
  } = data;

  return {
    ...persisted,
    procedure: "Procedure unavailable",
    summary: "Server-backed workspace records are available. Client-synthesised operational projections are withheld.",
    ...(metrics ? { metrics: metrics.filter((metric) => metric.label !== "Readiness") } : {}),
    documents: [],
    amendments: [],
    ...(commercial ? { commercial: commercial.filter((record) => record.id !== "axfx_com_003") } : {}),
    team: [],
    approvals: []
  };
}
