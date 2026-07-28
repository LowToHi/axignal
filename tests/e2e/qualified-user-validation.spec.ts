import { expect, test } from "@playwright/test";

const sessionId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const task = {
  task_id: "F1-AUTHORITY-001",
  title: "Distinguish canonical fact from proposal and context",
  language: "en",
  content_hash: `sha256:${"a".repeat(64)}`
};

function bundle(condition: "AXIGNAL" | "CONTROL", completed = false) {
  return {
    session: {
      validation_session_id: sessionId,
      condition,
      state: completed ? "COMPLETED" : "STARTED",
      outcome: completed
        ? {
            task_completed: true,
            authority_layer_correct: true,
            evidence_traceability: true,
            unknowns_identified: true,
            critical_error: false,
            confidence: 80
          }
        : null
    },
    task: {
      ...task,
      payload: {
        prompt: "Classify the highlighted statement and identify the evidence that supports it.",
        statement: "Russian real GDP growth was 2.3% in 2018.",
        evidence: [
          {
            id: "EV-WB-RUS-GDP-2018",
            title: "World Bank Russia Economic Report 41",
            excerpt: "Real GDP growth reached 2.3 percent in 2018.",
            source_state: "ADMITTED"
          }
        ],
        unknowns: [
          {
            id: "MOSCOW_MARKET_NOT_DEMONSTRATED",
            label: "The national report does not establish Moscow-specific market conditions."
          }
        ]
      }
    },
    events: [],
    response: completed
      ? {
          authority_layer_correct: true,
          evidence_traceability: true,
          unknowns_identified: true,
          critical_error: false,
          task_completed: true
        }
      : null
  };
}

async function installRoutes(page: Parameters<typeof test>[0]["page"], condition: "AXIGNAL" | "CONTROL") {
  await page.route("**/api/validation/tasks?language=en", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ tasks: [task] })
    });
  });
  await page.route("**/api/validation/sessions", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify(bundle(condition))
    });
  });
  await page.route(`**/api/validation/sessions/${sessionId}/events`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(bundle(condition))
    });
  });
  await page.route(`**/api/validation/sessions/${sessionId}/complete`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(bundle(condition, true))
    });
  });
}

for (const condition of ["AXIGNAL", "CONTROL"] as const) {
  test(`renders equivalent content in the ${condition} condition`, async ({ page }) => {
    await installRoutes(page, condition);
    await page.goto("/validation");
    await page.getByRole("button", { name: "Start controlled session" }).click();

    await expect(page.getByTestId("validation-condition")).toHaveText(condition);
    await expect(
      page.getByTestId(condition === "AXIGNAL" ? "axignal-condition" : "control-condition")
    ).toBeVisible();
    await expect(page.getByText("Russian real GDP growth was 2.3% in 2018.")).toBeVisible();
    await expect(page.getByText("World Bank Russia Economic Report 41")).toBeVisible();
    await expect(page.getByText(/authority_layer|reference_answer|required_evidence_ids/i)).toHaveCount(0);

    await page.getByLabel("Authority state").selectOption("CANONICAL_CLAIM");
    await page.getByLabel(/World Bank Russia Economic Report 41/).check();
    await page.getByLabel(/national report does not establish Moscow-specific/).check();
    await page.getByLabel("Explanation").fill("The evidence supports the national fact but not a local claim.");
    await page.getByRole("button", { name: "Submit immutable response" }).click();

    await expect(page.getByTestId("validation-outcome")).toContainText("task_completed");
    await expect(page.getByTestId("validation-outcome")).toContainText("append-only");
  });
}
