import { expect, test } from "@playwright/test";

const LOCAL_PREFIX = "axignal:axent:local-history:v1:";
const LEGACY_PREFIX = "axignal:axent:history:v3:";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(({ localPrefix, legacyPrefix }) => {
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith(localPrefix) || key.startsWith(legacyPrefix)) {
        localStorage.removeItem(key);
      }
    }
  }, { localPrefix: LOCAL_PREFIX, legacyPrefix: LEGACY_PREFIX });
});

test("turns the welcome state into a focused conversation", async ({ page }) => {
  await page.goto("/axent");

  const composer = page.getByRole("textbox", {
    name: "Ask AXENT anything about AXIGNAL",
    exact: true,
  });
  await composer.fill("How does AXIGNAL handle evidence?");
  await composer.press("Enter");

  await expect(page.locator("h1")).toHaveCount(0);
  await expect(page.locator('[aria-label="Starter questions"]')).toHaveCount(0);
  await expect(page.getByRole("log", { name: "AXENT conversation" })).toContainText(
    "Start with the evidence rail",
  );
  await expect(page.getByRole("complementary", { name: "Chat history" })).toBeVisible();
  await expect(page.getByRole("button", { name: "New chat", exact: true })).toBeVisible();
  await expect(page.getByText("Not synced to AXIGNAL servers.")).toBeVisible();
  await expect(page.getByText("Expires after 30 days.")).toBeVisible();
});

test("persists a conversation in identity-scoped bounded history", async ({ page }) => {
  const bootstrapResponse = await page.request.get(
    "/api/subscriber-workspace/bootstrap"
  );
  expect(bootstrapResponse.status()).toBe(200);
  const bootstrap = (await bootstrapResponse.json()) as {
    tenant: { id: string };
    identity: { id: string };
  };

  await page.goto("/axent");
  const composer = page.getByRole("textbox", {
    name: "Ask AXENT anything about AXIGNAL",
    exact: true,
  });
  await composer.fill("Show AXIGNAL opportunities");
  await composer.press("Enter");
  await expect(page.locator('[aria-label="Saved conversations"] article')).toHaveCount(1);

  const persisted = await page.evaluate(
    ({ prefix, tenantId, identityId }) => {
      const key = `${prefix}${tenantId}:${identityId}`;
      return { key, raw: localStorage.getItem(key) };
    },
    {
      prefix: LOCAL_PREFIX,
      tenantId: bootstrap.tenant.id,
      identityId: bootstrap.identity.id,
    },
  );
  expect(persisted.raw).not.toBeNull();
  const envelope = JSON.parse(persisted.raw ?? "null") as {
    schema_version: string;
    tenant_id: string;
    identity_id: string;
    saved_at: string;
    expires_at: string;
    conversations: unknown[];
  };
  expect(envelope).toMatchObject({
    schema_version: "axignal.axent-local-history/v1",
    tenant_id: bootstrap.tenant.id,
    identity_id: bootstrap.identity.id,
  });
  expect(envelope.conversations).toHaveLength(1);
  expect(Date.parse(envelope.expires_at) - Date.parse(envelope.saved_at)).toBe(
    30 * 24 * 60 * 60 * 1000,
  );
  expect(
    await page.evaluate(
      ({ prefix, tenantId }) => localStorage.getItem(`${prefix}${tenantId}`),
      { prefix: LEGACY_PREFIX, tenantId: bootstrap.tenant.id },
    ),
  ).toBeNull();
});

test("persists a conversation in history and lets the subscriber start another", async ({
  page,
}) => {
  await page.goto("/axent");

  const composer = page.getByRole("textbox", {
    name: "Ask AXENT anything about AXIGNAL",
    exact: true,
  });
  await composer.fill("Show AXIGNAL opportunities");
  await composer.press("Enter");

  const savedConversation = page.locator('[aria-label="Saved conversations"] article').first();
  await expect(savedConversation).toHaveCount(1);
  await page.getByRole("button", { name: "New chat", exact: true }).click();

  await expect(page.getByRole("heading", { name: "What are you investigating today?" })).toBeVisible();
  await expect(savedConversation).toHaveCount(1);

  await savedConversation.locator("button").first().click();
  await expect(page.getByRole("log", { name: "AXENT conversation" })).toContainText(
    "Show AXIGNAL opportunities",
  );
});

