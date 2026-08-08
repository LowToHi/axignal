import { expect, test, type Page } from "@playwright/test";

/**
 * Cierre visual y funcional E2E — landing pública de AXIGNAL.
 *
 * Cubre: logo, globe (primario + fallback), hero responsive, favicon y
 * metadatos, acceso de clientes (logged out / logged in), navegación,
 * menú móvil y calidad técnica (sin pageerror / 404 / overflow).
 */

test.describe.configure({ timeout: 25_000 });

async function collectErrors(page: Page) {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(`PAGEERROR: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`CONSOLE: ${message.text()}`);
  });
  return errors;
}

test("logo loads, links home and is not broken", async ({ page }) => {
  const errors = await collectErrors(page);
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const brand = page.getByRole("link", { name: "AXIGNAL home" }).first();
  await expect(brand).toBeVisible();
  const image = brand.locator("img").first();
  await expect(image).toBeVisible();
  const naturalWidth = await image.evaluate((el) => (el as HTMLImageElement).naturalWidth);
  expect(naturalWidth).toBeGreaterThan(0);
  const broken = await page
    .evaluate(() =>
      Array.from(document.images)
        .filter((img) => img.complete && img.naturalWidth === 0)
        .map((img) => img.src)
    );
  expect(broken).toEqual([]);
  await brand.click();
  await expect(page).toHaveURL(/\/$/);
  expect(errors.filter((e) => e.startsWith("PAGEERROR"))).toEqual([]);
});

test("renders the interactive globe in a supported runtime", async ({ page }) => {
  const errors = await collectErrors(page);
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const globe = page.getByTestId("semantic-globe");
  await expect(globe).toHaveCount(1);
  await expect(globe.locator("canvas")).toHaveCount(1, { timeout: 15_000 });
  await expect(globe.locator(".globe-poster")).toHaveCount(0);
  expect(errors.filter((e) => e.startsWith("PAGEERROR"))).toEqual([]);
});

test("shows an intentional visual fallback when WebGL is forced off", async ({
  browser
}) => {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await context.addInitScript(() => {
    const proto = HTMLCanvasElement.prototype;
    const original = proto.getContext;
    proto.getContext = function (type: string, ...args: unknown[]) {
      if (type === "webgl2" || type === "webgl" || type === "experimental-webgl") {
        return null;
      }
      return original.call(this, type, ...args);
    };
  });
  const page = await context.newPage();
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const globe = page.getByTestId("semantic-globe");
  await expect(globe.locator(".globe-poster")).toBeVisible({ timeout: 15_000 });
  await expect(globe.locator("canvas")).toHaveCount(0);
  // Nota discreta, no un mensaje técnico protagonista.
  await expect(globe.locator(".globe-poster-note")).toBeVisible();
  const note = (await globe.locator(".globe-poster-note").textContent()) ?? "";
  expect(note.toLowerCase()).not.toContain("unavailable. the source-state table");
  await context.close();
});

test("hero headline fits the viewport without clipping or overflow", async ({
  page
}) => {
  const errors = await collectErrors(page);
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const headline = page.getByRole("heading", { level: 1 });
  await expect(headline).toBeVisible();
  // Copy canónica comercial (el contrato prohíbe el copy superseded).
  await expect(headline).toContainText(
    /Find the public contracts your business is built to pursue/
  );
  const metrics = await page.evaluate(() => {
    const h1 = document.querySelector(".scene-global h1");
    if (!h1) return null;
    const rect = h1.getBoundingClientRect();
    return {
      fontSize: parseFloat(getComputedStyle(h1).fontSize),
      bottom: Math.round(rect.bottom),
      viewportHeight: window.innerHeight,
      bodyOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
      lineHeight: getComputedStyle(h1).lineHeight
    };
  });
  expect(metrics).not.toBeNull();
  expect(metrics!.bottom).toBeLessThanOrEqual(metrics!.viewportHeight);
  expect(metrics!.bodyOverflow).toBe(false);
  expect(metrics!.fontSize).toBeLessThan(96);
  await expect(page.getByRole("link", { name: "Request your 7-day B2G trial" }).first()).toBeVisible();
  expect(errors.filter((e) => e.startsWith("PAGEERROR"))).toEqual([]);
});

test("favicon and metadata are present and served", async ({ request }) => {
  const favicon = await request.get("/favicon.ico");
  expect(favicon.status()).toBe(200);
  const svg = await request.get("/favicon.svg");
  expect(svg.status()).toBe(200);
  const logoDark = await request.get("/brand/axignal-logo-dark.svg");
  expect(logoDark.status()).toBe(200);
});

test("customer access shows Log in logged out and Open AXIGNAL logged in", async ({
  page,
  context,
  isMobile
}) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const access = isMobile
    ? page.locator('#mobile-menu [data-axignal-customer-access="true"]').first()
    : page.locator('[data-axignal-customer-access="true"]').first();
  if (isMobile) {
    // En móvil el acceso vive en el menú móvil.
    await page.locator(".mobile-menu-toggle").click();
  }
  await expect(access).toBeVisible();
  await expect(access).toHaveText("Log in");
  const href = await access.getAttribute("href");
  expect(href).toMatch(/^https?:\/\//);

  // Estado autenticado: cookie de sesión → Open AXIGNAL.
  await context.addCookies([
    { name: "axignal_session", value: "test-session", domain: "127.0.0.1", path: "/" }
  ]);
  await page.reload({ waitUntil: "domcontentloaded" });
  if (isMobile) {
    await page.locator(".mobile-menu-toggle").click();
  }
  await expect(access).toHaveText("Open AXIGNAL", { timeout: 10_000 });
});

test("navigation, theme and language controls work", async ({ page, isMobile }) => {
  const errors = await collectErrors(page);
  await page.goto("/", { waitUntil: "domcontentloaded" });
  if (isMobile) {
    await page.locator(".mobile-menu-toggle").click();
  }
  for (const label of ["Product", "Method", "Pricing", "FAQ"]) {
    await expect(page.getByRole("link", { name: label, exact: true }).first()).toBeVisible();
  }
  const themeToggle = page.getByRole("button", { name: "Switch to light" });
  if (isMobile) {
    // El toggle global se oculta en móvil; la navegación vive en el menú.
    await page.keyboard.press("Escape");
  } else {
    await expect(themeToggle).toBeVisible();
    await themeToggle.click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    await page.getByRole("button", { name: "Switch to dark" }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  }

  const language = page.locator(".language-menu summary");
  await expect(language).toBeVisible();
  await language.click();
  const spanish = page.getByRole("link", { name: "Español", exact: true }).first();
  await expect(spanish).toBeVisible();
  expect(errors.filter((e) => e.startsWith("PAGEERROR"))).toEqual([]);
});

test("mobile menu contains all sections and closes with Escape", async ({
  browser
}) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const toggle = page.locator(".mobile-menu-toggle");
  await expect(toggle).toBeVisible();
  await toggle.click();
  const menu = page.locator("#mobile-menu");
  await expect(menu).toBeVisible();
  const labels = (await menu.locator("a").allTextContents()).map((t) => t.trim());
  for (const label of ["Product", "Method", "Pricing", "FAQ", "Request your 7-day B2G trial"]) {
    expect(labels).toContain(label);
  }
  // El acceso de clientes solo se renderiza cuando la app autenticada está
  // configurada (NEXT_PUBLIC_AXIGNAL_APP_URL); sin ella, no hay Log in.
  const access = menu.locator('[data-axignal-customer-access="true"]');
  if (process.env.NEXT_PUBLIC_AXIGNAL_APP_URL) {
    expect(labels).toContain("Log in");
    await expect(access).toBeVisible();
  } else {
    await expect(access).toHaveCount(0);
  }
  await page.keyboard.press("Escape");
  await expect(menu).not.toBeVisible();
  await expect(toggle).toBeFocused();
  await context.close();
});

test("does not expose the admitted source brand as public landing identity", async ({
  page
}) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.getByText(/Tenders Electronic Daily|TED bounded/i)).toHaveCount(0);
  await expect(page.getByText(/^TED · PRODUCT_ADMITTED/i)).not.toBeVisible();
  const statusRibbon = page.locator(".status-ribbon");
  await expect(statusRibbon).toBeVisible();
  const generatedBoundary = await statusRibbon.evaluate((element) =>
    getComputedStyle(element, "::before").content.replaceAll('"', "")
  );
  expect(generatedBoundary).toBe("ADMITTED PUBLIC-SOURCE PROFILE · PRIVATE AUTHENTICATED PILOT");
});

test("no horizontal overflow on mandatory viewports", async ({ browser }) => {
  const viewports = [
    { width: 1366, height: 768 },
    { width: 1440, height: 900 },
    { width: 1728, height: 1117 },
    { width: 1920, height: 1080 },
    { width: 768, height: 1024 },
    { width: 390, height: 844 }
  ];
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    await page.goto("/", { waitUntil: "domcontentloaded" });
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth + 1
    );
    expect(overflow, `overflow en ${viewport.width}x${viewport.height}`).toBe(false);
    await context.close();
  }
});

test("Log in leads to the real authenticated application", async ({ page, isMobile, request }) => {
  const appUrl = process.env.NEXT_PUBLIC_AXIGNAL_APP_URL;
  test.skip(!appUrl, "NEXT_PUBLIC_AXIGNAL_APP_URL no configurada");
  // La app autenticada puede no estar servida en esta matriz (corre en el
  // gate AXENT). El enlace debe existir; el destino se valida si responde.
  const probe = await request.get(appUrl!).catch(() => null);
  test.skip(probe === null || probe.status() !== 200, "app AXIGNAL no servida");
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const access = isMobile
    ? page.locator('#mobile-menu [data-axignal-customer-access="true"]').first()
    : page.locator('[data-axignal-customer-access="true"]').first();
  if (isMobile) {
    await page.locator(".mobile-menu-toggle").click();
  }
  await access.click();
  await page.waitForURL(/^http:\/\/127\.0\.0\.1:3000/, { timeout: 15_000 });
  await expect(page).toHaveTitle(/AXIGNAL/);
  // La aplicación autenticada renderiza el workspace real (o el AuthGate).
  const body = await page.evaluate(() => document.body.innerText.slice(0, 400));
  expect(
    body.includes("AXIGNAL") || body.toLowerCase().includes("passkey")
  ).toBe(true);
});

test("makes the controlled trial and canonical monthly prices explicit", async ({
  page
}) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.waitForFunction(
    () =>
      document.querySelector(".cinematic-stage")?.parentElement?.classList.contains("pin-spacer")
  );
  const pricingLink = page.getByRole("link", { name: "Pricing", exact: true });
  if (await pricingLink.isVisible()) {
    await pricingLink.click();
  } else {
    await page.locator("#pricing").scrollIntoViewIfNeeded();
  }
  await expect(page.locator("#pricing")).toBeInViewport();
  await expect(page.getByRole("heading", { name: /Choose the contracted operating boundary/i })).toBeVisible();
  // Trial destacado: exactamente una vez (sin tarjeta duplicada).
  const trialHeadings = page.getByRole("heading", { name: "Controlled Trial" });
  await expect(trialHeadings).toHaveCount(1);
  await expect(trialHeadings).toBeVisible();
  await expect(page.getByText("1,000,000 cumulative tokens per organisation")).toBeVisible();
  await expect(page.getByText("No card", { exact: true })).toBeVisible();
  await expect(page.getByText("No automatic renewal", { exact: true })).toBeVisible();
  await expect(page.getByText("No overage", { exact: true })).toBeVisible();
  await expect(page.getByText("Read-only at expiry", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Request 7-day B2G trial" }).first()).toBeVisible();
  await expect(page.getByText(/CONTROLLED 7-DAY TRIAL/)).toBeVisible();
  await expect(page.getByText(/Canonical price book · 2026-08-04/).first()).toBeVisible();
  // Planes contratados: dos tarjetas de igual anchura, sin columna vacía.
  await expect(page.getByRole("heading", { name: "Professional" })).toBeVisible();
  await expect(page.getByText("€149", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Team" })).toBeVisible();
  await expect(page.getByText("€399", { exact: true })).toBeVisible();
  await expect(page.locator(".paid-plan-card")).toHaveCount(2);
  await expect(page.locator(".paid-plan-card[data-plan='professional']")).toBeVisible();
  await expect(page.locator(".paid-plan-card[data-plan='team']")).toBeVisible();
  // Sin columna USERS: la fila de usuarios no se renderiza (price book no la define).
  await expect(page.getByText("Users", { exact: true })).toHaveCount(0);
  // CTA visibles en ambas tarjetas.
  await expect(page.getByRole("link", { name: "Request Professional access" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Request Team access" })).toBeVisible();
  // Sin desbordamiento horizontal.
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth + 1
  );
  expect(overflow).toBe(false);
});

test("pricing paid plans are equal-width on desktop and stacked on mobile", async ({
  browser
}) => {
  // Contextos explícitos: el test es independiente del project (corre en
  // desktop y mobile) y fija su propio viewport para cada caso.
  const desktopContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = desktopContext.pages()[0] ?? (await desktopContext.newPage());
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.waitForFunction(
    () =>
      document.querySelector(".cinematic-stage")?.parentElement?.classList.contains("pin-spacer")
  );
  await page.locator("#pricing").scrollIntoViewIfNeeded();
  await expect(page.locator(".paid-plan-card")).toHaveCount(2);

  // Desktop (1440): 2 columnas, misma anchura.
  const widthsDesktop = await page.locator(".paid-plan-card").evaluateAll((cards) =>
    cards.map((c) => Math.round(c.getBoundingClientRect().width))
  );
  expect(widthsDesktop[0]).toBeGreaterThan(400);
  expect(Math.abs(widthsDesktop[0] - widthsDesktop[1])).toBeLessThanOrEqual(2);
  await desktopContext.close();

  // Móvil (390): 1 columna, tarjetas apiladas.
  const mobileContext = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const mobilePage = mobileContext.pages()[0] ?? (await mobileContext.newPage());
  await mobilePage.goto("/", { waitUntil: "domcontentloaded" });
  await mobilePage.waitForFunction(
    () =>
      document.querySelector(".cinematic-stage")?.parentElement?.classList.contains("pin-spacer")
  );
  await mobilePage.locator("#pricing").scrollIntoViewIfNeeded();
  await expect(mobilePage.locator(".paid-plan-card")).toHaveCount(2);
  const widthsMobile = await mobilePage.locator(".paid-plan-card").evaluateAll((cards) =>
    cards.map((c) => Math.round(c.getBoundingClientRect().width))
  );
  expect(Math.abs(widthsMobile[0] - widthsMobile[1])).toBeLessThanOrEqual(2);
  expect(widthsMobile[0]).toBeGreaterThan(300);
  // Sin desbordamiento horizontal en móvil.
  const overflowMobile = await mobilePage.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth + 1
  );
  expect(overflowMobile).toBe(false);
  await mobileContext.close();
});
