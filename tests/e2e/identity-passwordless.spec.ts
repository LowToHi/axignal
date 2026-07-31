import { expect, test } from "@playwright/test";

test.describe.configure({ mode: "serial", retries: 0 });
test.skip(
  process.env.AXIGNAL_PLAYWRIGHT_EXTERNAL_SERVER !== "true" ||
    process.env.AXIGNAL_PLAYWRIGHT_BASE_URL !== "http://localhost:18080",
  "P25 identity E2E requires the isolated passwordless topology."
);

test("registers, revokes and reauthenticates with a real WebAuthn boundary", async ({
  page,
  context
}) => {
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

  await page.goto("/");
  await expect(
    page.getByRole("region", { name: "Acceso seguro a AXIGNAL" })
  ).toBeVisible();
  await expect(page.getByText("PASSWORDLESS · PHISHING-RESISTANT")).toBeVisible();

  await page.getByRole("tab", { name: "Crear cuenta" }).click();
  await page.getByLabel("Email profesional").fill("buyer.p25@example.test");
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
  expect(codes).toMatch(/^AX-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}/m);

  await recovery.getByRole("button", { name: "He guardado los códigos" }).click();
  await expect(page.locator("main.shell")).toBeVisible();

  const credentials = await cdp.send("WebAuthn.getCredentials", {
    authenticatorId: authenticator.authenticatorId
  });
  expect(credentials.credentials).toHaveLength(1);
  expect(credentials.credentials[0]?.isResidentCredential).toBeTruthy();

  const trial = await page.evaluate(async () => {
    const response = await fetch("/api/identity/trials/current", {
      cache: "no-store"
    });
    return { status: response.status, body: await response.json() };
  });
  expect(trial.status).toBe(200);
  expect(trial.body.state).toBe("READY");
  expect(trial.body.started_at).toBeNull();
  expect(trial.body.expires_at).toBeNull();
  expect(trial.body.token_budget_ceiling).toBe(1_000_000);

  const cookies = await context.cookies();
  const sessionCookie = cookies.find(
    (cookie) => cookie.name === "axignal_identity_session"
  );
  expect(sessionCookie).toBeDefined();
  expect(sessionCookie?.httpOnly).toBeTruthy();
  expect(sessionCookie?.sameSite).toBe("Lax");
  expect(await page.evaluate(() => localStorage.length)).toBe(0);

  const logout = await page.evaluate(async () => {
    const response = await fetch("/api/identity/sessions/logout", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{}"
    });
    return { status: response.status, body: await response.json() };
  });
  expect(logout.status).toBe(200);
  expect(logout.body.revoked).toBe(true);

  await page.reload();
  await expect(
    page.getByRole("region", { name: "Acceso seguro a AXIGNAL" })
  ).toBeVisible();
  await page.getByRole("button", { name: "Usar passkey" }).click();
  await expect(page.locator("main.shell")).toBeVisible();

  const renewed = (await context.cookies()).find(
    (cookie) => cookie.name === "axignal_identity_session"
  );
  expect(renewed).toBeDefined();
  expect(renewed?.value).not.toBe(sessionCookie?.value);

  await cdp.send("WebAuthn.removeVirtualAuthenticator", {
    authenticatorId: authenticator.authenticatorId
  });
});
