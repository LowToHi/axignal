import {
  expect,
  test,
  type BrowserContext,
  type Page
} from "@playwright/test";

test.describe.configure({ mode: "serial", retries: 0 });
test.setTimeout(240_000);
test.skip(
  process.env.AXIGNAL_PLAYWRIGHT_EXTERNAL_SERVER !== "true" ||
    process.env.AXIGNAL_PLAYWRIGHT_BASE_URL !== "http://127.0.0.1:18080",
  "The live subscriber E2E requires the isolated governed topology."
);

async function registerPasskey(page: Page, context: BrowserContext) {
  await page.setExtraHTTPHeaders({
    origin: "http://localhost:18080",
    "sec-fetch-site": "same-origin"
  });
  const cdp = await context.newCDPSession(page);
  await cdp.send("WebAuthn.enable");
  const authenticator = await cdp.send("WebAuthn.addVirtualAuthenticator", {
    options: {
      protocol: "ctap2",
      ctap2Version: "ctap2_1",
      transport: "internal",
      hasResidentKey: true,
      hasUserVerification: true,
      isUserVerified: true,
      automaticPresenceSimulation: true
    }
  });

  await page.goto("http://localhost:18080/");
  await expect(
    page.getByRole("region", { name: "Acceso seguro a AXIGNAL" })
  ).toBeVisible();
  await page.getByRole("tab", { name: "Crear cuenta" }).click();
  await page.getByLabel("Email profesional").fill("pilot@example.test");
  await page.getByRole("button", { name: "Continuar" }).click();
  await page
    .getByRole("button", {
      name: "Verificar email de prueba y crear passkey"
    })
    .click();
  const recovery = page.getByRole("region", {
    name: "Códigos de recuperación AXIGNAL"
  });
  await expect(recovery).toBeVisible();
  await recovery.getByRole("button", { name: "He guardado los códigos" }).click();
  await expect(page.getByRole("button", { name: /^PLAN ·/ })).toBeVisible({
    timeout: 15_000
  });

  return { cdp, authenticatorId: authenticator.authenticatorId };
}

async function activateProfessional(page: Page) {
  await page.getByRole("button", { name: /^PLAN ·/ }).click();
  const panel = page.getByRole("complementary", {
    name: "Plan y facturación"
  });
  await expect(panel).toBeVisible();
  await panel
    .getByText(/Confirmo que estoy seleccionando explícitamente/)
    .click();
  await panel
    .getByRole("button", { name: "Seleccionar Professional" })
    .click();
  await expect(page).toHaveURL(/\/billing\/test-checkout/);
  await page.getByRole("button", { name: "Confirmar pago de prueba" }).click();
  await expect(page).toHaveURL(/billing=success/);
  await expect(page.getByText(/Plan: Professional · acceso ACTIVE/)).toBeVisible({
    timeout: 15_000
  });
  await panel.getByRole("button", { name: "Cerrar" }).click();
  await expect(panel).toBeHidden();
}

async function initialiseOwnerSeat(page: Page) {
  await expect(page.getByText("seat_membership_required")).toBeVisible();
  const launcher = page.getByRole("button", { name: "SEATS · SETUP" });
  await expect(launcher).toBeVisible({ timeout: 15_000 });
  await launcher.click();
  const panel = page.getByRole("complementary", {
    name: "Organisation seats and members"
  });
  await expect(panel).toBeVisible();
  await panel.getByRole("button", { name: "Initialise owner seat" }).click();
  await expect(page.getByRole("button", { name: "SEATS · 1/3" })).toBeVisible({
    timeout: 15_000
  });
  await panel.getByRole("button", { name: "Close" }).click();
  await expect(panel).toBeHidden();
  await page.reload({ waitUntil: "domcontentloaded", timeout: 45_000 });
}

test("executes the no-fixture subscriber happy path", async ({ page, context }) => {
  const passkey = await registerPasskey(page, context);
  try {
    await activateProfessional(page);
    await initialiseOwnerSeat(page);

    const live = page.locator(
      '[data-e2e-no-fixtures="true"][data-adapter="persistent-real"]'
    );
    await expect(live).toBeVisible({ timeout: 20_000 });
    await expect(live).toContainText("PROFESSIONAL_MONTHLY");
    await expect(live).toContainText("ACTIVE");
    await expect(live).not.toContainText("ENGINEERING FIXTURE");
    await expect(live.locator('[id^="axfx_"]')).toHaveCount(0);

    const question =
      "Find active European public procurement opportunities for governed data platforms.";
    await page.getByLabel("Research question").fill(question);
    await page.getByRole("button", { name: "Start ResearchRun" }).click();
    await expect(page.getByText("COMPLETED", { exact: true })).toBeVisible({
      timeout: 120_000
    });

    const investigation = page.getByRole("region", {
      name: "InvestigationContext"
    });
    await expect(investigation).toContainText("src_ted_search_api_v3");
    await expect(investigation.getByText("Persistent evidence")).toBeVisible();
    await expect(
      investigation.getByText("Claims and deterministic admission")
    ).toBeVisible();
    await expect(investigation.getByText("Persistent dossier")).toBeVisible();

    await page
      .getByRole("button", { name: "Open persistent workspace" })
      .click();
    const operations = page.getByRole("region", {
      name: "Persistent workspace, document and export"
    });
    await expect(operations).toBeVisible();

    await page.getByLabel("Title").fill("Pursuit note");
    await page
      .getByLabel("Body")
      .fill(
        "Proceed to internal qualification using the admitted dossier and source evidence."
      );
    await page.getByRole("button", { name: "Persist document" }).click();
    await expect(page.getByText("Pursuit note", { exact: true })).toBeVisible();
    await expect(page.getByText("DOCUMENT_CREATED", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Create Markdown export" }).click();
    const download = page.getByRole("link", {
      name: "Download verified Markdown export"
    });
    await expect(download).toBeVisible();
    const href = await download.getAttribute("href");
    expect(href).toBeTruthy();
    const response = await page.request.get(href as string);
    expect(response.ok()).toBeTruthy();
    expect(response.headers()["content-type"]).toContain("text/markdown");
    const markdown = await response.text();
    expect(markdown).toContain("# ");
    expect(markdown).toContain("Pursuit note");
    expect(markdown).toContain("src_ted_search_api_v3");

    await page.reload({ waitUntil: "domcontentloaded", timeout: 45_000 });
    await expect(
      page.locator(
        '[data-e2e-no-fixtures="true"][data-adapter="persistent-real"]'
      )
    ).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(question, { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Pursuit note", { exact: true })).toBeVisible();
    await expect(page.getByText("EXPORT_CREATED", { exact: true })).toBeVisible();
  } finally {
    await passkey.cdp.send("WebAuthn.removeVirtualAuthenticator", {
      authenticatorId: passkey.authenticatorId
    });
  }
});
