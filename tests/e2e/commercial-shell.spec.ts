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
  "Commercial billing E2E requires the isolated deterministic-provider topology."
);

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
  await expect(page.locator("main.shell")).toBeVisible();

  return { cdp, authenticatorId: authenticator.authenticatorId };
}

async function emitProviderEvent(
  page: Page,
  action: "CONFIRM_UPGRADE" | "CONFIRM_CANCELLATION" | "ROLLBACK"
) {
  const result = await page.evaluate(async (requestedAction) => {
    const response = await fetch("/api/billing/test/provider-event", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: requestedAction })
    });
    return {
      ok: response.ok,
      status: response.status,
      text: await response.text()
    };
  }, action);
  expect(result.ok, `${result.status}: ${result.text}`).toBeTruthy();
  const refresh = page.getByRole("button", { name: "Actualizar" });
  if (await refresh.isVisible().catch(() => false)) await refresh.click();
}

test("executes the authenticated commercial shell without external Stripe", async ({
  page,
  context
}) => {
  const passwordless = await loginWithPasskey(page, context);
  try {
    const launcher = page.getByRole("button", { name: /PLAN ·/ });
    await launcher.click();
    const panel = page.getByRole("complementary", {
      name: "Plan y facturación"
    });
    await expect(panel).toBeVisible();
    await expect(panel.getByText("NO_PLAN", { exact: true })).toBeVisible();
    await panel
      .getByText(/Confirmo que estoy seleccionando explícitamente/)
      .click();

    const chooseProfessional = panel.getByRole("button", {
      name: "Seleccionar Professional"
    });
    await expect(chooseProfessional).toBeEnabled();
    await chooseProfessional.click();

    await expect(page).toHaveURL(/\/billing\/test-checkout/);
    const checkoutUrl = page.url();
    await expect(page.getByText("Confirmación de pago de prueba")).toBeVisible();
    await expect(
      page.getByText(/Cargar esta página o volver a AXIGNAL no concede acceso/)
    ).toBeVisible();

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
    await expect(
      page.getByText("CANCEL_AT_PERIOD_END", { exact: true })
    ).toBeVisible();
    await expect(page.getByText(/Cancelación programada/)).toBeVisible();
    await expect(page.getByText(/acceso ACTIVE/)).toBeVisible();

    await emitProviderEvent(page, "CONFIRM_CANCELLATION");
    await expect(page.getByText("CANCELLED", { exact: true }).first()).toBeVisible();
    await expect(page.getByText(/acceso CANCELLED/)).toBeVisible();

    await emitProviderEvent(page, "ROLLBACK");
    await expect(page.getByText("ROLLED_BACK", { exact: true })).toBeVisible();
    await expect(
      page.getByText("PAID_LIFECYCLE_ROLLED_BACK", { exact: true })
    ).toBeVisible();
    await expect(page.getByText(/Stripe sandbox externo verificado: no/)).toBeVisible();

    const persistedSummaryPromise = page.waitForResponse(
      (response) =>
        response.url().includes("/api/billing/summary") &&
        response.status() === 200
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
  } finally {
    await passwordless.cdp.send("WebAuthn.removeVirtualAuthenticator", {
      authenticatorId: passwordless.authenticatorId
    });
  }
});
