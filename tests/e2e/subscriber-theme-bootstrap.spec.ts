import { expect, test } from "@playwright/test";

test("restores a stored light preference before navigation changes the workspace", async ({
  page,
}) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("axignal:subscriber:theme", "light");
  });

  await page.goto("/alerts");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.locator("html")).toHaveCSS("color-scheme", "light");

  const investigationsLink = page.getByRole("link", { name: "Investigations" });

  if ((page.viewportSize()?.width ?? Number.POSITIVE_INFINITY) <= 1024) {
    const navigationToggle = page.getByRole("button", { name: "Open navigation" });

    await expect(navigationToggle).toBeVisible();
    await navigationToggle.click();
    await expect(investigationsLink).toBeInViewport();
  }

  await investigationsLink.click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});
