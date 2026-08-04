import assert from "node:assert/strict";
import test from "node:test";

import { provenanceSafeOperationsData } from "../components/subscriber/operations/operations-provenance";
import type { TenderWorkspaceData } from "../components/subscriber/operations/types";

function workspace(fixtureMode: boolean): TenderWorkspaceData {
  return {
    workspaceId: "workspace-1",
    tenderId: "tender-1",
    title: "Tender workspace",
    buyer: "Authority",
    jurisdiction: "EU",
    procedure: "Open procedure",
    dueAt: "2026-09-01T12:00:00Z",
    updatedAt: "2026-08-04T00:00:00Z",
    revision: 2,
    status: "preparing",
    fixtureMode,
    summary: "Synthetic summary",
    metrics: [
      { label: "Readiness", value: "68%" },
      { label: "Requirements", value: "4" }
    ],
    documents: [{ id: "axfx_doc_1", title: "Draft", version: "1", owner: "Team", status: "draft", updatedAt: "2026-08-04" }],
    amendments: [{ id: "amendment-1", title: "Amendment", publishedAt: "2026-08-01", affectedRequirements: 7, impact: "high" }],
    commercial: [
      { id: "commercial-1", label: "Candidate value", status: "estimated", amount: "EUR 100" },
      { id: "axfx_com_003", label: "Tax treatment", status: "not_applicable" }
    ],
    team: [{ id: "owner-1", name: "Synthetic owner", role: "Owner", responsibility: "Authority", status: "active" }],
    approvals: [{ id: "approval-1", subject: "Package", status: "pending", requestedFrom: "Approver" }],
    readiness: {
      score: 68,
      blockingItems: ["Missing evidence"],
      packagePrepared: false,
      subscriberApproved: false,
      handoffOpened: false,
      externalSubmissionConfirmed: false
    }
  };
}

test("preserves explicitly labelled engineering fixture projections", () => {
  const input = workspace(true);
  assert.equal(provenanceSafeOperationsData(input), input);
});

test("withholds client-synthesised operational projections from live-adapter mode", () => {
  const result = provenanceSafeOperationsData(workspace(false));

  assert.equal(result.procedure, "Procedure unavailable");
  assert.deepEqual(result.documents, []);
  assert.deepEqual(result.amendments, []);
  assert.deepEqual(result.team, []);
  assert.deepEqual(result.approvals, []);
  assert.equal(result.readiness, undefined);
  assert.deepEqual(result.metrics, [{ label: "Requirements", value: "4" }]);
  assert.deepEqual(result.commercial, [
    { id: "commercial-1", label: "Candidate value", status: "estimated", amount: "EUR 100" }
  ]);
});
