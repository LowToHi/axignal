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

test("landing metadata and fallback assets stay local and coherent", async () => {
  const [layout, manifest, globe] = await Promise.all([
    readFile(resolve(landingRoot, "app/layout.tsx"), "utf8"),
    readFile(resolve(landingRoot, "app/manifest.ts"), "utf8"),
    readFile(resolve(landingRoot, "components/semantic-globe.tsx"), "utf8"),
  ]);

  assert.equal(existsSync(resolve(landingRoot, "public/favicon.svg")), true);
  assert.match(layout, /url: "\/favicon\.svg"/);
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
