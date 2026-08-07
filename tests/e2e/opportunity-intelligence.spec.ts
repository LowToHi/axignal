import { expect, test } from "@playwright/test";

/**
 * Prioridad 5 — Playwright over the real web surface.
 *
 * Requires the full local stack (API + web + PostgreSQL) running on
 * http://127.0.0.1:3000 with the test runtime (bot token auto-login).
 *
 * Verifies the materialized Opportunity Intelligence surfaces:
 * - landing consumes the real libraries API (O01 present);
 * - pricing consumes the real sandbox catalogue (149/399 hypotheses);
 * - library page O01 renders with coverage disclosure;
 * - Public Employment stays hidden (noindex) and not linked from Shell 1.
 */

const BASE = process.env.AXIGNAL_PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";

test("vertical slice O01: real surfaces render API data", async ({ page }) => {
  test.setTimeout(60_000);

  // 1. Shell 1 landing: libraries from the real API.
  const response = await page.goto(`${BASE}/opportunity-intelligence`, {
    waitUntil: "networkidle"
  });
  expect(response?.status()).toBeLessThan(500);
  await expect(
    page.getByRole("heading", { name: "AXIGNAL Opportunity Intelligence" })
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /Global Public Procurement/ })
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /Innovation, Research and Intellectual Property/ })
  ).toBeVisible();

  // 2. Pricing page: hypotheses from the sandbox catalogue.
  await page.goto(`${BASE}/opportunity-intelligence/pricing`, {
    waitUntil: "networkidle"
  });
  await expect(
    page.getByRole("heading", { name: "Pricing" })
  ).toBeVisible();
  await expect(page.getByText("149.00 EUR/month")).toBeVisible();
  await expect(page.getByText("399.00 EUR/month")).toBeVisible();
  await expect(page.getByText(/pricing hypotheses/)).toBeVisible();

  // 3. Library page O01 with coverage disclosure.
  await page.goto(`${BASE}/opportunity-intelligence/libraries/O01`, {
    waitUntil: "networkidle"
  });
  await expect(
    page.getByRole("heading", { name: "Public Procurement" })
  ).toBeVisible();
  await expect(page.getByText(/Coverage disclosure/)).toBeVisible();

  // 4. Library pages O02-O09 render.
  for (const libraryId of ["O02", "O03", "O04", "O05", "O06", "O07", "O08", "O09"]) {
    await page.goto(`${BASE}/opportunity-intelligence/libraries/${libraryId}`, {
      waitUntil: "domcontentloaded"
    });
    expect(page.url()).toContain(libraryId);
  }

  // 5. Public Employment: hidden surface, not launched, never linked from Shell 1.
  await page.goto(`${BASE}/empleo-publico`, { waitUntil: "networkidle" });
  await expect(page.getByText(/DRAFT/)).toBeVisible();
  await expect(page.getByText(/no indexable|No indexable/)).toBeVisible();
  const robots = await page.evaluate(() => {
    const meta = document.querySelector('meta[name="robots"]');
    return meta ? meta.getAttribute("content") : "";
  });
  expect(robots.toLowerCase()).toContain("noindex");
  expect(robots.toLowerCase()).toContain("nofollow");
});

test("vertical slice O01: Shell 1 does not link to Public Employment", async ({
  page
}) => {
  test.setTimeout(60_000);
  await page.goto(`${BASE}/opportunity-intelligence`, {
    waitUntil: "networkidle"
  });
  const empleoLinks = page.getByRole("link", { name: /empleo|public employment/i });
  expect(await empleoLinks.count()).toBe(0);
});
