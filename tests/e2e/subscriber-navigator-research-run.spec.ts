import { expect, test } from "@playwright/test";

const researchRunId = "8b85ef72-4db4-4f75-a8b1-b07ca3db7cd0";

test("subscriber Navigator refuses synthetic ResearchRun fallback", async ({ page }) => {
  const bootstrapResponse = await page.request.get(
    "/api/subscriber-workspace/bootstrap"
  );
  expect(bootstrapResponse.status()).toBe(200);
  const bootstrap = (await bootstrapResponse.json()) as {
    route_data: { opportunities: Array<{ id: string }> };
  };
  const opportunityId = bootstrap.route_data.opportunities[0]?.id;
  expect(opportunityId).toBeTruthy();

  const response = await page.request.post("/api/research/runs", {
    data: {
      question: "Verify the selected procurement opportunity.",
      locale: "en",
      includePrivateKnowledge: false,
      researchMode: "STRUCTURED_SOURCE_OBSERVATION",
      subscriberOpportunityId: opportunityId
    }
  });
  expect(response.status()).toBe(503);
  await expect(response.json()).resolves.toMatchObject({
    error: expect.stringContaining("synthetic fallback is forbidden")
  });
});

test("Navigator creates a persistent ResearchRun and redirects to its canonical route", async ({
  page
}) => {
  await page.route("**/api/research/runs**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (request.method() === "POST" && url.pathname === "/api/research/runs") {
      const body = request.postDataJSON() as Record<string, unknown>;
      expect(body).toMatchObject({
        question: "Investigate the selected opportunity with admitted sources.",
        includePrivateKnowledge: false,
        researchMode: "STRUCTURED_SOURCE_OBSERVATION"
      });
      expect(body.subscriberOpportunityId).toEqual(expect.any(String));
      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({
          research_run_id: researchRunId,
          state: "QUEUED",
          queue_delivery: "PUBLISHED",
          source_ids: ["ted-eu"],
          synthetic: false
        })
      });
      return;
    }
    if (
      request.method() === "GET" &&
      url.pathname === `/api/research/runs/${researchRunId}`
    ) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          research_run_id: researchRunId,
          context_id: "subscriber:tenant:opportunity",
          opportunity_id: "axfx_opp_eu_mobility_001",
          question: "Investigate the selected opportunity with admitted sources.",
          state: "COMPLETED",
          private_knowledge_authorised: false,
          source_plan: [{ source_id: "ted-eu", status: "USED" }],
          budgets: {},
          actual_usage: {},
          evidence: [
            {
              evidence_id: "ev_ted_001",
              source_id: "ted-eu",
              title: "TED notice version 4",
              relationship: "SUPPORT",
              observed_at: "2026-08-04T00:00:00Z",
              rights_status: "RIGHTS_VALID",
              provisional: false,
              payload: {}
            }
          ],
          candidate_claims: [
            {
              candidate_claim_id: "cc_001",
              statement: "The notice contains a submission deadline.",
              kind: "SUPPORT",
              state: "ADMITTED",
              producer_type: "DETERMINISTIC_PARSER",
              method_version: "ted-parser@1",
              canonical_claim_id: "claim_001",
              rejection_reasons: []
            }
          ],
          canonical_claims: [
            {
              canonical_claim_id: "claim_001",
              statement: "The deadline is 28 August 2026.",
              state: "ADMITTED",
              epistemic_class: "OBSERVED"
            }
          ],
          dossier: {
            dossier_id: "dossier_001",
            status: "READY",
            title: "Procurement evidence dossier",
            summary: "One admitted deadline claim.",
            sections: [],
            attribution: {}
          },
          admission_batch_id: "batch_001",
          error_code: null,
          error_detail: null,
          created_at: "2026-08-04T00:00:00Z",
          updated_at: "2026-08-04T00:00:10Z",
          synthetic: false
        })
      });
      return;
    }
    await route.fallback();
  });

  await page.goto("/investigations");
  const composer = page.getByLabel("Write a command or question…");
  await expect(composer).toBeVisible();
  await composer.fill(
    "Investigate the selected opportunity with admitted sources."
  );
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page).toHaveURL(`/research-runs/${researchRunId}`);
  await expect(page.getByRole("heading", { name: "ResearchRun" })).toBeVisible();
  await expect(page.getByText("COMPLETED").first()).toBeVisible();
  await expect(page.getByText("TED notice version 4")).toBeVisible();
  await expect(page.getByText("The deadline is 28 August 2026.")).toBeVisible();
  await expect(page.getByText("Procurement evidence dossier")).toBeVisible();
  await expect(page.getByText("No synthetic result is substituted")).toBeVisible();
});
