import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ timeout: 20_000 });

async function scrollCinematic(page: Page, progress: number) {
  await page.evaluate((normalisedProgress) => {
    const stage = document.querySelector(".cinematic-stage");
    const spacer = stage?.closest(".pin-spacer");
    if (!spacer) throw new Error("CINEMATIC_PIN_SPACER_MISSING");
    const bounds = spacer.getBoundingClientRect();
    const start = window.scrollY + bounds.top;
    const distance = Math.max(window.innerHeight, bounds.height - window.innerHeight);
    window.scrollTo(0, start + normalisedProgress * distance);
  }, progress);
}

test("keeps one real Globe mounted through the six-scene desktop narrative", async ({
  page
}, testInfo) => {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));

  const response = await page.goto("/", { waitUntil: "domcontentloaded" });
  expect(response?.status()).toBe(200);
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: /Find the public contracts your business is built to pursue.*Turn global procurement into a qualified B2G pipeline/i
    })
  ).toBeVisible();

  const globe = page.getByTestId("semantic-globe");
  const canvas = globe.locator("canvas");
  const header = page.locator(".site-header");
  const brand = header.getByRole("link", { name: "AXIGNAL home" });
  await expect(globe).toHaveCount(1);
  await expect(canvas).toHaveCount(1);
  await expect(header).toBeVisible();
  await expect(brand).toBeVisible();
  await page.waitForFunction(
    () => document.querySelector(".cinematic-stage")?.parentElement?.classList.contains("pin-spacer")
  );
  await canvas.evaluate((element) => element.setAttribute("data-continuity-id", "primary-globe"));

  await scrollCinematic(page, 0.43);
  await expect(page.locator(".cinematic-running-head")).toContainText(/02|03|04/);
  await expect(page.locator(".trace-object").nth(4)).toBeVisible();
  const mobileProject = testInfo.project.name === "landing-mobile";
  await expect(globe).toHaveAttribute("data-boundary-lod-requested", mobileProject ? "false" : "true");
  await expect(globe).toHaveAttribute("data-boundary-lod-loaded", mobileProject ? "false" : "true");
  await expect(globe).toHaveAttribute("data-boundary-lod-active", mobileProject ? "false" : "true");
  await expect(header).toHaveCSS("opacity", "1");
  await expect(brand).toBeVisible();

  await scrollCinematic(page, 0.87);
  await expect(page.locator(".cinematic-running-head")).toContainText("06 / 06");
  await expect(page.locator(".cinematic-dossier")).toBeVisible();
  await expect(page.locator('canvas[data-continuity-id="primary-globe"]')).toHaveCount(1);
  await expect(header).toHaveCSS("opacity", "1");
  await expect(brand).toBeVisible();

  await page.screenshot({
    path: testInfo.outputPath("desktop-dossier.png"),
    fullPage: false
  });

  await scrollCinematic(page, 0);
  await expect(page.locator('canvas[data-continuity-id="primary-globe"]')).toHaveCount(1);
  await expect(globe).toHaveAttribute("data-boundary-lod-requested", "true");
  await expect(globe).toHaveAttribute("data-boundary-lod-loaded", "true");
  expect(page.url()).toBe("http://127.0.0.1:3001/");
  expect(pageErrors).toEqual([]);
  expect(consoleErrors).toEqual([]);
});

test("switches the landing theme without remounting the Globe", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const globe = page.getByTestId("semantic-globe");
  const themeToggle = page.getByRole("button", { name: "Switch to light" });

  await expect(globe).toHaveCount(1);
  await expect(themeToggle).toBeVisible();
  await themeToggle.click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByRole("button", { name: "Switch to dark" })).toBeVisible();
  await expect(globe).toHaveCount(1);
  await page.getByRole("button", { name: "Switch to dark" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});