test("reuses, downloads, exports and deletes a saved conversation", async ({ page }) => {
  await page.goto("/axent");

  const composer = page.getByRole("textbox", {
    name: "Ask AXENT anything about AXIGNAL",
    exact: true,
  });
  await composer.fill("Explain the evidence model");
  await composer.press("Enter");

  const savedConversation = page.locator('[aria-label="Saved conversations"] article').first();
  await expect(savedConversation).toBeVisible();

  await savedConversation.getByRole("button", { name: /Use .* as context/ }).click();
  await expect(page.locator('[role="status"]').filter({ hasText: "Using context from Explain the evidence model" })).toBeVisible();

  const requestPromise = page.waitForRequest((request) => request.url().endsWith("/api/subscriber-workspace/assistant") && request.method() === "POST");
  await composer.fill("What should I review next?");
  await composer.press("Enter");
  const request = await requestPromise;
  const requestBody = request.postDataJSON() as { history?: Array<{ content: string }> };
  expect(requestBody.history?.some((item) => item.content.includes("Explain the evidence model"))).toBe(true);
  await expect(composer).toBeEnabled();
  await expect(page.locator('[aria-label="Saved conversations"] article')).toHaveCount(2);

  const activeConversation = page.locator('[aria-label="Saved conversations"] article').first();
  const textDownload = page.waitForEvent("download");
  await activeConversation.getByRole("button", { name: /Download/ }).click();
  expect((await textDownload).suggestedFilename()).toMatch(/\.txt$/);

  const pdfDownload = page.waitForEvent("download");
  await activeConversation.getByRole("button", { name: /Export .* as PDF/ }).click();
  expect((await pdfDownload).suggestedFilename()).toMatch(/\.pdf$/);

  const dialogPromise = page.waitForEvent("dialog").then((dialog) => dialog.accept());
  await activeConversation.getByRole("button", { name: /Delete/ }).click();
  await dialogPromise;
  await expect(page.locator('[aria-label="Saved conversations"] article')).toHaveCount(1);
});

test("purges AXENT local history on logout without deleting unrelated storage", async ({
  page,
}) => {
  await page.goto("/axent");
  const language = page.locator("header select");
  await language.selectOption("en");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");

  await page.evaluate(({ localPrefix, legacyPrefix }) => {
    localStorage.setItem(`${localPrefix}tenant:user`, "current");
    localStorage.setItem(`${legacyPrefix}tenant`, "legacy");
    localStorage.setItem("axignal:unrelated", "keep");
  }, { localPrefix: LOCAL_PREFIX, legacyPrefix: LEGACY_PREFIX });

  await page.getByRole("button", { name: /Account menu for/ }).click();
  const logoutResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/auth/logout") &&
      response.request().method() === "POST",
  );
  await page.getByRole("menuitem", {
    name: "Sign out and clear local AXENT history",
  }).click();
  expect((await logoutResponse).status()).toBe(200);
  await page.waitForURL("**/", { waitUntil: "domcontentloaded" });

  const storageState = await page.context().storageState();
  const originStorage = storageState.origins.find(
    (origin) => origin.origin === new URL(page.url()).origin,
  )?.localStorage ?? [];
  const axentKeys = originStorage
    .map((entry) => entry.name)
    .filter(
      (key) => key.startsWith(LOCAL_PREFIX) || key.startsWith(LEGACY_PREFIX),
    );
  const unrelated = originStorage.find(
    (entry) => entry.name === "axignal:unrelated",
  )?.value ?? null;

  expect(axentKeys).toEqual([]);
  expect(unrelated).toBe("keep");
});
