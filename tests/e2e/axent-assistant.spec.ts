import { expect, test } from "@playwright/test";

/**
 * Mandato AXENT — sección 9: AXENT global assistant over the real web.
 *
 * The test-runtime session authenticates server-side; the assistant panel
 * is rendered by the root layout (available from any product surface) and
 * talks to the real API through /api/axent/* proxies.
 */
test("AXENT global assistant renders and answers on the real web", async ({
  page,
  context,
}) => {
  // Real test-runtime login so the assistant proxy carries an identity.
  const login = await context.request.post("/api/auth/login", {
    data: { email: "test-runtime@axignal.test", password: "axignal-test-pass" },
  });
  expect(login.status()).toBe(200);

  await page.goto("/opportunity-intelligence");
  await expect(page.getByLabel("Abrir AXENT")).toBeVisible();

  await page.getByLabel("Abrir AXENT").click();
  await expect(
    page.getByLabel("AXENT asistente")
  ).toBeVisible();

  const input = page.getByLabel("Mensaje para AXENT");
  await expect(input).toBeVisible();
  await input.fill("muéstreme oportunidades de ciberseguridad");
  await page.getByRole("button", { name: "Enviar" }).click();

  // The assistant answers with a grounded segment (real API -> PostgreSQL).
  await expect(
    page.locator("section[aria-label='AXENT asistente']").getByText(/AXIGNAL|No se ha identificado|La evidencia/)
  ).toBeVisible({ timeout: 20000 });
});

test("AXENT dedicated page exists and is not indexed", async ({ page }) => {
  await page.goto("/axent");
  await expect(page.getByRole("heading", { level: 1, name: "AXENT" })).toBeVisible();
  const noindex = await page
    .locator('meta[name="robots"]')
    .getAttribute("content");
  expect(noindex).toContain("noindex");
});