test("makes the controlled trial and canonical monthly prices explicit", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.waitForFunction(
    () => document.querySelector(".cinematic-stage")?.parentElement?.classList.contains("pin-spacer")
  );
  const pricingLink = page.getByRole("link", { name: "Pricing", exact: true });
  if (await pricingLink.isVisible()) {
    await pricingLink.click();
  } else {
    await page.locator("#pricing").scrollIntoViewIfNeeded();
  }
  await expect(page.locator("#pricing")).toBeInViewport();
  await expect(page.getByRole("heading", { name: /Choose the contracted operating boundary/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Controlled Trial" }).first()).toBeVisible();
  await expect(page.getByText("1,000,000 cumulative tokens per organisation")).toBeVisible();
  await expect(page.getByText("No card", { exact: true })).toBeVisible();
  await expect(page.getByText("No automatic renewal", { exact: true })).toBeVisible();
  await expect(page.getByText("No overage", { exact: true })).toBeVisible();
  await expect(page.getByText("Read-only at expiry", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Request 7-day B2G trial" }).first()).toBeVisible();
  await expect(page.getByText(/APPLICATION ONLY · NO CARD · NO AUTOMATIC CONVERSION/)).toBeVisible();
  await expect(page.getByText(/Canonical price book · 2026-08-04/).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Professional" })).toBeVisible();
  await expect(page.getByText("€149", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Team" })).toBeVisible();
  await expect(page.getByText("€399", { exact: true })).toBeVisible();
  await expect(page.getByText("Design Partner", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Enterprise" })).toHaveCount(0);
});

test("does not expose the admitted source brand as public landing identity", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.getByText(/Tenders Electronic Daily|TED bounded/i)).toHaveCount(0);
  await expect(page.getByText(/^TED · PRODUCT_ADMITTED/i)).not.toBeVisible();
  const statusRibbon = page.locator(".status-ribbon");
  await expect(statusRibbon).toBeVisible();
  const generatedBoundary = await statusRibbon.evaluate((element) =>
    getComputedStyle(element, "::before").content.replaceAll('"', "")
  );
  expect(generatedBoundary).toBe("ADMITTED PUBLIC-SOURCE PROFILE · PRIVATE AUTHENTICATED PILOT");
});

test("retains Globe continuity and contained pricing on mobile", async ({ browser }, testInfo) => {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 1
  });
  const page = await context.newPage();
  page.setDefaultTimeout(10_000);
  await page.goto("/", { waitUntil: "domcontentloaded" });

  await expect(page.getByTestId("semantic-globe").locator("canvas")).toHaveCount(1);
  await page.waitForFunction(
    () => document.querySelector(".cinematic-stage")?.parentElement?.classList.contains("pin-spacer")
  );
  await scrollCinematic(page, 0.43);
  await expect(page.locator(".cinematic-running-head")).toContainText(/02|03|04/);
  await expect(page.locator(".trace-object").nth(4)).toBeVisible();
  await expect(page.getByTestId("semantic-globe").locator("canvas")).toHaveCount(1);
  await expect(page.getByTestId("semantic-globe")).toHaveAttribute(
    "data-boundary-lod-requested",
    "false"
  );
  await expect(page.getByTestId("semantic-globe")).toHaveAttribute(
    "data-boundary-lod-loaded",
    "false"
  );

  const dimensions = await page.evaluate(() => ({
    body: document.body.scrollWidth,
    viewport: window.innerWidth,
    regionalBoundaryDownloaded: performance
      .getEntriesByType("resource")
      .some((entry) => entry.name.includes("europe-boundaries-50m.geojson")),
    comparisonContained:
      document.querySelector(".pricing-comparison-scroll")?.scrollWidth !== undefined &&
      getComputedStyle(document.querySelector(".pricing-comparison-scroll")!).overflowX === "auto"
  }));
  expect(dimensions.body).toBeLessThanOrEqual(dimensions.viewport + 1);
  expect(dimensions.regionalBoundaryDownloaded).toBe(false);
  expect(dimensions.comparisonContained).toBe(true);

  await page.screenshot({
    path: testInfo.outputPath("mobile-evidence.png"),
    fullPage: false
  });
  await context.close();
});

test("preserves all six states without pinned scrub for reduced motion", async ({ browser }) => {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    reducedMotion: "reduce"
  });
  const page = await context.newPage();
  page.setDefaultTimeout(10_000);
  await page.goto("/", { waitUntil: "domcontentloaded" });

  await expect(page.getByTestId("semantic-globe").locator("canvas")).toHaveCount(1);
  await expect(page.locator(".reduced-story article")).toHaveCount(6);
  await expect(page.locator(".reduced-story")).toBeVisible();
  await expect(page.locator(".reduced-story")).toContainText("GLOBAL");
  await expect(page.locator(".reduced-story")).toContainText("DOSSIER");
  await expect(page.locator(".cinematic-stage")).not.toHaveCSS("position", "fixed");

  await context.close();
});
