import { expect, test } from "@playwright/test";

test("discloses deterministic AXENT guidance when no live model response is used", async ({ page }) => {
  await page.goto("/axent");

  const composer = page.getByRole("textbox", { name: "Ask AXENT anything about AXIGNAL" });
  await composer.fill("Help me understand the evidence in this AXIGNAL workspace.");

  const responsePromise = page.waitForResponse((response) =>
    response.url().includes("/api/subscriber-workspace/assistant") && response.request().method() === "POST"
  );

  await page.getByRole("button", { name: "Send message" }).click();
  const response = await responsePromise;

  expect(response.status()).toBe(200);
  expect(response.headers()["x-axignal-ai-authority"]).toBe("proposal-only");
  expect(response.headers()["x-axignal-assistant-mode"]).toBe("fixture");
  await expect(page.getByText(/Deterministic guidance mode — no live model response was used\./)).toBeVisible();
});
