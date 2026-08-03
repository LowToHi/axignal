import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith("axignal:axent:history:")) localStorage.removeItem(key);
    }
  });
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
