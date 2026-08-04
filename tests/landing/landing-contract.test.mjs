import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const repoRoot = resolve(fileURLToPath(new URL("../..", import.meta.url)));
const landingRoot = resolve(repoRoot, "apps/landing");
const localeCodes = ["de", "en", "es", "fr", "it", "pt"];

async function readJson(relativePath) {
  const absolutePath = resolve(repoRoot, relativePath);
  return JSON.parse(await readFile(absolutePath, "utf8"));
}

function collectKeys(value, prefix = "", keys = new Set()) {
  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      const path = `${prefix}[${index}]`;
      keys.add(path);
      collectKeys(item, path, keys);
    });
    return keys;
  }

  if (value && typeof value === "object") {
    for (const [name, child] of Object.entries(value)) {
      const path = prefix ? `${prefix}.${name}` : name;
      keys.add(path);
      collectKeys(child, path, keys);
    }
  }

  return keys;
}

test("all landing locales are valid and structurally aligned", async () => {
  const locales = await Promise.all(
    localeCodes.map(async (locale) => [locale, await readJson(`apps/landing/messages/${locale}.json`)]),
  );
  const baseline = collectKeys(locales.find(([locale]) => locale === "en")[1]);

  for (const [locale, messages] of locales) {
    assert.ok(messages.nav, `${locale}.json must contain navigation messages`);
    assert.deepEqual(
      [...collectKeys(messages)].sort(),
      [...baseline].sort(),
      `${locale}.json must preserve the English key structure`,
    );
  }
});

test("canonical B2G copy overrides every supported locale", async () => {
  const [contract, i18n] = await Promise.all([
    readFile(resolve(landingRoot, "lib/canonical-commercial-contract.ts"), "utf8"),
    readFile(resolve(landingRoot, "lib/i18n.ts"), "utf8"),
  ]);

  assert.match(contract, /BUSINESS-TO-GOVERNMENT \(B2G\) OPPORTUNITY INTELLIGENCE/);
  assert.match(contract, /Find the public contracts your business is built to pursue\./);
  assert.match(contract, /Request your 7-day B2G trial/);
  for (const locale of localeCodes) {
    assert.match(contract, new RegExp(`\\n  ${locale}: \\{`), `${locale} must have canonical commercial copy`);
  }
  assert.match(i18n, /canonicalCommercialCopy\[locale\]/);
  assert.match(i18n, /index === 2/);
  assert.match(i18n, /index === 7/);
});

test("price book is versioned and reconciled to the contractual catalogue", async () => {
  const [contract, pricing] = await Promise.all([
    readFile(resolve(landingRoot, "lib/canonical-commercial-contract.ts"), "utf8"),
    readFile(resolve(landingRoot, "lib/pricing-data.ts"), "utf8"),
  ]);

  assert.match(contract, /CONTROLLED_TRIAL_7D/);
  assert.match(contract, /amountMinor: 0/);
  assert.match(contract, /PROFESSIONAL_MONTHLY/);
  assert.match(contract, /amountMinor: 14_900/);
  assert.match(contract, /TEAM_MONTHLY/);
  assert.match(contract, /amountMinor: 39_900/);
  assert.match(pricing, /AXIGNAL_PRICE_BOOK\.plans\.professional/);
  assert.match(pricing, /AXIGNAL_PRICE_BOOK\.plans\.team/);
  assert.doesNotMatch(pricing, /€349|€899|€1,499|€18k|Design Partner|name: "Enterprise"/);
});

test("public landing removes source-brand identity while retaining bounded authority", async () => {
  const [profile, data, overrides, layout, browserTests] = await Promise.all([
    readFile(resolve(landingRoot, "lib/product-profile.ts"), "utf8"),
    readFile(resolve(landingRoot, "lib/landing-data.ts"), "utf8"),
    readFile(resolve(landingRoot, "app/contract-overrides.css"), "utf8"),
    readFile(resolve(landingRoot, "app/layout.tsx"), "utf8"),
    readFile(resolve(repoRoot, "tests/landing/landing.spec.ts"), "utf8"),
  ]);
  const publicSourceText = `${profile}\n${data}`;

  assert.doesNotMatch(publicSourceText, /Tenders Electronic Daily|EU_TED|TED bounded|perfil acotado de TED|profil TED/i);
  assert.match(publicSourceText, /ADMITTED_PUBLIC_SOURCE_PROFILE_01/);
  assert.match(publicSourceText, /Admitted European public-source profile/);
  assert.match(overrides, /\.status-ribbon span:first-child/);
  assert.match(overrides, /display: none/);
  assert.match(overrides, /ADMITTED PUBLIC-SOURCE PROFILE · PRIVATE AUTHENTICATED PILOT/);
  assert.match(layout, /contract-overrides\.css/);
  assert.match(browserTests, /does not expose the admitted source brand as public landing identity/);
});

