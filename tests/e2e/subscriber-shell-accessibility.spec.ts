import { expect, test } from "@playwright/test";

const workspaceId = "axfx_ws_eu_cloud_001";

async function useEnglishShell(page: Parameters<typeof test>[0] extends never ? never : any) {
  const language = page.locator("header select");
  await language.selectOption("en");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
}

test("traps and restores focus for the command palette", async ({ page }) => {
  await page.goto("/axent");
  await useEnglishShell(page);
  const viewportWidth = page.viewportSize()?.width ?? 1280;
  const trigger = viewportWidth <= 900
    ? page.getByRole("button", { name: "Open navigation", exact: true })
    : page.getByRole("button", { name: /Search opportunities/i });

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

test("keeps contextual workspace navigation available across desktop, tablet and mobile", async ({ page }) => {
  await page.goto(`/workspaces/${workspaceId}/overview`);
  await useEnglishShell(page);
  const viewportWidth = page.viewportSize()?.width ?? 1280;

  if (viewportWidth <= 900) {
    const trigger = page.getByRole("button", { name: "Open navigation", exact: true });
    await trigger.click();

    const drawer = page.getByRole("dialog", { name: "Mobile product navigation" });
    await expect(drawer).toBeVisible();
    await expect(page.getByRole("button", { name: "Close navigation", exact: true })).toBeFocused();
    await expect(drawer.getByRole("link", { name: "Qualification" })).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(drawer).toBeHidden();
    await expect(trigger).toBeFocused();
  } else {
    await expect(page.getByRole("navigation", { name: "Workspace sections", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open navigation", exact: true })).toBeHidden();
  }
});

test("replaces animated globe output with a static equivalent when reduced motion is requested", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/investigations");

  const globe = page.getByRole("region", { name: "European Union" });
  await expect(globe).toBeVisible();
  await expect(page.getByTestId("semantic-globe-webgl")).toHaveCount(0);
  await expect(page.getByTestId("semantic-globe-static")).toBeVisible();
  await expect(page.getByText(/Motion reduced\. A static cartographic equivalent is shown/)).toBeVisible();

  const motionContract = await page.locator("html").evaluate((element) => ({
    active: getComputedStyle(element).getPropertyValue("--ax-reduced-motion-active").trim(),
    staticSurface: document.querySelector('[data-reduced-motion="true"]') !== null,
  }));
  expect(motionContract.active).toBe("1");
  expect(motionContract.staticSurface).toBe(true);

  await expect(globe.getByRole("table")).toBeAttached();
  await expect(globe.getByRole("button", { name: /Select Sovereign cloud operations framework/ })).toBeAttached();
});
