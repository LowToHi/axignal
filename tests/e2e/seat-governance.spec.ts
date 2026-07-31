import { expect, test } from "@playwright/test";

test.describe.configure({ mode: "serial", retries: 0 });
test.skip(
  process.env.AXIGNAL_PLAYWRIGHT_EXTERNAL_SERVER !== "true" ||
    process.env.AXIGNAL_PLAYWRIGHT_BASE_URL !== "http://127.0.0.1:18080",
  "Seat governance E2E requires the isolated billing and seat topology."
);

async function login(page: import("@playwright/test").Page) {
  await page.goto("/");
  const email = page.getByLabel("Email");
  if (await email.isVisible().catch(() => false)) {
    await email.fill("pilot@example.test");
    await page.getByLabel("Contraseña").fill("pilot-password");
    await page.getByRole("button", { name: "Entrar" }).click();
  }
  await expect(page.locator("main.shell")).toBeVisible();
}

async function confirmCheckout(page: import("@playwright/test").Page) {
  await page.getByRole("button", { name: /PLAN ·/ }).click();
  const panel = page.getByRole("complementary", { name: "Plan y facturación" });
  await panel.getByText(/Confirmo que estoy seleccionando explícitamente/).click();
  await panel.getByRole("button", { name: "Seleccionar Professional" }).click();
  await expect(page).toHaveURL(/\/billing\/test-checkout/);
  await page.getByRole("button", { name: "Confirmar pago de prueba" }).click();
  await expect(page).toHaveURL(/billing=success/);
  await expect(page.locator("main.shell")).toBeVisible();
  await expect(page.getByText(/Plan: Professional · acceso ACTIVE/)).toBeVisible();
  await page
    .getByRole("complementary", { name: "Plan y facturación" })
    .getByRole("button", { name: "Cerrar" })
    .click();
}

async function confirmUpgrade(page: import("@playwright/test").Page) {
  const billing = page.getByRole("complementary", { name: "Plan y facturación" });
  await billing.getByRole("button", { name: "Upgrade explícito a Team" }).click();
  const result = await page.evaluate(async () => {
    const response = await fetch("/api/billing/test/provider-event", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: "CONFIRM_UPGRADE" })
    });
    return { ok: response.ok, text: await response.text() };
  });
  expect(result.ok, result.text).toBeTruthy();
  await billing.getByRole("button", { name: "Actualizar" }).click();
  await expect(page.getByText(/Plan: Team · acceso ACTIVE/)).toBeVisible();
}

test("governs flat-tier seats from payment through capacity and upgrade", async ({ page }) => {
  await login(page);
  await confirmCheckout(page);

  const seatLauncher = page.getByRole("button", { name: "SEATS · SETUP" });
  await expect(seatLauncher).toBeVisible();
  await seatLauncher.click();

  const seatPanel = page.getByRole("complementary", {
    name: "Organisation seats and members"
  });
  await seatPanel.getByRole("button", { name: "Initialise owner seat" }).click();
  await expect(page.getByRole("button", { name: "SEATS · 1/3" })).toBeVisible();
  await expect(seatPanel.getByText("Professional")).toBeVisible();
  await expect(seatPanel.getByText("FLAT_TIER")).toBeVisible();

  await seatPanel.getByLabel("Work email").fill("member2@example.test");
  await seatPanel.getByLabel("Initial role").selectOption("BID_REVIEWER");
  await seatPanel.getByRole("button", {
    name: "Reserve seat and send invitation"
  }).click();
  await expect(page.getByRole("button", { name: "SEATS · 2/3" })).toBeVisible();
  await expect(seatPanel.getByText(/TEST ONLY acceptance token/)).toBeVisible();

  await seatPanel.getByLabel("Work email").fill("member3@example.test");
  await seatPanel.getByLabel("Initial role").selectOption("VIEWER");
  await seatPanel.getByRole("button", {
    name: "Reserve seat and send invitation"
  }).click();
  await expect(page.getByRole("button", { name: "SEATS · 3/3" })).toBeVisible();
  await expect(seatPanel.getByText(/Seat capacity exhausted/)).toBeVisible();
  await expect(
    seatPanel.getByRole("button", { name: "Reserve seat and send invitation" })
  ).toBeDisabled();

  const revokeButtons = seatPanel.getByRole("button", { name: "Revoke invitation" });
  await revokeButtons.first().click();
  await expect(page.getByRole("button", { name: "SEATS · 2/3" })).toBeVisible();

  await page.getByRole("button", { name: /PLAN · Professional/ }).click();
  await confirmUpgrade(page);
  await page
    .getByRole("complementary", { name: "Plan y facturación" })
    .getByRole("button", { name: "Cerrar" })
    .click();
  await seatPanel.getByRole("button", { name: "Refresh" }).click();
  await expect(page.getByRole("button", { name: "SEATS · 2/15" })).toBeVisible();
  await expect(seatPanel.getByText("Team")).toBeVisible();
  await expect(seatPanel.getByText(/Stripe bills one package unit/)).toBeVisible();
});
