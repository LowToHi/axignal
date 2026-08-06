#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const ROOT = process.cwd();

function requireCondition(condition, message, failures) {
  if (!condition) failures.push(message);
}

function webpDimensions(buffer) {
  if (buffer.toString("ascii", 0, 4) !== "RIFF" || buffer.toString("ascii", 8, 12) !== "WEBP") {
    throw new Error("NOT_WEBP");
  }
  const chunk = buffer.toString("ascii", 12, 16);
  if (chunk === "VP8X") {
    return [1 + buffer.readUIntLE(24, 3), 1 + buffer.readUIntLE(27, 3)];
  }
  if (chunk === "VP8 ") {
    const marker = buffer.indexOf(Buffer.from([0x9d, 0x01, 0x2a]), 20);
    if (marker < 0) throw new Error("VP8_DIMENSIONS_NOT_FOUND");
    return [buffer.readUInt16LE(marker + 3) & 0x3fff, buffer.readUInt16LE(marker + 5) & 0x3fff];
  }
  if (chunk === "VP8L") {
    const bits = buffer.readUInt32LE(21);
    return [(bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1];
  }
  throw new Error(`UNSUPPORTED_WEBP_CHUNK_${chunk}`);
}

function auditSource({ globe, rendering, css, provenance, assets }) {
  const failures = [];
  const implementation = `${globe}\n${rendering}`;
  const requiredGlobePatterns = [
    ["desktop-high tier", /desktop-high/],
    ["regional texture", /earth-europe/],
    ["shader LOD blend", /axRegionalMix/],
    ["Europe LOD bounds", /EUROPE_LOD_BOUNDS/],
    ["vector boundaries", /countries-110m\.simplified\.geojson/],
    ["Europe 50m vector LOD", /europe-boundaries-50m\.geojson/],
    ["adaptive DPR", /setDpr/],
    ["DPR hysteresis windows", /lowWindows/],
    ["offscreen frame control", /IntersectionObserver/],
    ["instanced markers", /instancedMesh/],
    ["effective DPR telemetry", /data-effective-dpr/],
    ["drawing buffer telemetry", /data-drawing-buffer/],
    ["LOD state telemetry", /data-lod-active/],
    ["boundary LOD telemetry", /data-boundary-lod-active/]
  ];
  for (const [label, pattern] of requiredGlobePatterns) {
    requireCondition(pattern.test(implementation), `missing ${label}`, failures);
  }

  requireCondition(!/dpr=\{\[1,\s*1\.5\]\}/.test(globe), "fixed DPR [1, 1.5] remains", failures);
  requireCondition(
    !/fallback=\{<div className="globe-fallback"/.test(globe),
    "poster-capable fallback remains inside healthy Canvas",
    failures
  );
  requireCondition(/selectGlobeTextureTier/.test(rendering), "tier selector missing", failures);
  requireCondition(/estimateTextureMemoryMb/.test(rendering), "texture memory estimator missing", failures);
  requireCondition(/\.globe-poster\s*\{[\s\S]*globe-poster\.webp/.test(css), "poster fallback style missing", failures);
  requireCondition(
    !/\.globe-(?:fallback|initialising)[^{]*\{[^}]*globe-poster\.webp/s.test(css),
    "healthy/checking fallback references poster",
    failures
  );
  requireCondition(
    provenance.includes("BLOCKED_NO_PINNED_ENCODER"),
    "KTX2 encoder state is not recorded",
    failures
  );
  requireCondition(/"rights"/.test(provenance), "asset rights records missing", failures);

  const minimums = new Map([
    ["earth-albedo-mobile.webp", [2048, 1024]],
    ["earth-albedo.webp", [4096, 2048]],
    ["earth-albedo-high.webp", [5400, 2700]],
    ["earth-europe-mobile.webp", [1024, 600]],
    ["earth-europe.webp", [2048, 1200]],
    ["earth-europe-high.webp", [3072, 1800]],
    ["earth-clouds-mobile.webp", [1024, 512]],
    ["earth-clouds.webp", [2048, 1024]]
  ]);
  for (const [name, [minimumWidth, minimumHeight]] of minimums) {
    const buffer = assets.get(name);
    requireCondition(Boolean(buffer), `missing texture ${name}`, failures);
    if (!buffer) continue;
    const [width, height] = webpDimensions(buffer);
    requireCondition(
      width >= minimumWidth && height >= minimumHeight,
      `${name} is ${width}x${height}; expected at least ${minimumWidth}x${minimumHeight}`,
      failures
    );
  }
  return failures;
}

function selfTest() {
  const asset = fs.readFileSync(
    path.join(ROOT, "apps", "landing", "public", "globe", "earth-albedo.webp")
  );
  const assets = new Map([
    ["earth-albedo-mobile.webp", asset],
    ["earth-albedo.webp", asset],
    ["earth-albedo-high.webp", asset],
    ["earth-europe-mobile.webp", asset],
    ["earth-europe.webp", asset],
    ["earth-europe-high.webp", asset],
    ["earth-clouds-mobile.webp", asset],
    ["earth-clouds.webp", asset]
  ]);
  const safe = auditSource({
    globe:
      "desktop-high earth-europe axRegionalMix EUROPE_LOD_BOUNDS countries-110m.simplified.geojson europe-boundaries-50m.geojson setDpr lowWindows IntersectionObserver instancedMesh data-effective-dpr data-drawing-buffer data-lod-active data-boundary-lod-active",
    rendering: "selectGlobeTextureTier estimateTextureMemoryMb",
    css: '.globe-poster { background:url("/globe/globe-poster.webp") }',
    provenance: '{"rights":"documented","ktx2":"BLOCKED_NO_PINNED_ENCODER"}',
    assets
  });
  const unsafe = auditSource({
    globe: 'dpr={[1, 1.5]} fallback={<div className="globe-fallback"/>}',
    rendering: "",
    css: '.globe-fallback { background:url("/globe/globe-poster.webp") }',
    provenance: "{}",
    assets: new Map()
  });
  requireCondition(unsafe.length >= 8, "unsafe fixture was not rejected", safe);
  return safe.filter((failure) => !failure.includes("expected at least"));
}

function main() {
  const failures = process.argv.includes("--self-test")
    ? selfTest()
    : auditSource({
        globe: fs.readFileSync(
          path.join(ROOT, "apps", "landing", "components", "semantic-globe.tsx"),
          "utf8"
        ),
        rendering: fs.readFileSync(
          path.join(ROOT, "apps", "landing", "lib", "globe-rendering.ts"),
          "utf8"
        ),
        css: fs.readFileSync(path.join(ROOT, "apps", "landing", "app", "globals.css"), "utf8"),
        provenance: fs.readFileSync(
          path.join(ROOT, "docs", "landing", "asset-provenance.generated.json"),
          "utf8"
        ),
        assets: new Map(
          fs
            .readdirSync(path.join(ROOT, "apps", "landing", "public", "globe"))
            .filter((name) => name.endsWith(".webp"))
            .map((name) => [
              name,
              fs.readFileSync(path.join(ROOT, "apps", "landing", "public", "globe", name))
            ])
        )
      });

  if (failures.length) {
    console.error(JSON.stringify({ status: "FAIL", failures }, null, 2));
    return 1;
  }
  console.log(JSON.stringify({ status: "PASS", gate: "AX-WEBGL-LANDING-GATE" }));
  return 0;
}

process.exitCode = main();
