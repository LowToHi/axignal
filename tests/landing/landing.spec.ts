import { expect, test } from "@playwright/test";

test("renders the production Globe narrative and synthetic-data boundary", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { level: 1, name: /Discover what is changing/i })
  ).toBeVisible();
  await expect(page.getByText(/Synthetic demonstration · not investment performance/i)).toBeVisible();
  await expect(page.getByTestId("semantic-globe")).toBeAttached();
  await expect(page.getByRole("link", { name: "Request private access" }).first()).toBeVisible();

  const bodyWidth = await page.locator("body").evaluate((element) => element.scrollWidth);
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 1);
});

test("supports reduced motion without hiding the investigation", async ({ browser }) => {
  const context = await browser.newContext({ reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /The world produces more information/i })).toBeVisible();
  await page.getByRole("link", { name: "Explore the investigation" }).click();
  await expect(page.locator("#investigation")).toBeInViewport();

  await context.close();
});

test("submits a consented private-pilot request through the typed endpoint", async ({ page }) => {
  await page.route("**/api/pilot-intake", async (route) => {
    const request = route.request();
    const body = request.postDataJSON() as { email: string; consent: boolean; useCase: string };
    expect(body.email).toBe("analyst@example.com");
    expect(body.consent).toBe(true);
    expect(body.useCase.length).toBeGreaterThanOrEqual(20);

    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({
        status: "received",
        message: "Request received. AXIGNAL will review the fit for the private pilot."
      })
    });
  });

  await page.goto("/#access");
  await page.getByLabel("Work email").fill("analyst@example.com");
  await page.getByLabel("Role").selectOption("Analyst");
  await page.getByLabel("Organisation").fill("Example Research");
  await page
    .getByLabel("What decision would AXIGNAL support?")
    .fill("Compare infrastructure and policy transmission across four European markets.");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Request private access" }).click();

  await expect(page.getByText(/AXIGNAL will review the fit/i)).toBeVisible();
});

test("captures visual-review evidence", async ({ page }, testInfo) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: /Discover what is changing/i })).toBeVisible();

  const capture = async (name: string) => {
    const path = testInfo.outputPath(`${name}.png`);
    await page.screenshot({ path, fullPage: false, animations: "disabled" });
    await testInfo.attach(name, { path, contentType: "image/png" });
  };

  await capture("hero");

  await page.locator("#investigation").scrollIntoViewIfNeeded();
  await page.waitForTimeout(700);
  await capture("investigation");

  await page.locator("#access").scrollIntoViewIfNeeded();
  await page.waitForTimeout(700);
  await expect(page.getByLabel("Work email")).toBeVisible();
  await capture("access");
});
