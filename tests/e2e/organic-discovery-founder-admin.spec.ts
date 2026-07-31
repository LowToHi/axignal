import { expect, test } from "@playwright/test";

test.describe.configure({ mode: "serial", retries: 0 });
test.skip(
  process.env.AXIGNAL_PLAYWRIGHT_EXTERNAL_SERVER !== "true" ||
    process.env.AXIGNAL_PLAYWRIGHT_BASE_URL !== "http://127.0.0.1:18080",
  "P26 E2E requires the isolated organic-discovery topology."
);

test("publishes only admitted intelligence and exposes a governed founder OS", async ({
  page,
  context
}) => {
  test.setTimeout(120_000);
  const publicUrl = "http://localhost:18080/tenders/germany/cybersecurity";
  const publicResponse = await page.goto(publicUrl);
  expect(publicResponse?.status()).toBe(200);
  await expect(
    page.getByRole("heading", {
      name: "Cybersecurity government tenders in Germany"
    })
  ).toBeVisible();
  await expect(page.getByText("VERIFIABLE SNAPSHOT")).toBeVisible();
  await expect(page.getByText("28").first()).toBeVisible();
  await expect(
    page.getByText("Dataset ≠ indexable page · Citation ≠ endorsement")
  ).toBeVisible();
  const structuredData = await page
    .locator('script[type="application/ld+json"]')
    .textContent();
  expect(structuredData).toContain('"@type":"CollectionPage"');
  expect(structuredData).toContain('"@type":"Dataset"');
  expect(structuredData).toContain('"measurementTechnique"');
  expect(structuredData).toContain('"isBasedOn"');

  const rejected = await page.goto(
    "http://localhost:18080/tenders/germany/synthetic-cybersecurity"
  );
  expect(rejected?.status()).toBe(404);

  const robots = await page.request.get("http://localhost:18080/robots.txt");
  expect(robots.status()).toBe(200);
  const robotsBody = await robots.text();
  expect(robotsBody).toContain("User-Agent: OAI-SearchBot");
  expect(robotsBody).toContain("User-Agent: GPTBot");
  expect(robotsBody).toContain("Disallow: /admin/");

  const sitemap = await page.request.get("http://localhost:18080/sitemap.xml");
  expect(sitemap.status()).toBe(200);
  const sitemapBody = await sitemap.text();
  expect(sitemapBody).toContain("/tenders/germany/cybersecurity");
  expect(sitemapBody).not.toContain("synthetic-cybersecurity");

  await page.goto(publicUrl);
  await expect(page.getByLabel("Professional email")).toBeVisible();
  const alertResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/public/tender-alerts") &&
      response.request().method() === "POST"
  );
  await page
    .getByLabel("Professional email")
    .fill("browser.p26@example.test");
  await page.getByLabel("Cadence").selectOption("DAILY");
  await page.getByRole("button", { name: "Create tender alert" }).click();
  const alertResponse = await alertResponsePromise;
  expect(alertResponse.status()).toBe(202);
  const alertBody = (await alertResponse.json()) as Record<string, unknown>;
  expect(alertBody.trial_created).toBe(false);
  expect(alertBody.tenant_created).toBe(false);
  expect(alertBody.state).toBe("PENDING_CONFIRMATION");
  expect(alertBody.test_confirmation_token).toEqual(expect.any(String));
  await expect(
    page.getByText("Check your email to confirm the alert.")
  ).toBeVisible();

  const token = String(alertBody.test_confirmation_token);
  await page.goto(
    `http://localhost:18080/alerts/confirm?token=${encodeURIComponent(token)}`
  );
  await page.getByRole("button", { name: "Confirm tender alert" }).click();
  await expect(
    page.getByRole("heading", { name: "Your tender alert is active." })
  ).toBeVisible();

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
  await page.getByLabel("Email profesional").fill("founder.p26@example.test");
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
  await recovery
    .getByRole("button", { name: "He guardado los códigos" })
    .click();
  await expect(page.locator("main.shell")).toBeVisible();

  await page.goto("http://localhost:18080/admin");
  await expect(page.getByTestId("founder-bootstrap")).toBeVisible();
  await page
    .getByRole("button", { name: "Provision test founder principal" })
    .click();
  await expect(page.getByTestId("founder-admin-dashboard")).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Founder administration" })
  ).toBeVisible();
  await expect(
    page.getByText("Generated does not mean indexable.")
  ).toBeVisible();

  await page.getByRole("button", { name: "Organic SEO" }).click();
  await expect(
    page.getByRole("heading", { name: "Programmatic SEO governance" })
  ).toBeVisible();
  await expect(
    page.getByText("Cybersecurity government tenders in Germany")
  ).toBeVisible();
  await expect(
    page.getByText("Synthetic Germany cybersecurity tenders")
  ).toBeVisible();

  await page.getByRole("button", { name: "CRM" }).click();
  await expect(
    page.getByRole("heading", { name: "CRM contacts" })
  ).toBeVisible();
  await expect(page.getByText("browser.p26@example.test")).toBeVisible();

  await page.getByRole("button", { name: "Tender Alerts" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Tender alerts",
      level: 3,
      exact: true
    })
  ).toBeVisible();
  await expect(page.getByText("ACTIVE").first()).toBeVisible();

  await cdp.send("WebAuthn.removeVirtualAuthenticator", {
    authenticatorId: authenticator.authenticatorId
  });
});
