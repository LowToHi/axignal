import {
  expect,
  test,
  type BrowserContext,
  type Page
} from "@playwright/test";

test.describe.configure({ mode: "serial", retries: 0 });
test.skip(
  process.env.AXIGNAL_PLAYWRIGHT_EXTERNAL_SERVER !== "true" ||
    process.env.AXIGNAL_PLAYWRIGHT_BASE_URL !== "http://127.0.0.1:18080",
  "Seat governance E2E requires the isolated billing and seat topology."
);

function identitySessionCookie(
  cookies: Awaited<ReturnType<BrowserContext["cookies"]>>
) {
  return cookies.find(
    (cookie) =>
      cookie.name === "__Host-axignal_session" ||
      cookie.name === "axignal_identity_session"
  );
}

async function expectPersistentWorkspace(page: Page) {
  await expect(
    page.getByRole("heading", { name: "Persistent opportunity intelligence" })
  ).toBeVisible();
  await expect(page.locator('main[data-adapter="persistent-real"]')).toBeVisible();
}

async function expectAuthenticatedCommercialState(page: Page) {
  await expect(
    page.getByRole("button", { name: "PLAN · Sin plan", exact: true })
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Persistent opportunity intelligence" })
  ).not.toBeVisible();
  await expect(page.locator('main[data-adapter="persistent-real"]')).not.toBeVisible();
}

async function loginWithPasskey(page: Page, context: BrowserContext) {
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
  const legacyLogin = await page.evaluate(async () => {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        email: "pilot@example.test",
        password: "pilot-password"
      })
    });
    return { status: response.status, body: await response.json() };
  });
  expect(legacyLogin).toEqual({
    status: 404,
    body: {
      error: "request_rejected",
      code: "legacy_password_login_disabled"
    }
  });

  await expect(
    page.getByRole("region", { name: "Acceso seguro a AXIGNAL" })
  ).toBeVisible();
  await page.getByRole("tab", { name: "Crear cuenta" }).click();
  await page.getByLabel("Email profesional").fill("pilot@example.test");
  await page.getByRole("button", { name: "Continuar" }).click();
  await expect(
    page.getByText(
      "Si la dirección puede utilizarse, recibirás un enlace de verificación."
    )
  ).toBeVisible();
  await page
    .getByRole("button", {
      name: "Verificar email de prueba y crear passkey"
    })
    .click();

  const recovery = page.getByRole("region", {
    name: "Códigos de recuperación AXIGNAL"
  });
  await expect(recovery).toBeVisible();
  const codes = await recovery.locator("pre").innerText();
  expect(codes.split("\n")).toHaveLength(8);
  await recovery.getByRole("button", { name: "He guardado los códigos" }).click();
  await expectAuthenticatedCommercialState(page);

  const credentials = await cdp.send("WebAuthn.getCredentials", {
    authenticatorId: authenticator.authenticatorId
  });
  expect(credentials.credentials).toHaveLength(1);
  expect(credentials.credentials[0]?.isResidentCredential).toBeTruthy();

  const sessionCookie = identitySessionCookie(await context.cookies());
  expect(sessionCookie).toBeDefined();
  expect(sessionCookie?.httpOnly).toBeTruthy();
  expect(sessionCookie?.sameSite).toBe("Lax");

  return { cdp, authenticatorId: authenticator.authenticatorId };
}

async function confirmCheckout(page: Page) {
  await page.getByRole("button", { name: /PLAN ·/ }).click();
  const panel = page.getByRole("complementary", { name: "Plan y facturación" });
  await panel.getByText(/Confirmo que estoy seleccionando explícitamente/).click();
  await panel.getByRole("button", { name: "Seleccionar Professional" }).click();
  await expect(page).toHaveURL(/\/billing\/test-checkout/);
  await page.getByRole("button", { name: "Confirmar pago de prueba" }).click();
  await expect(page).toHaveURL(/billing=success/);
  await expectPersistentWorkspace(page);
  await expect(page.getByText(/Plan: Professional · acceso ACTIVE/)).toBeVisible();
  await page
    .getByRole("complementary", { name: "Plan y facturación" })
    .getByRole("button", { name: "Cerrar" })
    .click();
}

async function confirmUpgrade(page: Page) {
  const billing = page.getByRole("complementary", { name: "Plan y facturación" });
  await billing.getByRole("button", { name: "Upgrade explícito a Team" }).click();
  await expect(billing.getByText("UPGRADE_PENDING", { exact: true })).toBeVisible();

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

test("governs seats through a passwordless AAL2 session", async ({
  page,
  context
}) => {
  const passwordless = await loginWithPasskey(page, context);
  try {
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

    const revokeButtons = seatPanel.getByRole("button", {
      name: "Revoke invitation"
    });
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
  } finally {
    await passwordless.cdp.send("WebAuthn.removeVirtualAuthenticator", {
      authenticatorId: passwordless.authenticatorId
    });
  }
});
