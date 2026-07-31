import { expect, test } from "@playwright/test";

const prohibitedClaims = [
  "guaranteed truth",
  "guaranteed win",
  "zero hallucinations",
  "100 percent accurate",
  "fully autonomous decisions",
  "replace your analysts",
  "market validated",
  "complete global coverage"
];

test("renders the explicit B2G message and publication boundary", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      level: 1,
      name: /Find the public contracts your business is built to pursue/i
    })
  ).toBeVisible();
  await expect(page.getByText(/Business-to-Government \(B2G\) Opportunity Intelligence/i).first()).toBeVisible();
  await expect(page.getByText(/Turn global procurement into a qualified B2G pipeline/i)).toBeVisible();
  await expect(page.getByTestId("landing-experience")).toHaveAttribute(
    "data-message-version",
    "b2g-opportunity-v1.0"
  );
  await expect(page.getByText(/Synthetic demonstration · not procurement or win-rate evidence/i)).toBeVisible();
  await expect(page.getByTestId("semantic-globe")).toBeAttached();
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);

  const bodyText = (await page.locator("body").innerText()).toLowerCase();
  for (const claim of prohibitedClaims) {
    expect(bodyText).not.toContain(claim);
  }
  expect(bodyText).not.toMatch(/\bted\b/i);

  const bodyWidth = await page.locator("body").evaluate((element) => element.scrollWidth);
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 1);
});

test("presents the controlled trial and paid plans from the server price book", async ({ page }) => {
  await page.goto("/#pricing");

  const trial = page.getByTestId("plan-controlled_trial_7d");
  const professional = page.getByTestId("plan-professional_monthly");
  const team = page.getByTestId("plan-team_monthly");

  await expect(trial).toContainText("7-day B2G trial");
  await expect(trial).toContainText("Free");
  await expect(trial).toContainText("for 7 days");
  await expect(trial).toContainText("1,000,000 AI tokens");
  await expect(trial).toContainText("no card");
  await expect(professional).toContainText("Professional");
  await expect(professional).toContainText("€149");
  await expect(professional).toContainText("1–3 seats");
  await expect(team).toContainText("Team");
  await expect(team).toContainText("€399");
  await expect(team).toContainText("4–15 seats");
  await expect(page.getByText(/public Stripe live checkout is not enabled/i)).toBeVisible();
});

test("supports reduced motion and keyboard navigation", async ({ browser }) => {
  const context = await browser.newContext({ reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.goto("/");

  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeInViewport();

  await expect(
    page.getByRole("heading", { name: /Start with what your company can credibly sell to government/i })
  ).toBeVisible();
  await page.getByRole("link", { name: "See a public-contract investigation" }).click();
  await expect(page.locator("#workflow")).toBeInViewport();

  await context.close();
});

test("submits message-qualified B2G trial evidence", async ({ page }) => {
  await page.route("**/api/pilot-intake", async (route) => {
    const request = route.request();
    const body = request.postDataJSON() as {
      email: string;
      role: string;
      consent: boolean;
      useCase: string;
      messageVersion: string;
    };
    expect(body.email).toBe("b2g@example.com");
    expect(body.role).toBe("Bid or proposal management");
    expect(body.consent).toBe(true);
    expect(body.useCase.length).toBeGreaterThanOrEqual(20);
    expect(body.messageVersion).toBe("b2g-opportunity-v1.0");

    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({
        status: "received",
        message:
          "Request received. AXIGNAL will review the B2G market, source coverage and controlled-trial fit."
      })
    });
  });

  await page.goto("/#access");
  await page.getByLabel("Work email").fill("b2g@example.com");
  await page.getByLabel("Your role in the B2G decision").selectOption("Bid or proposal management");
  await page.getByLabel("Company").fill("Example Public Sector Supplier");
  await page
    .getByLabel(/What does your company sell to government/i)
    .fill("We sell transport analytics to European public authorities and need to qualify framework tenders.");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Request 7-day B2G trial" }).click();

  await expect(page.getByText(/review the B2G market/i)).toBeVisible();
});

test("fails closed when the B2G trial channel is not configured", async ({ page }) => {
  await page.goto("/#access");
  await page.getByLabel("Work email").fill("sales@example.com");
  await page.getByLabel("Your role in the B2G decision").selectOption("Business development");
  await page.getByLabel("Company").fill("Example Supplier");
  await page
    .getByLabel(/What does your company sell to government/i)
    .fill("We provide energy-efficiency services and need to qualify municipal tenders in Spain and France.");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Request 7-day B2G trial" }).click();

  await expect(page.getByText(/not configured\. No request was stored/i)).toBeVisible();
  await expect(page.locator('[data-status="success"]')).toHaveCount(0);
});

test("rejects B2G intake records without a message version", async ({ request }) => {
  const response = await request.post("/api/pilot-intake", {
    data: {
      email: "b2g@example.com",
      role: "Tender or procurement intelligence",
      company: "Example Supplier",
      useCase: "Qualify public-sector technology tenders across two target markets.",
      consent: true,
      website: ""
    }
  });

  expect(response.status()).toBe(422);
  const body = (await response.json()) as { status: string; message: string };
  expect(body).toMatchObject({
    status: "rejected",
    message: expect.stringContaining("message version")
  });
});

test("captures B2G visual evidence for hero, workflow, pricing and trial", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.addStyleTag({ content: "html{scroll-behavior:auto!important}" });
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: /Find the public contracts your business is built to pursue/i
    })
  ).toBeVisible();

  const capture = async (name: string) => {
    const path = testInfo.outputPath(`${name}.png`);
    await page.screenshot({ path, fullPage: false, animations: "disabled" });
    await testInfo.attach(name, { path, contentType: "image/png" });
  };

  await page.waitForTimeout(1_000);
  await capture("b2g-hero");

  await page.locator('[data-story-step][data-step="4"]').scrollIntoViewIfNeeded();
  await page.waitForTimeout(700);
  await capture("b2g-opportunity-workflow");

  await page.locator("#pricing").scrollIntoViewIfNeeded();
  await expect(page.getByRole("heading", { name: /Prove the workflow on one real B2G market/i })).toBeVisible();
  await capture("b2g-trial-and-plans");

  await page.locator("#access").scrollIntoViewIfNeeded();
  await expect(
    page.getByRole("heading", { name: /Bring one public-procurement market/i })
  ).toBeVisible();
  await expect(page.getByLabel("Work email")).toBeVisible();
  await capture("b2g-trial-request");
});
