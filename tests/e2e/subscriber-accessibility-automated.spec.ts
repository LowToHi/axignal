import { expect, test, type Page } from "@playwright/test";

const workspaceId = "axfx_ws_eu_cloud_001";
const criticalRoutes = [
  "/axent",
  "/investigations",
  `/workspaces/${workspaceId}/overview`,
] as const;

async function useEnglishShell(page: Page) {
  const language = page.locator("header select");
  if (await language.count()) {
    await language.selectOption("en");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
  }
}

async function semanticViolations(page: Page) {
  return page.evaluate(() => {
    const duplicates = Object.entries(
      Array.from(document.querySelectorAll<HTMLElement>("[id]")).reduce<
        Record<string, number>
      >((counts, element) => {
        counts[element.id] = (counts[element.id] ?? 0) + 1;
        return counts;
      }, {}),
    )
      .filter(([, count]) => count > 1)
      .map(([id]) => `duplicate-id:${id}`);

    const positiveTabIndex = Array.from(
      document.querySelectorAll<HTMLElement>("[tabindex]"),
    )
      .filter((element) => element.tabIndex > 0)
      .map((element) => `positive-tabindex:${element.tagName.toLowerCase()}`);

    const interactive = Array.from(
      document.querySelectorAll<HTMLElement>(
        'a[href],button,input:not([type="hidden"]),select,textarea,[role="button"],[role="link"],[role="menuitem"]',
      ),
    );

    function isVisible(element: HTMLElement) {
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return (
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        rect.width > 0 &&
        rect.height > 0 &&
        element.getAttribute("aria-hidden") !== "true"
      );
    }

    function accessibleName(element: HTMLElement) {
      const ariaLabel = element.getAttribute("aria-label")?.trim();
      if (ariaLabel) return ariaLabel;

      const labelledBy = element.getAttribute("aria-labelledby");
      if (labelledBy) {
        const value = labelledBy
          .split(/\s+/)
          .map((id) => document.getElementById(id)?.textContent?.trim() ?? "")
          .filter(Boolean)
          .join(" ");
        if (value) return value;
      }

      if (
        element instanceof HTMLInputElement ||
        element instanceof HTMLSelectElement ||
        element instanceof HTMLTextAreaElement
      ) {
        const labels = Array.from(element.labels ?? [])
          .map((label) => label.textContent?.trim() ?? "")
          .filter(Boolean)
          .join(" ");
        if (labels) return labels;
        if (element instanceof HTMLInputElement && element.value.trim()) {
          return element.value.trim();
        }
      }

      const title = element.getAttribute("title")?.trim();
      if (title) return title;
      return element.textContent?.replace(/\s+/g, " ").trim() ?? "";
    }

    const unnamed = interactive
      .filter(isVisible)
      .filter((element) => !accessibleName(element))
      .map((element) => {
        const id = element.id ? `#${element.id}` : "";
        const role = element.getAttribute("role");
        return `unnamed:${element.tagName.toLowerCase()}${id}${role ? `[role=${role}]` : ""}`;
      });

    const mainCount = document.querySelectorAll("main").length;
    const landmarks = mainCount === 1 ? [] : [`main-landmarks:${mainCount}`];

    return [...duplicates, ...positiveTabIndex, ...unnamed, ...landmarks];
  });
}

test.describe.configure({ mode: "serial" });

for (const route of criticalRoutes) {
  test(`keeps semantic integrity on ${route}`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto(route);
    await useEnglishShell(page);

    await expect(page.locator("main#subscriber-main")).toHaveCount(1);
    expect(await semanticViolations(page)).toEqual([]);
  });
}

test("reflows critical subscriber surfaces at 320 CSS pixels", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 320, height: 900 });

  for (const route of criticalRoutes) {
    await page.goto(route);
    await useEnglishShell(page);
    await expect(page.locator("main#subscriber-main")).toBeVisible();

    const overflow = await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      document: document.documentElement.scrollWidth,
      body: document.body.scrollWidth,
    }));
    expect(overflow.document).toBeLessThanOrEqual(overflow.viewport + 1);
    expect(overflow.body).toBeLessThanOrEqual(overflow.viewport + 1);
  }
});

test("keeps controls available after 200 percent text scaling", async ({ page }) => {
  await page.goto("/axent");
  await useEnglishShell(page);
  await page.addStyleTag({ content: "html { font-size: 200% !important; }" });

  await expect(page.locator("main#subscriber-main")).toBeVisible();
  await expect(
    page.getByRole("textbox", {
      name: "Ask AXENT anything about AXIGNAL",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Send message" })).toBeVisible();
});

test("preserves keyboard operation and visible focus in forced-colors mode", async ({
  page,
}) => {
  await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
  await page.goto("/investigations");
  await useEnglishShell(page);

  const forcedColors = await page.locator("html").evaluate((element) =>
    getComputedStyle(element)
      .getPropertyValue("--ax-forced-colors-active")
      .trim(),
  );
  expect(forcedColors).toBe("1");

  const focusTarget = (page.viewportSize()?.width ?? 1280) <= 900
    ? page.getByRole("button", { name: "Open navigation", exact: true })
    : page.getByRole("button", { name: /Search opportunities/i });
  await focusTarget.focus();
  const focusStyle = await focusTarget.evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      outlineStyle: style.outlineStyle,
      outlineWidth: Number.parseFloat(style.outlineWidth),
    };
  });
  expect(focusStyle.outlineStyle).not.toBe("none");
  expect(focusStyle.outlineWidth).toBeGreaterThanOrEqual(2);

  await page.keyboard.press("Control+K");
  const dialog = page.getByRole("dialog", { name: "Navigate" });
  await expect(dialog).toBeVisible();
  await expect(
    page.getByRole("textbox", { name: "Search or enter a command" }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(focusTarget).toBeFocused();
});