test("B2G trial intake persists canonical schema, source and message version", async () => {
  const [contract, form, route] = await Promise.all([
    readFile(resolve(landingRoot, "lib/canonical-commercial-contract.ts"), "utf8"),
    readFile(resolve(landingRoot, "components/pilot-access-form.tsx"), "utf8"),
    readFile(resolve(landingRoot, "app/api/pilot-intake/route.ts"), "utf8"),
  ]);

  for (const marker of [
    "axignal.b2g-trial-intake.v1",
    "landing_b2g_opportunity_v1_0",
    "b2g-opportunity-v1.0",
  ]) {
    assert.match(contract, new RegExp(marker.replaceAll(".", "\\.")));
  }
  assert.match(form, /source: AXIGNAL_TRIAL_INTAKE\.source/);
  assert.match(form, /messageVersion: AXIGNAL_TRIAL_INTAKE\.messageVersion/);
  assert.match(form, /company:/);
  assert.match(form, /governmentOffer:/);
  assert.match(form, /qualificationBottleneck:/);
  assert.match(route, /messageVersion: typeof AXIGNAL_TRIAL_INTAKE\.messageVersion/);
  assert.match(route, /idempotencyKeyHash/);
  assert.match(route, /No success was recorded/);
  assert.match(route, /allowedPlans/);
});

test("browser assertions reject superseded copy and assert canonical commercial authority", async () => {
  const browserTests = await readFile(resolve(repoRoot, "tests/landing/landing.spec.ts"), "utf8");

  assert.match(browserTests, /Find the public contracts your business is built to pursue/);
  assert.match(browserTests, /Controlled Trial/);
  assert.match(browserTests, /€149/);
  assert.match(browserTests, /€399/);
  assert.match(browserTests, /Canonical price book · 2026-08-04/);
  assert.doesNotMatch(browserTests, /Win the right public opportunities/);
  assert.doesNotMatch(browserTests, /Indicative candidate pricing/);
  assert.doesNotMatch(browserTests, /name: "Design Partner" \}\)\.toBeVisible/);
});

test("landing stays fail-closed for indexing before launch authority", async () => {
  const [metadata, robots] = await Promise.all([
    readFile(resolve(landingRoot, "lib/metadata.ts"), "utf8"),
    readFile(resolve(landingRoot, "app/robots.ts"), "utf8"),
  ]);

  assert.match(metadata, /index: false/);
  assert.match(metadata, /follow: false/);
  assert.match(metadata, /noarchive: true/);
  assert.match(robots, /disallow: "\/"/);
  assert.doesNotMatch(robots, /sitemap:/);
});

test("landing metadata and fallback assets stay local and coherent", async () => {
  const [layout, manifest, globe] = await Promise.all([
    readFile(resolve(landingRoot, "app/layout.tsx"), "utf8"),
    readFile(resolve(landingRoot, "app/manifest.ts"), "utf8"),
    readFile(resolve(landingRoot, "components/semantic-globe.tsx"), "utf8"),
  ]);

  assert.equal(existsSync(resolve(landingRoot, "public/favicon.svg")), true);
  assert.match(layout, /url: "\/favicon\.svg"/);
  assert.match(layout, /B2G Opportunity Intelligence/);
  assert.match(manifest, /src: "\/favicon\.svg"/);
  assert.match(globe, /globe-canvas-fallback-text/);
  assert.match(globe, /onContextFailure/);
  assert.match(globe, /reducedMotion/);
  assert.match(globe, /europeanOpportunities/);
  assert.match(globe, /sphereGeometry args=\{\[0\.012, 12, 12\]\}/);
  assert.doesNotMatch(globe, /ActivityArcLayer|AuraGlyph|axignal-aura/);
});

test("landing package exposes a real contract test command", async () => {
  const packageJson = await readJson("apps/landing/package.json");
  assert.match(packageJson.scripts.test, /node --test/);
  assert.doesNotMatch(packageJson.scripts.test, /process\.exit\(0\)/);
});
