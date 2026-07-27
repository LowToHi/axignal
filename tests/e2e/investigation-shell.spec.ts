import { expect, test } from "@playwright/test";

test("preserves the canonical Navigator → lens → evidence workflow", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("AXIGNAL NAVIGATOR")).toBeVisible();
  await expect(page.getByRole("button", { name: "GLOBE", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("CLAIM & EVIDENCE RAIL")).toBeVisible();
  await expect(page.getByText("Moscú, Rusia").first()).toBeVisible();

  await page.getByRole("button", { name: "GRAPH", exact: true }).click();
  await expect(page.getByRole("button", { name: "GRAPH", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("Transmission graph")).toBeVisible();
  await expect(page.getByText("Distrito de Ramenki")).toBeVisible();

  const composer = page.getByLabel("Mensaje para AXIGNAL");
  await composer.fill("Muéstrame las contradicciones");
  await page.getByRole("button", { name: "Enviar" }).click();
  await expect(page.getByText(/tasas hipotecarias pueden reducir la demanda/i)).toBeVisible();
});

test("supports a first-class light theme", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Cambiar tema" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});
