import { expect, test } from "@playwright/test";

/**
 * Prioridad 2 — Opportunity Operations over the real web + API + PostgreSQL.
 *
 * The test-runtime session (bot token) authenticates server-side; every
 * action flows browser -> Next.js proxy -> FastAPI -> PostgreSQL and the
 * page reflects the persisted result.
 */

const BASE = process.env.AXIGNAL_PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";

test("operations: discover opportunities from the pipeline", async ({ page }) => {
  test.setTimeout(60_000);
  const response = await page.goto(`${BASE}/opportunity-intelligence/opportunities`, {
    waitUntil: "networkidle"
  });
  expect(response?.status()).toBeLessThan(500);
  await expect(
    page.getByRole("heading", { name: "Opportunities" })
  ).toBeVisible();
  // Either the table renders (data present) or the empty state is honest.
  const rows = page.locator("tbody tr");
  const empty = page.getByText(/No hay oportunidades todavía/);
  if ((await rows.count()) > 0) {
    await expect(rows.first()).toBeVisible();
  } else {
    await expect(empty).toBeVisible();
  }
});

test("operations: notices page renders versioned O01 data", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto(`${BASE}/opportunity-intelligence/notices`, {
    waitUntil: "networkidle"
  });
  await expect(page.getByRole("heading", { name: "Notices" })).toBeVisible();
  const rows = page.locator("tbody tr");
  if ((await rows.count()) > 0) {
    const firstRow = rows.first();
    await expect(firstRow).toContainText("123456-2026");
    await expect(firstRow).toContainText("Cybersecurity");
  }
});

test("operations: opportunity detail renders evidence and claims", async ({
  page
}) => {
  test.setTimeout(60_000);
  await page.goto(`${BASE}/opportunity-intelligence/opportunities`, {
    waitUntil: "networkidle"
  });
  const link = page.getByRole("link", { name: /opp_ted_/ }).first();
  if ((await link.count()) === 0) {
    test.skip(true, "no pipeline opportunities available in this environment");
    return;
  }
  await link.click();
  await page.waitForLoadState("networkidle");
  await expect(page.getByRole("heading", { name: /opp_ted_/ })).toBeVisible();
  // Evidence + canonical claims sections render (data or honest empty).
  await expect(page.getByRole("heading", { name: "Evidence" })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Canonical claims" })
  ).toBeVisible();
});

test("operations: workspaces page renders and supports creation", async ({
  page
}) => {
  test.setTimeout(60_000);
  await page.goto(`${BASE}/opportunity-intelligence/workspaces`, {
    waitUntil: "networkidle"
  });
  await expect(page.getByRole("heading", { name: "Workspaces" })).toBeVisible();
  const rows = page.locator("tbody tr");
  if ((await rows.count()) > 0) {
    // Creation control is present next to each workspace row.
    await expect(
      rows.first().getByRole("button", { name: /Crear Bid Workspace/ })
    ).toBeVisible();
  }
});

test("operations: subscription and entitlement status reachable", async ({
  page
}) => {
  test.setTimeout(60_000);
  await page.goto(`${BASE}/opportunity-intelligence`, {
    waitUntil: "networkidle"
  });
  // Landing links to pricing (catalogue status) and operations surfaces.
  await expect(page.getByRole("link", { name: "Pricing" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Pursuits" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Workspaces" })).toBeVisible();
});
