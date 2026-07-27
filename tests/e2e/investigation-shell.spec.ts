import { expect, test } from "@playwright/test";

test("persists Navigator, lens, opportunity and evidence context", async ({ page }) => {
  await page.goto("/");

  const shell = page.locator("main.shell");
  await expect(page.getByText("AXIGNAL NAVIGATOR")).toBeVisible();
  await expect(shell).toHaveAttribute("data-context-version", "1");
  await expect(page.getByRole("button", { name: "GLOBE", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );

  const zil = page.getByRole("button", { name: /Zona ZIL ALTA/ });
  await zil.click();
  await expect(zil).toHaveAttribute("data-selected", "true");

  const composer = page.getByLabel("Mensaje para AXIGNAL");
  await composer.fill("Cambia al grafo y muéstrame las contradicciones");
  await page.getByRole("button", { name: "Enviar" }).click();

  await expect(page.getByRole("button", { name: "GRAPH", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByText("Transmission graph")).toBeVisible();
  await expect(page.getByText(/coste de financiación puede retrasar/i)).toBeVisible();
  await expect(page.getByText("Mortgage rate environment")).toBeVisible();
  await expect(page.getByText(/He aislado la contradicción material de Zona ZIL/i)).toBeVisible();

  const versionAfterCommand = Number(await shell.getAttribute("data-context-version"));
  expect(versionAfterCommand).toBeGreaterThan(2);

  await page.reload();
  await expect(page.getByRole("button", { name: "GRAPH", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByRole("button", { name: /Zona ZIL ALTA/ })).toHaveAttribute(
    "data-selected",
    "true",
  );
  await expect(page.getByText("Mortgage rate environment")).toBeVisible();
  await expect(shell).toHaveAttribute("data-context-version", String(versionAfterCommand));
});

test("persists theme, horizon and saved Investigation Trail", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Cambiar tema" }).click();
  await page.getByLabel("Horizonte").selectOption("36M");
  await page.getByRole("button", { name: "Guardar Trail" }).click();

  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByLabel("Horizonte")).toHaveValue("36M");
  await expect(page.getByRole("button", { name: "Trail guardado" })).toBeVisible();

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByLabel("Horizonte")).toHaveValue("36M");
  await expect(page.getByRole("button", { name: "Trail guardado" })).toBeVisible();
});

test("fails without mutating context when the Navigator route is unavailable", async ({ page }) => {
  await page.route("**/api/navigator/interpret", (route) => route.abort());
  await page.goto("/");

  const shell = page.locator("main.shell");
  await expect(shell).toHaveAttribute("data-context-version", "1");
  await page.getByLabel("Mensaje para AXIGNAL").fill("Cambia al grafo");
  await page.getByRole("button", { name: "Enviar" }).click();

  await expect(page.getByText(/No he modificado el contexto/i)).toBeVisible();
  await expect(shell).toHaveAttribute("data-context-version", "1");
  await expect(page.getByRole("button", { name: "GLOBE", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
});
