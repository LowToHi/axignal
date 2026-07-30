#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { chromium } from "@playwright/test";

const BASE_URL = process.env.AXIGNAL_LANDING_URL ?? "http://localhost:3001/es";
const OUTPUT = path.resolve(process.cwd(), "output", "webgl-review");
let activeBrowser = null;
const SCENES = [
  ["SCENE_GLOBAL", 0],
  ["SCENE_EUROPE_START", 0.1],
  ["SCENE_EUROPE_CROSSFADE", 0.2],
  ["SCENE_EUROPE_LOD", 0.28],
  ["SCENE_FRAGMENTATION", 0.38],
  ["SCENE_EVIDENCE", 0.55],
  ["SCENE_INVESTIGATION", 0.72],
  ["SCENE_DOSSIER", 0.88]
];

async function runtimeSnapshot(page, progress) {
  return page.evaluate((normalisedProgress) => {
    const root = document.querySelector("[data-testid=semantic-globe]");
    const canvas = root?.querySelector("canvas");
    const bounds = canvas?.getBoundingClientRect();
    return {
      progress: normalisedProgress,
      url: location.href,
      viewport: [innerWidth, innerHeight],
      devicePixelRatio,
      canvasCss: bounds ? [bounds.width, bounds.height] : null,
      drawingBuffer: canvas ? [canvas.width, canvas.height] : null,
      runtime: window.__AXIGNAL_GLOBE_RUNTIME__ ?? null
    };
  }, progress);
}

async function moveToProgress(page, progress, settleMs = 500) {
  await page.evaluate((value) => {
    const stage = document.querySelector(".cinematic-stage");
    const spacer = stage?.closest(".pin-spacer");
    const target = spacer ?? document.querySelector(".cinematic-shell");
    if (!target) throw new Error("CINEMATIC_SCROLL_TARGET_MISSING");
    const bounds = target.getBoundingClientRect();
    const start = window.scrollY + bounds.top;
    const distance = Math.max(window.innerHeight, bounds.height - window.innerHeight);
    window.scrollTo(0, start + value * distance);
  }, progress);
  await page.waitForTimeout(settleMs);
}

async function captureSequence(browser) {
  const videoDirectory = path.join(OUTPUT, "video-raw");
  fs.mkdirSync(videoDirectory, { recursive: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1100 },
    deviceScaleFactor: 1,
    reducedMotion: "no-preference",
    recordVideo: { dir: videoDirectory, size: { width: 1280, height: 978 } }
  });
  const page = await context.newPage();
  const errors = [];
  page.setDefaultTimeout(12_000);
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));

  try {
    const response = await page.goto(BASE_URL, {
      waitUntil: "domcontentloaded",
      timeout: 12_000
    });
    if (!response?.ok()) throw new Error(`HTTP_${response?.status() ?? "NO_RESPONSE"}`);
    await page.waitForFunction(
      () =>
        document
          .querySelector("[data-testid=semantic-globe]")
          ?.getAttribute("data-texture-tier") !== "pending"
    );
    await page.waitForFunction(() => document.querySelectorAll(".pin-spacer").length === 1);
    await moveToProgress(page, 0, 500);

    for (let step = 0; step <= 36; step += 1) {
      await moveToProgress(page, (step / 36) * 0.92, 70);
    }

    const manifest = [];
    const sequenceDirectory = path.join(OUTPUT, "sequence");
    fs.mkdirSync(sequenceDirectory, { recursive: true });
    for (let index = 0; index < SCENES.length; index += 1) {
      const [name, progress] = SCENES[index];
      await moveToProgress(page, progress, 350);
      if (name === "SCENE_EUROPE_LOD") {
        await page.waitForFunction(
          () =>
            document
              .querySelector("[data-testid=semantic-globe]")
              ?.getAttribute("data-lod-active") === "true",
          null,
          { timeout: 12_000 }
        );
      }
      const filename = `${String(index + 1).padStart(2, "0")}-${name.toLowerCase()}.png`;
      await page.screenshot({ path: path.join(sequenceDirectory, filename) });
      manifest.push({
        scene: name,
        screenshot: `sequence/${filename}`,
        ...(await runtimeSnapshot(page, progress))
      });
    }

    fs.writeFileSync(
      path.join(OUTPUT, "sequence-manifest.json"),
      `${JSON.stringify({ baseUrl: BASE_URL, errors, scenes: manifest }, null, 2)}\n`
    );

    const video = page.video();
    await page.close();
    await context.close();
    if (video) {
      const generated = await video.path();
      fs.copyFileSync(generated, path.join(OUTPUT, "globe-scroll-complete.webm"));
    }
    return { errors, scenes: manifest.length };
  } catch (error) {
    await page.close().catch(() => {});
    await context.close().catch(() => {});
    throw error;
  }
}

