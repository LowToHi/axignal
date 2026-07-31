import { expect, test } from "@playwright/test";

const prohibitedClaims = [
  "guaranteed truth",
  "zero hallucinations",
  "100 percent accurate",
  "fully autonomous decisions",
  "replace your analysts",
  "market validated"
];

test("renders the buyer-outcome message and publication boundary", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      level: 1,
      name: /Turn scattered sources into a decision your team can verify/i
    })
  ).toBeVisible();
  await expect(page.getByText("Keep the evidence trail intact.")).toBeVisible();
  await expect(page.getByTestId("landing-experience")).toHaveAttribute(
    "data-message-version",
    "buyer-outcome-v1.0"
  );
  await expect(page.getByText(/Synthetic demonstration · not investment performance/i)).toBeVisible();
  await expect(page.getByTestId("semantic-globe")).toBeAttached();
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);

  const bodyText = (await page.locator("body").innerText()).toLowerCase();
  for (const claim of prohibitedClaims) {
    expect(bodyText).not.toContain(claim);
  }

  const bodyWidth = await page.locator("body").evaluate((element) => element.scrollWidth);
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 1);
});

test("presents candidate plans from the versioned server price book", async ({ page }) => {
  await page.goto("/#pricing");

  const professional = page.getByTestId("plan-professional_monthly");
  const team = page.getByTestId("plan-team_monthly");

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
    page.getByRole("heading", { name: /Important decisions begin with evidence scattered/i })
  ).toBeVisible();
  await page.getByRole("link", { name: "See the research workflow" }).click();
  await expect(page.locator("#workflow")).toBeInViewport();

  await context.close();
});

test("submits message-qualified controlled-access evidence", async ({ page }) => {
  await page.route("**/api/pilot-intake", async (route) => {
    const request = route.request();
    const body = request.postDataJSON() as {
      email: string;
      role: string;
      consent: boolean;
      useCase: string;
      messageVersion: string;
    };
    expect(body.email).toBe("strategy@example.com");
    expect(body.role).toBe("Corporate strategy");
    expect(body.consent).toBe(true);
    expect(body.useCase.length).toBeGreaterThanOrEqual(20);
    expect(body.messageVersion).toBe("buyer-outcome-v1.0");

    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({
        status: "received",
        message:
          "Request received. AXIGNAL will review the research decision and controlled-access fit."
      })
    });
  });

  await page.goto("/#access");
  await page.getByLabel("Work email").fill("strategy@example.com");
  await page.getByLabel("Your role in the decision").selectOption("Corporate strategy");
  await page.getByLabel("Organisation").fill("Example Strategy");
  await page
    .getByLabel(/What must your team decide/i)
    .fill("Decide which European infrastructure markets warrant deeper diligence and why.");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Request a research workspace" }).click();

  await expect(page.getByText(/review the research decision/i)).toBeVisible();
});

test("fails closed when the intake persistence channel is not configured", async ({ page }) => {
  await page.goto("/#access");
  await page.getByLabel("Work email").fill("research@example.com");
  await page.getByLabel("Your role in the decision").selectOption("Investment research");
  await page.getByLabel("Organisation").fill("Example Research");
  await page
    .getByLabel(/What must your team decide/i)
    .fill("Assess a material research question with public and private source evidence.");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Request a research workspace" }).click();

  await expect(page.getByText(/not configured\. No request was stored/i)).toBeVisible();
  await expect(page.locator('[data-status="success"]')).toHaveCount(0);
});

test("rejects intake records without a message version", async ({ request }) => {
  const response = await request.post("/api/pilot-intake", {
    data: {
      email: "research@example.com",
      role: "Investment research",
      company: "Example Research",
      useCase: "Assess a material research decision using multiple evidence sources.",
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

test("captures visual evidence for hero, workflow, pricing and access", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.addStyleTag({ content: "html{scroll-behavior:auto!important}" });
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: /Turn scattered sources into a decision your team can verify/i
    })
  ).toBeVisible();

  const capture = async (name: string) => {
    const path = testInfo.outputPath(`${name}.png`);
    await page.screenshot({ path, fullPage: false, animations: "disabled" });
    await testInfo.attach(name, { path, contentType: "image/png" });
  };

  await page.waitForTimeout(1_000);
  await capture("message-hero");

  await page.locator('[data-story-step][data-step="4"]').scrollIntoViewIfNeeded();
  await page.waitForTimeout(700);
  await capture("evidence-workflow");

  await page.locator("#pricing").scrollIntoViewIfNeeded();
  await expect(page.getByRole("heading", { name: /Start with the team/i })).toBeVisible();
  await capture("candidate-plans");

  await page.locator("#access").scrollIntoViewIfNeeded();
  await expect(
    page.getByRole("heading", { name: /Bring one research decision that is expensive to get wrong/i })
  ).toBeVisible();
  await expect(page.getByLabel("Work email")).toBeVisible();
  await capture("controlled-access");
});
