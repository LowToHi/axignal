import { expect, test } from "@playwright/test";

test.describe.configure({ mode: "serial" });

test("renders the admitted cartographic globe with its accessible equivalent", async ({
  page,
}) => {
  const boundaries = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname ===
        "/globe/europe-boundaries-50m.geojson" && response.ok(),
  );

  await page.goto("/investigations");
  await boundaries;

  await expect(page.getByTestId("semantic-globe-webgl")).toBeAttached();
  await expect(
    page.getByText("NASA Earth Observatory · Natural Earth"),
  ).toBeVisible();
  await expect(
    page.getByRole("table", {
      name: "European Union: accessible geographic opportunity list",
    }),
  ).toBeAttached();
});

test("keeps the Globe visible without a fade transition when selection changes", async ({
  page,
}) => {
  await page.goto("/investigations");

  const canvas = page.getByTestId("semantic-globe-webgl").locator("canvas");
  await expect(canvas).toBeAttached();
  await expect
    .poll(() => canvas.evaluate((element) => getComputedStyle(element).animationName))
    .toBe("none");

  await page.getByRole("button", {
    name: "Urban data platform implementation and support MEDIUM Evidence fit 68% evidence Assessment confidence 68%",
    exact: true,
  }).click();
  await expect(
    page.getByRole("region", { name: "European Union" }),
  ).toContainText("Selected Urban data platform implementation and support");
  await expect
    .poll(() => canvas.evaluate((element) => getComputedStyle(element).animationName))
    .toBe("none");
});

test("keeps the complete opportunity equivalent when WebGL is unavailable", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const nativeGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (contextId, ...args) {
      if (contextId === "webgl" || contextId === "webgl2") return null;
      return nativeGetContext.call(this, contextId, ...args);
    };
  });

  await page.goto("/investigations");

  await expect(
    page.getByText(
      "Cartographic globe unavailable. The accessible opportunity list remains available below.",
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("table", {
      name: "European Union: accessible geographic opportunity list",
    }),
  ).toBeAttached();
  await expect(
    page.getByRole("button", {
      name: "Select Sovereign cloud operations framework",
    }),
  ).toBeAttached();
});

test("keeps the globe canvas mounted while the Navigator draft changes", async ({
  page,
}) => {
  await page.goto("/investigations");

  const globe = page.getByTestId("semantic-globe-webgl");
  await expect(globe).toBeAttached();
  const identity = await globe.evaluate((element) => {
    const value = "navigator-draft-stability";
    element.setAttribute("data-render-identity", value);
    return value;
  });

  const composer = page.locator("#axignal-navigator-command");
  await composer.pressSequentially("Review public procurement evidence", {
    delay: 20,
  });

  await expect(composer).toHaveValue("Review public procurement evidence");
  await expect(globe).toHaveAttribute("data-render-identity", identity);
});

test("keeps the globe mounted when a persistent Navigator run is rejected", async ({
  page,
}) => {
  await page.goto("/investigations");

  const globe = page.getByTestId("semantic-globe-webgl");
  await expect(globe).toBeAttached();
  const identity = await globe.evaluate((element) => {
    const value = "navigator-action-stability";
    element.setAttribute("data-render-identity", value);
    return value;
  });

  const actionResponse = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === "/api/research/runs" &&
      response.request().method() === "POST",
  );
  const composer = page.locator("#axignal-navigator-command");
  await composer.fill("Review public procurement evidence");
  await composer.press("Enter");
  const response = await actionResponse;

  expect(response.status()).toBe(503);
  await expect(page.getByTestId("navigator-research-error")).toContainText(
    "synthetic fallback is forbidden",
  );
  await expect(globe).toHaveAttribute("data-render-identity", identity);
});

test("allows the globe to rotate and zoom without remounting", async ({
  page,
}) => {
  await page.goto("/investigations");

  const globe = page.getByTestId("semantic-globe-webgl");
  await expect(globe).toBeAttached();
  const canvas = globe.locator("canvas");
  const bounds = await canvas.boundingBox();
  expect(bounds).not.toBeNull();

  const identity = await globe.evaluate((element) => {
    const value = "interactive-globe-stability";
    element.setAttribute("data-render-identity", value);
    return value;
  });

  const centerX = (bounds?.x ?? 0) + (bounds?.width ?? 0) / 2;
  const centerY = (bounds?.y ?? 0) + (bounds?.height ?? 0) / 2;
  await page.mouse.move(centerX, centerY);
  await page.mouse.down();
  await page.mouse.move(centerX + 120, centerY + 18, { steps: 6 });
  await page.mouse.up();
  await page.mouse.wheel(0, -240);

  await expect(globe).toHaveAttribute("data-render-identity", identity);
});

test("does not rotate the globe autonomously while idle", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/investigations");

  const globeRegion = page.getByRole("region", { name: "European Union" });
  const card = globeRegion
    .locator('[role="status"]')
    .filter({ hasText: "Selected Sovereign cloud operations framework" });
  await expect(card).toBeAttached({ timeout: 15000 });
  const before = await card.boundingBox();
  expect(before).not.toBeNull();
  await page.waitForTimeout(900);
  const after = await card.boundingBox();
  expect(after).not.toBeNull();
  expect(Math.abs(after!.x - before!.x)).toBeLessThan(1);
  expect(Math.abs(after!.y - before!.y)).toBeLessThan(1);
});

test("keeps the selected marker card at a fixed visual size while zooming", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/investigations");

  const globeRegion = page.getByRole("region", { name: "European Union" });
  const card = globeRegion
    .locator('[role="status"]')
    .filter({ hasText: "Selected Sovereign cloud operations framework" });
  await expect(page.getByTestId("semantic-globe-webgl")).toBeAttached();
  await expect(card).toBeAttached({ timeout: 15000 });
  await expect(card).toBeVisible();
  const before = await card.boundingBox();
  expect(before).not.toBeNull();

  const canvas = page.getByTestId("semantic-globe-webgl").locator("canvas");
  const bounds = await canvas.boundingBox();
  expect(bounds).not.toBeNull();
  await page.mouse.move(
    (bounds?.x ?? 0) + (bounds?.width ?? 0) / 2,
    (bounds?.y ?? 0) + (bounds?.height ?? 0) / 2,
  );
  await page.mouse.wheel(0, -240);

  const after = await card.boundingBox();
  expect(after).not.toBeNull();
  expect(after!.width).toBeLessThanOrEqual(before!.width + 1);
  expect(after!.height).toBeLessThanOrEqual(before!.height + 1);
});

test("lets subscribers select a timeline point", async ({ page }) => {
  await page.goto("/investigations");

  const deadline = page.locator(
    '[aria-label="Timeline points"] button[aria-label="2026-08-28: Submission deadline"]',
  );
  await expect(deadline).toHaveCount(1);
  await deadline.click();

  await expect(deadline).toHaveAttribute("aria-current", "date");
  await expect(
    page.getByRole("region", { name: "Investigation timeline" }),
  ).toContainText("Submission deadline");
});

test("keeps the selected opportunity details with the active globe marker", async ({
  page,
}) => {
  await page.goto("/investigations");

  const urbanOpportunity = page.getByRole("button", {
    name: "Urban data platform implementation and support MEDIUM Evidence fit 68% evidence Assessment confidence 68%",
    exact: true,
  });
  await expect(urbanOpportunity).toHaveCount(1);
  await urbanOpportunity.click();

  await expect(
    page.getByRole("region", { name: "European Union" }),
  ).toContainText("Selected Urban data platform implementation and support");
});