async function captureComparison(browser, mode) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1100 },
    deviceScaleFactor: 1.5,
    reducedMotion: "no-preference"
  });
  const page = await context.newPage();
  page.setDefaultTimeout(12_000);

  if (mode === "before") {
    const legacyAlbedo = path.join(OUTPUT, "legacy-earth-albedo.webp");
    const legacyClouds = path.join(OUTPUT, "legacy-earth-clouds.webp");
    await page.route("**/globe/earth-albedo-high.webp", (route) =>
      route.fulfill({ path: legacyAlbedo, contentType: "image/webp" })
    );
    await page.route("**/globe/earth-clouds.webp", (route) =>
      route.fulfill({ path: legacyClouds, contentType: "image/webp" })
    );
    await page.route("**/globe/earth-europe-high.webp", (route) => route.abort("failed"));
    await page.route("**/globe/countries-110m.simplified.geojson", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/geo+json",
        body: '{"type":"FeatureCollection","features":[]}'
      })
    );
  }

  try {
    await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 12_000 });
    await page.waitForFunction(
      () =>
        document
          .querySelector("[data-testid=semantic-globe]")
          ?.getAttribute("data-texture-tier") === "desktop-high"
    );
    await page.waitForFunction(() => document.querySelectorAll(".pin-spacer").length === 1);
    await moveToProgress(page, 0.22, 1600);
    if (mode === "after") {
      await page.waitForFunction(
        () =>
          document
            .querySelector("[data-testid=semantic-globe]")
            ?.getAttribute("data-lod-active") === "true",
        null,
        { timeout: 12_000 }
      );
    }
    const filename = `comparison-${mode}.png`;
    await page.screenshot({ path: path.join(OUTPUT, filename) });
    const snapshot = await runtimeSnapshot(page, 0.22);
    return { mode, screenshot: filename, ...snapshot };
  } finally {
    await page.close().catch(() => {});
    await context.close().catch(() => {});
  }
}

async function main() {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  activeBrowser = browser;
  try {
    const comparisonOnly = process.argv.includes("--comparison-only");
    const sequenceOnly = process.argv.includes("--sequence-only");
    const sequence = comparisonOnly ? null : await captureSequence(browser);
    let comparison = null;
    if (!sequenceOnly) {
      const before = await captureComparison(browser, "before");
      const after = await captureComparison(browser, "after");
      comparison = { browser: "chromium-headless", before, after };
      fs.writeFileSync(
        path.join(OUTPUT, "comparison-manifest.json"),
        `${JSON.stringify(comparison, null, 2)}\n`
      );
    }
    console.log(JSON.stringify({ status: "PASS", sequence, comparison: Boolean(comparison) }));
  } finally {
    await browser.close().catch(() => {});
    activeBrowser = null;
  }
}

let timeoutHandle;
const hardTimeout = new Promise((_, reject) => {
  timeoutHandle = setTimeout(async () => {
    await activeBrowser?.close().catch(() => {});
    reject(new Error("CAPTURE_HARD_TIMEOUT_55000MS"));
  }, 55_000);
});

Promise.race([main(), hardTimeout])
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => clearTimeout(timeoutHandle));
