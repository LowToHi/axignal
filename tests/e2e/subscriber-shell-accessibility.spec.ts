import { expect, test } from "@playwright/test";

const workspaceId = "axfx_ws_eu_cloud_001";

test("traps and restores focus for the command palette", async ({ page }) => {
  await page.goto("/axent");

  const trigger = page.getByRole("button", { name: /Search opportunities/i });
  await trigger.focus();
  await page.keyboard.press("Control+K");

  const dialog = page.getByRole("dialog", { name: "Navigate" });
  const input = page.getByRole("textbox", { name: "Search or enter a command" });
  await expect(dialog).toBeVisible();
  await expect(input).toBeFocused();

  await page.keyboard.press("Shift+Tab");
  await expect.poll(async () => dialog.evaluate((element) => element.contains(document.activeElement))).toBe(true);

  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();
});

test("keeps contextual workspace navigation available across desktop and tablet", async ({ page }) => {
  await page.goto(`/workspaces/${workspaceId}/overview`);
  const viewportWidth = page.viewportSize()?.width ?? 1280;

  if (viewportWidth <= 900) {
    const trigger = page.getByRole("button", { name: "Open navigation" });
    await trigger.click();

    const drawer = page.getByRole("dialog", { name: "Mobile product navigation" });
    await expect(drawer).toBeVisible();
    await expect(page.getByRole("button", { name: "Close navigation" })).toBeFocused();
    await expect(drawer.getByRole("link", { name: "Qualification" })).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(drawer).toBeHidden();
    await expect(trigger).toBeFocused();
  } else {
    await expect(page.getByRole("navigation", { name: "Tender workspace navigation" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open navigation" })).toBeHidden();
  }
});
