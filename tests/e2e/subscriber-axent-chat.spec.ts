import { expect, test, type Page } from "@playwright/test";

import { installAxentPersistenceStub } from "./helpers/axent-persistence-stub";

const COMPOSER_NAME = "Ask AXENT anything about AXIGNAL";

async function axentLocalHistoryKeys(page: Page): Promise<string[]> {
  return page.evaluate(() =>
    Object.keys(localStorage).filter(
      (key) => key.startsWith("axignal:axent:local-history:") || key.startsWith("axignal:axent:history:"),
    ),
  );
}

test("turns the welcome state into a focused server-persistent conversation", async ({ page }) => {
  await installAxentPersistenceStub(page);
  await page.goto("/axent");

  const composer = page.getByRole("textbox", { name: COMPOSER_NAME, exact: true });
  await composer.fill("How does AXIGNAL handle evidence?");
  await composer.press("Enter");

  await expect(page.locator("h1")).toHaveCount(0);
  await expect(page.getByRole("log", { name: "AXENT conversation" })).toContainText(
    "Start with the evidence rail",
  );
  await expect(page.getByRole("complementary", { name: "Chat history" })).toBeVisible();
  await expect(page.getByRole("button", { name: "New chat", exact: true })).toBeVisible();
  await expect(page.getByText("Server persistent")).toBeVisible();
});

test("persists through the identity-scoped BFF without browser-local authority", async ({ page }) => {
  const stub = await installAxentPersistenceStub(page);
  await page.goto("/axent");

  const composer = page.getByRole("textbox", { name: COMPOSER_NAME, exact: true });
  await composer.fill("Show AXIGNAL opportunities");
  await composer.press("Enter");

  await expect(page.locator('[aria-label="Saved conversations"] article')).toHaveCount(1);
  expect(stub.createRequests).toHaveLength(1);
  expect(stub.createRequests[0]).toMatchObject({ retention_class: "STANDARD_90D" });
  expect(stub.createRequests[0]).not.toHaveProperty("tenant_id");
  expect(stub.createRequests[0]).not.toHaveProperty("identity_subject");
  expect(stub.conversations()).toHaveLength(1);
  expect(stub.conversations()[0].messages).toHaveLength(2);
  expect(await axentLocalHistoryKeys(page)).toEqual([]);
});

test("keeps saved server conversations available while starting another", async ({ page }) => {
  await installAxentPersistenceStub(page);
  await page.goto("/axent");

  const composer = page.getByRole("textbox", { name: COMPOSER_NAME, exact: true });
  await composer.fill("Show AXIGNAL opportunities");
  await composer.press("Enter");

  const savedConversation = page.locator('[aria-label="Saved conversations"] article').first();
  await expect(savedConversation).toBeVisible();
  await page.getByRole("button", { name: "New chat", exact: true }).click();
  await expect(page.getByRole("heading", { name: "What are you investigating today?" })).toBeVisible();
  await expect(savedConversation).toBeVisible();

  await savedConversation.getByRole("button", { name: /Open conversation/ }).click();
  await expect(page.getByRole("log", { name: "AXENT conversation" })).toContainText(
    "Show AXIGNAL opportunities",
  );
});

test("sends only a conversation reference and requests governed deletion", async ({ page }) => {
  const stub = await installAxentPersistenceStub(page);
  await page.goto("/axent");

  const composer = page.getByRole("textbox", { name: COMPOSER_NAME, exact: true });
  await composer.fill("Explain the evidence model");
  await composer.press("Enter");
  await expect(page.locator('[aria-label="Saved conversations"] article')).toHaveCount(1);

  await composer.fill("What should I review next?");
  await composer.press("Enter");
  expect(stub.assistantRequests).toHaveLength(2);
  expect(stub.assistantRequests[1]).toHaveProperty("conversation_id");
  expect(stub.assistantRequests[1]).not.toHaveProperty("history");
  expect(await axentLocalHistoryKeys(page)).toEqual([]);

  await page.getByRole("button", { name: "Request deletion", exact: true }).click();
  await expect(page.locator('[aria-label="Saved conversations"] article')).toHaveCount(0);
  expect(stub.deleteRequests).toHaveLength(1);
});

test("logout clears obsolete AXENT keys without deleting unrelated storage", async ({ page }) => {
  await installAxentPersistenceStub(page);
  await page.goto("/axent");
  await page.evaluate(() => {
    localStorage.setItem("axignal:axent:local-history:v1:obsolete", "obsolete");
    localStorage.setItem("axignal:axent:history:v3:obsolete", "obsolete");
    localStorage.setItem("axignal:unrelated", "keep");
  });

  await page.getByRole("button", { name: /Account menu for/ }).click();
  const logoutResponse = page.waitForResponse(
    (response) => response.url().endsWith("/api/auth/logout") && response.request().method() === "POST",
  );
  await page.getByRole("menuitem", { name: "Sign out and clear local AXENT history" }).click();
  expect((await logoutResponse).status()).toBe(200);
  await page.waitForURL("**/", { waitUntil: "domcontentloaded" });

  const storageState = await page.context().storageState();
  const originStorage = storageState.origins.find(
    (origin) => origin.origin === new URL(page.url()).origin,
  )?.localStorage ?? [];
  expect(originStorage.some((entry) => entry.name.startsWith("axignal:axent:"))).toBe(false);
  expect(originStorage.find((entry) => entry.name === "axignal:unrelated")?.value).toBe("keep");
});