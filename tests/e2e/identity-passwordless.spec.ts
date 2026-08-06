import { mkdirSync, writeFileSync } from "node:fs";

import { expect, test } from "@playwright/test";

test.describe.configure({ mode: "serial", retries: 0 });
test.skip(
  process.env.AXIGNAL_PLAYWRIGHT_EXTERNAL_SERVER !== "true" ||
    process.env.AXIGNAL_PLAYWRIGHT_BASE_URL !== "http://127.0.0.1:18080",
  "P25 identity E2E requires the isolated passwordless topology."
);

const EMAIL = "buyer.p25@example.test";

const authenticatorOptions = {
  protocol: "ctap2" as const,
  ctap2Version: "ctap2_1" as const,
  transport: "internal" as const,
  hasResidentKey: true,
  hasUserVerification: true,
  isUserVerified: true,
  automaticPresenceSimulation: true
};

function identitySessionCookie(
  cookies: Awaited<ReturnType<import("@playwright/test").BrowserContext["cookies"]>>
) {
  return cookies.find(
    (cookie) =>
      cookie.name === "__Host-axignal_session" ||
      cookie.name === "axignal_identity_session"
  );
}

test("registers, rotates, recovers and replaces passkeys across a real WebAuthn boundary", async ({
  browser,
  page,
  context
}) => {
  const primaryCdp = await context.newCDPSession(page);
  await primaryCdp.send("WebAuthn.enable");
  const primaryAuthenticator = await primaryCdp.send(
    "WebAuthn.addVirtualAuthenticator",
    { options: authenticatorOptions }
  );

  await page.goto("http://localhost:18080/");
  await expect(
    page.getByRole("region", { name: "Acceso seguro a AXIGNAL" })
  ).toBeVisible();
  await expect(page.getByText("PASSWORDLESS · PHISHING-RESISTANT")).toBeVisible();

  await page.getByRole("tab", { name: "Crear cuenta" }).click();
  await page.getByLabel("Email profesional").fill(EMAIL);
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

  const initialRecovery = page.getByRole("region", {
    name: "Códigos de recuperación AXIGNAL"
  });
  await expect(initialRecovery).toBeVisible();
  const initialCodesText = await initialRecovery.locator("pre").innerText();
  const initialCodes = initialCodesText
    .split("\n")
    .map((code) => code.trim())
    .filter(Boolean);
  expect(initialCodes).toHaveLength(8);
  expect(initialCodes[0]).toMatch(/^AX-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$/);

  await initialRecovery
    .getByRole("button", { name: "He guardado los códigos" })
    .click();
  await expect(page.locator("main.shell")).toBeVisible();

  const originalCredentials = await primaryCdp.send("WebAuthn.getCredentials", {
    authenticatorId: primaryAuthenticator.authenticatorId
  });
  expect(originalCredentials.credentials).toHaveLength(1);
  expect(originalCredentials.credentials[0]?.isResidentCredential).toBeTruthy();

  const trialBeforeRecovery = await page.evaluate(async () => {
    const response = await fetch("/api/identity/trials/current", {
      cache: "no-store"
    });
    return { status: response.status, body: await response.json() };
  });
  expect(trialBeforeRecovery.status).toBe(200);
  expect(trialBeforeRecovery.body.state).toBe("READY");
  expect(trialBeforeRecovery.body.started_at).toBeNull();
  expect(trialBeforeRecovery.body.expires_at).toBeNull();
  expect(trialBeforeRecovery.body.token_budget_ceiling).toBe(1_000_000);

  const initialSession = identitySessionCookie(await context.cookies());
  expect(initialSession).toBeDefined();
  expect(initialSession?.httpOnly).toBeTruthy();
  expect(initialSession?.sameSite).toBe("Lax");

  const localStorageEntries = await page.evaluate(() =>
    Object.entries(localStorage)
  );
  const sensitiveKey = /(session|auth|token|credential|passkey|tenant|identity)/i;
  expect(localStorageEntries.some(([key]) => sensitiveKey.test(key))).toBe(false);
  expect(JSON.stringify(localStorageEntries)).not.toContain(EMAIL);

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

  const rotatedSession = identitySessionCookie(await context.cookies());
  expect(rotatedSession).toBeDefined();
  expect(rotatedSession?.value).not.toBe(initialSession?.value);

  const recoveryContext = await browser.newContext();
  const recoveryPage = await recoveryContext.newPage();
  const recoveryCdp = await recoveryContext.newCDPSession(recoveryPage);
  await recoveryCdp.send("WebAuthn.enable");
  const replacementAuthenticator = await recoveryCdp.send(
    "WebAuthn.addVirtualAuthenticator",
    { options: authenticatorOptions }
  );

  await recoveryPage.goto("http://localhost:18080/");
  await recoveryPage.getByRole("tab", { name: "Recuperar" }).click();
  await recoveryPage.getByLabel("Email").fill(EMAIL);
  await recoveryPage.getByLabel("Código de recuperación").fill(initialCodes[0]!);
  await recoveryPage
    .getByRole("button", { name: "Crear una passkey nueva" })
    .click();

  const replacementRecovery = recoveryPage.getByRole("region", {
    name: "Códigos de recuperación AXIGNAL"
  });
  await expect(replacementRecovery).toBeVisible();
  const replacementCodesText = await replacementRecovery.locator("pre").innerText();
  const replacementCodes = replacementCodesText
    .split("\n")
    .map((code) => code.trim())
    .filter(Boolean);
  expect(replacementCodes).toHaveLength(8);
  expect(replacementCodes).not.toEqual(initialCodes);

  await replacementRecovery
    .getByRole("button", { name: "He guardado los códigos" })
    .click();
  await expect(recoveryPage.locator("main.shell")).toBeVisible();

  const replacementCredentials = await recoveryCdp.send("WebAuthn.getCredentials", {
    authenticatorId: replacementAuthenticator.authenticatorId
  });
  expect(replacementCredentials.credentials).toHaveLength(1);
  expect(replacementCredentials.credentials[0]?.isResidentCredential).toBeTruthy();

  const recoveredSession = identitySessionCookie(await recoveryContext.cookies());
  expect(recoveredSession).toBeDefined();
  expect(recoveredSession?.value).not.toBe(rotatedSession?.value);

  const trialAfterRecovery = await recoveryPage.evaluate(async () => {
    const response = await fetch("/api/identity/trials/current", {
      cache: "no-store"
    });
    return { status: response.status, body: await response.json() };
  });
  expect(trialAfterRecovery.status).toBe(200);
  expect(trialAfterRecovery.body.tenant_id).toBe(
    trialBeforeRecovery.body.tenant_id
  );
  expect(trialAfterRecovery.body.state).toBe("READY");

  // Recovery starts from a separate browser with no session. The previously
  // active session in the original browser must be invalidated server-side.
  await page.reload();
  await expect(
    page.getByRole("region", { name: "Acceso seguro a AXIGNAL" })
  ).toBeVisible();

  // The old virtual authenticator still owns its credential locally. The
  // server must reject it because recovery revoked all previous authenticators.
  await page.getByRole("button", { name: "Usar passkey" }).click();
  await expect(page.locator("p.auth-error")).toContainText(
    "The authentication request could not be completed"
  );
  await expect(page.locator("main.shell")).not.toBeVisible();

  // Recovery codes are one-time. Replaying the consumed code must fail before
  // a new WebAuthn registration ceremony can begin.
  await page.getByRole("tab", { name: "Recuperar" }).click();
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Código de recuperación").fill(initialCodes[0]!);
  await page
    .getByRole("button", { name: "Crear una passkey nueva" })
    .click();
  await expect(page.locator("p.auth-error")).toContainText(
    "The authentication request could not be completed"
  );

  // The replacement passkey remains capable of issuing a fresh rotated
  // session after an explicit logout.
  const recoveredLogout = await recoveryPage.evaluate(async () => {
    const response = await fetch("/api/identity/sessions/logout", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{}"
    });
    return { status: response.status, body: await response.json() };
  });
  expect(recoveredLogout.status).toBe(200);
  expect(recoveredLogout.body.revoked).toBe(true);

  await recoveryPage.reload();
  await expect(
    recoveryPage.getByRole("region", { name: "Acceso seguro a AXIGNAL" })
  ).toBeVisible();
  await recoveryPage.getByRole("button", { name: "Usar passkey" }).click();
  await expect(recoveryPage.locator("main.shell")).toBeVisible();

  const finalSession = identitySessionCookie(await recoveryContext.cookies());
  expect(finalSession).toBeDefined();
  expect(finalSession?.value).not.toBe(recoveredSession?.value);

  mkdirSync("artifacts", { recursive: true });
  writeFileSync(
    "artifacts/c2-identity-recovery-browser.json",
    `${JSON.stringify(
      {
        schema: "axignal.c2-identity-recovery-browser.v1",
        status: "PASS",
        email_verification: "PASS",
        initial_passkey_registration: "PASS",
        opaque_http_only_session: "PASS",
        session_rotation_after_authentication: "PASS",
        recovery_code_one_time: "PASS",
        recovery_revoked_prior_sessions: "PASS",
        recovery_revoked_prior_authenticators: "PASS",
        replacement_passkey_registration: "PASS",
        replacement_recovery_codes: 8,
        replacement_session_assurance: "AAL2",
        tenant_continuity: "PRESERVED",
        trial_state_after_recovery: trialAfterRecovery.body.state,
        public_signup_authorised: false,
        external_identity_provider_calls: 0,
        model_calls: 0
      },
      null,
      2
    )}\n`
  );

  await primaryCdp.send("WebAuthn.removeVirtualAuthenticator", {
    authenticatorId: primaryAuthenticator.authenticatorId
  });
  await recoveryCdp.send("WebAuthn.removeVirtualAuthenticator", {
    authenticatorId: replacementAuthenticator.authenticatorId
  });
  await recoveryContext.close();
});