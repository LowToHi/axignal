import { expect, test } from "@playwright/test";

const demoPath = "/demo";

test("persists Navigator, lens, opportunity and evidence context", async ({ page }) => {
  await page.goto(demoPath);

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
  await page.goto(demoPath);

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

test("creates a traceable ResearchRun without admitting canonical claims", async ({ page }) => {
  await page.goto(demoPath);

  const shell = page.locator("main.shell");
  await page.getByRole("button", { name: "Investigar oportunidad" }).click();

  await expect(page.getByRole("region", { name: "ResearchRun" })).toBeVisible();
  await expect(page.getByText("ADMISSION_QUEUED", { exact: true })).toBeVisible();
  await expect(page.getByText("PROPUESTA · NO ADMITIDA")).toBeVisible();
  await expect(page.getByText("OFFICIAL_API", { exact: true })).toBeVisible();
  await expect(page.getByText("AUTHORISED_BROWSER", { exact: true })).toBeVisible();
  await expect(page.getByText(/IGNORED_INJECTION/)).toBeVisible();
  await expect(page.getByText(/canonical_claim_id: null/).first()).toBeVisible();
  await expect(page.getByText("UNKNOWN", { exact: true })).toBeVisible();
  await expect(page.getByText(/Ningún resultado ha sido admitido como claim canónico/i)).toBeVisible();

  const versionAfterResearch = Number(await shell.getAttribute("data-context-version"));
  expect(versionAfterResearch).toBeGreaterThan(1);

  await page.reload();
  await expect(page.getByText("PROPUESTA · NO ADMITIDA")).toBeVisible();
  await expect(page.getByText("ADMISSION_QUEUED", { exact: true })).toBeVisible();
  await expect(shell).toHaveAttribute("data-context-version", String(versionAfterResearch));
});

test("uses tenant-private fixture only after explicit authorisation", async ({ page }) => {
  await page.goto(demoPath);

  await page.getByLabel("Memoria privada sintética para ResearchRun").check();
  await page.getByRole("button", { name: "Investigar oportunidad" }).click();

  const privateSource = page.getByText("Tenant-private note fixture");
  await expect(privateSource).toBeVisible();
  await expect(page.getByText(/Usada solo como contexto privado/i)).toBeVisible();
  await expect(page.getByText(/memoria privada usada/i)).toBeVisible();
  await expect(page.getByText(/canonical_claim_id: null/).first()).toBeVisible();

  await page.reload();
  await expect(page.getByLabel("Memoria privada sintética para ResearchRun")).toBeChecked();
  await expect(privateSource).toBeVisible();
});

test("fails without mutating context when the Navigator route is unavailable", async ({ page }) => {
  await page.route("**/api/navigator/interpret", (route) => route.abort());
  await page.goto(demoPath);

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

test("fails closed when the ResearchRun route is unavailable", async ({ page }) => {
  await page.route("**/api/research/runs", (route) => route.abort());
  await page.goto(demoPath);

  const shell = page.locator("main.shell");
  await expect(shell).toHaveAttribute("data-context-version", "1");
  await page.getByRole("button", { name: "Investigar oportunidad" }).click();

  await expect(page.getByText(/No he modificado el contexto/i)).toBeVisible();
  await expect(shell).toHaveAttribute("data-context-version", "1");
  await expect(page.getByText("NO INICIADO")).toBeVisible();
});
