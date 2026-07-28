import { expect, test } from "@playwright/test";

const caseId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";

function reviewCase(state: "OPEN" | "RESOLVED" = "OPEN") {
  return {
    human_review_case_id: caseId,
    tenant_id: "77777777-7777-4777-8777-777777777777",
    research_run_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    admission_handoff_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    admission_decision_id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
    candidate_claim_id: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
    case_type: "HUMAN_REVIEW_REQUIRED",
    state,
    priority: "NORMAL",
    assigned_reviewer_subject: state === "RESOLVED" ? "usr_human_review_ci" : null,
    assigned_reviewer_email: state === "RESOLVED" ? "human-review-ci@example.test" : null,
    opened_reason: "candidate_class_not_auto_admissible",
    resolution: state === "RESOLVED" ? "ACCEPT_AS_CONTEXT" : null,
    resolution_reason_code: state === "RESOLVED" ? "LIMITATION_CONFIRMED" : null,
    resolution_note: state === "RESOLVED" ? "Limitación conservada como contexto no canónico." : null,
    deterministic_decision: {
      outcome: "HUMAN_REVIEW_REQUIRED",
      policy_version: "document-observed-fact@0.1.0",
      gate_results: {
        HANDOFF_SCHEMA_VALID: true,
        PACKAGE_HASH_VALID: true,
        SOURCE_STILL_ADMITTED: true,
        SOURCE_KILL_SWITCH_OFF: true,
        RIGHTS_STILL_VALID: true,
        RAW_OBJECT_HASH_VALID: true,
        PRODUCER_AUTHORITY_SEPARATED: true,
        POLICY_VERSION_PINNED: true
      },
      rejection_reasons: ["candidate_class_not_auto_admissible"],
      canonical_claim_id: null
    },
    candidate_claim: {
      statement: "The national forecasts do not establish Moscow property-market conditions.",
      kind: "LIMITATION",
      state: "HUMAN_REVIEW_REQUIRED",
      producer_type: "LOCAL_MODEL",
      producer_id: "proposal-only-model",
      method_version: "institutional-claim-extraction@0.1.0",
      assumptions: [],
      unknowns: ["No local transaction or yield evidence is present."],
      canonical_claim_id: null
    },
    source: {
      source_id: "world-bank-rer41",
      name: "World Bank Russia Economic Report 41",
      rights_status: "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
      license_id: "CC-BY-4.0",
      admission_state: "ADMITTED",
      kill_switch: false
    },
    evidence: [
      {
        evidence_id: "ffffffff-ffff-4fff-8fff-ffffffffffff",
        title: "Local-market applicability limitation",
        relationship: "CONTEXT",
        source_id: "world-bank-rer41",
        rights_status: "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        fragment_id: "frag_limitation",
        quote_hash: "sha256:fixture",
        text: "National forecasts do not establish Moscow property conditions."
      }
    ],
    events: state === "RESOLVED"
      ? ["CASE_OPENED", "CASE_ASSIGNED", "REVIEW_STARTED", "RESOLUTION_RECORDED", "CASE_CLOSED"].map(
          (event_type, index) => ({
            human_review_event_id: `${index}0000000-0000-4000-8000-000000000000`,
            event_type,
            actor_subject: index === 0 ? null : "usr_human_review_ci",
            actor_email: index === 0 ? null : "human-review-ci@example.test",
            reason_code: "LIMITATION_CONFIRMED",
            payload: {},
            occurred_at: "2026-07-28T10:00:00Z"
          })
        )
      : [
          {
            human_review_event_id: "10000000-0000-4000-8000-000000000000",
            event_type: "CASE_OPENED",
            actor_subject: null,
            actor_email: null,
            reason_code: "candidate_class_not_auto_admissible",
            payload: {},
            occurred_at: "2026-07-28T10:00:00Z"
          }
        ]
  };
}

test("keeps model proposal, deterministic decision and human review distinct", async ({ page }) => {
  await page.route("**/api/human-review/cases", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ cases: [reviewCase()] }) });
  });
  await page.route(`**/api/human-review/cases/${caseId}/actions`, async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(reviewCase("RESOLVED")) });
  });

  await page.goto("/");
  const review = page.getByRole("complementary", { name: "Human Review" });
  await expect(review).toBeVisible();
  await expect(review.getByText("MODEL PROPOSAL", { exact: true })).toBeVisible();
  await expect(review.getByText("DETERMINISTIC DECISION", { exact: true })).toBeVisible();
  await expect(review.getByText("HUMAN REVIEW", { exact: true }).first()).toBeVisible();
  await expect(review.getByText(/canonical_claim_id: null/).first()).toBeVisible();

  await review.getByRole("button", { name: "Aceptar como contexto" }).click();
  await expect(review).toHaveAttribute("data-state", "RESOLVED");
  await expect(review.getByText(/no se creó ningún claim canónico/i)).toBeVisible();
  await expect(review.getByText(/events: 5/i)).toBeVisible();
});
