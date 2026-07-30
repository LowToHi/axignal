import { expect, test } from "@playwright/test";

test.describe.configure({ mode: "serial", retries: 0 });

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

async function emitProviderEvent(
  page: import("@playwright/test").Page,
  action: "CONFIRM_UPGRADE" | "CONFIRM_CANCELLATION" | "ROLLBACK"
) {
  const result = await page.evaluate(async (requestedAction) => {
    const response = await fetch("/api/billing/test/provider-event", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: requestedAction })
    });
    return { ok: response.ok, status: response.status, text: await response.text() };
  }, action);
  expect(result.ok, `${result.status}: ${result.text}`).toBeTruthy();
  const refresh = page.getByRole("button", { name: "Actualizar" });
  if (await refresh.isVisible().catch(() => false)) await refresh.click();
}

test("executes the authenticated commercial shell without external Stripe", async ({ page }) => {
  await login(page);

  const launcher = page.getByRole("button", { name: /PLAN ·/ });
  await launcher.click();
  const panel = page.getByRole("complementary", { name: "Plan y facturación" });
  await expect(panel).toBeVisible();
  await expect(panel.getByText("NO_PLAN", { exact: true })).toBeVisible();
  await panel.getByText(/Confirmo que estoy seleccionando explícitamente/).click();

  const chooseProfessional = panel.getByRole("button", {
    name: "Seleccionar Professional"
  });
  await expect(chooseProfessional).toBeEnabled();
  await chooseProfessional.click();

  await expect(page).toHaveURL(/\/billing\/test-checkout/);
  const checkoutUrl = page.url();
  await expect(page.getByText("Confirmación de pago de prueba")).toBeVisible();
  await expect(page.getByText(/Cargar esta página o volver a AXIGNAL no concede acceso/)).toBeVisible();

  await page.getByRole("link", { name: "Cancelar y volver" }).click();
  await expect(page.locator("main.shell")).toBeVisible();
  await page.getByRole("button", { name: /PLAN ·/ }).click();
  await expect(page.getByText(/PAYMENT_CONFIRMATION_PENDING/)).toBeVisible();
  await expect(page.getByText(/acceso NO_ENTITLEMENT/)).toBeVisible();

  await page.goto(checkoutUrl);
  await page.getByRole("button", { name: "Confirmar pago de prueba" }).click();
  await expect(page).toHaveURL(/billing=success/);
  await expect(page.locator("main.shell")).toBeVisible();
  await expect(page.getByText("ACTIVE", { exact: true }).first()).toBeVisible();
  await expect(page.getByText(/Plan: Professional · acceso ACTIVE/)).toBeVisible();
  await expect(page.getByText(/IA mensual sin cuota de tokens: sí/)).toBeVisible();

  await page.getByRole("button", { name: "Upgrade explícito a Team" }).click();
  await expect(page.getByText("UPGRADE_PENDING", { exact: true })).toBeVisible();
  await emitProviderEvent(page, "CONFIRM_UPGRADE");
  await expect(page.getByText(/Plan: Team · acceso ACTIVE/)).toBeVisible();

  await page.getByRole("button", { name: "Cancelar al final del periodo" }).click();
  await expect(page.getByText("CANCEL_PENDING", { exact: true })).toBeVisible();
  await emitProviderEvent(page, "CONFIRM_CANCELLATION");
  await expect(page.getByText("CANCEL_AT_PERIOD_END", { exact: true })).toBeVisible();
  await expect(page.getByText(/Cancelación programada/)).toBeVisible();
  await expect(page.getByText(/acceso ACTIVE/)).toBeVisible();

  await emitProviderEvent(page, "CONFIRM_CANCELLATION");
  await expect(page.getByText("CANCELLED", { exact: true }).first()).toBeVisible();
  await expect(page.getByText(/acceso CANCELLED/)).toBeVisible();

  await emitProviderEvent(page, "ROLLBACK");
  await expect(page.getByText("ROLLED_BACK", { exact: true })).toBeVisible();
  await expect(page.getByText("PAID_LIFECYCLE_ROLLED_BACK", { exact: true })).toBeVisible();
  await expect(page.getByText(/Stripe sandbox externo verificado: no/)).toBeVisible();

  const persistedSummaryPromise = page.waitForResponse(
    (response) => response.url().includes("/api/billing/summary") && response.status() === 200
  );
  await page.reload();
  const persistedSummaryResponse = await persistedSummaryPromise;
  const persistedSummary = (await persistedSummaryResponse.json()) as {
    selection?: { state?: string } | null;
    entitlement?: { state?: string; plan_code?: string } | null;
  };
  expect(persistedSummary.selection?.state).toBe("ROLLED_BACK");
  expect(persistedSummary.entitlement?.state).toBe("CANCELLED");
  expect(persistedSummary.entitlement?.plan_code).toBe("TEAM_MONTHLY");
  await expect(page.getByRole("button", { name: "PLAN · Team" })).toBeVisible();
});
