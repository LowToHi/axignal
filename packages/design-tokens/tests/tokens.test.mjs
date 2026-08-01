import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const css = await readFile(new URL("../src/tokens.css", import.meta.url), "utf8");

function block(pattern, label) {
  const match = css.match(pattern);
  assert.ok(match, `${label} block is required`);
  return match[1];
}

function declarations(source) {
  return [...source.matchAll(/(--ax-[a-z0-9-]+)\s*:\s*([^;]+);/g)].map(
    ([, name, value]) => [name, value.trim()]
  );
}

function declarationMap(source) {
  return new Map(declarations(source));
}

const rootBlock = block(/:root\s*\{([\s\S]*?)\}/, ":root");
const lightBlock = block(
  /\[data-theme="light"\]\s*\{([\s\S]*?)\}/,
  "light theme"
);
const reducedMotionBlock = block(
  /@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{[\s\S]*?:root\s*\{([\s\S]*?)\}\s*\}/,
  "reduced motion"
);

const semanticColourTokens = [
  "--ax-bg-canvas",
  "--ax-bg-panel",
  "--ax-bg-raised",
  "--ax-bg-active",
  "--ax-fg-primary",
  "--ax-fg-secondary",
  "--ax-fg-tertiary",
  "--ax-border-subtle",
  "--ax-border-default",
  "--ax-brand-signal",
  "--ax-selection",
  "--ax-support",
  "--ax-contradiction",
  "--ax-inferred",
  "--ax-critical",
  "--ax-unknown"
];

test("the root theme defines every semantic, typography, radius and motion token", () => {
  const root = declarationMap(rootBlock);
  const required = [
    ...semanticColourTokens,
    "--ax-font-ui",
    "--ax-font-mono",
    "--ax-radius-xs",
    "--ax-radius-sm",
    "--ax-radius-md",
    "--ax-radius-lg",
    "--ax-space-1",
    "--ax-space-2",
    "--ax-space-3",
    "--ax-space-4",
    "--ax-space-6",
    "--ax-duration-fast",
    "--ax-duration-base",
    "--ax-duration-transform",
    "--ax-ease-standard"
  ];

  for (const token of required) assert.ok(root.has(token), `${token} is required`);
  assert.match(css, /:root\s*\{\s*color-scheme:\s*dark;/);
});

test("token names are unique inside each theme scope", () => {
  for (const [label, source] of [
    ["root", rootBlock],
    ["light", lightBlock],
    ["reduced motion", reducedMotionBlock]
  ]) {
    const names = declarations(source).map(([name]) => name);
    assert.equal(
      new Set(names).size,
      names.length,
      `${label} contains duplicate token declarations`
    );
  }
});

test("light mode overrides every semantic colour with a valid six-digit hex value", () => {
  const light = declarationMap(lightBlock);
  assert.match(css, /\[data-theme="light"\]\s*\{\s*color-scheme:\s*light;/);

  for (const token of semanticColourTokens) {
    assert.ok(light.has(token), `${token} must be overridden in light mode`);
    assert.match(light.get(token), /^#[0-9a-f]{6}$/i, `${token} must use a hex colour`);
  }
});

test("default semantic colours are valid six-digit hex values", () => {
  const root = declarationMap(rootBlock);
  for (const token of semanticColourTokens) {
    assert.match(root.get(token), /^#[0-9a-f]{6}$/i, `${token} must use a hex colour`);
  }
});

test("reduced-motion mode collapses all declared animation durations", () => {
  const reduced = declarationMap(reducedMotionBlock);
  assert.deepEqual(Object.fromEntries(reduced), {
    "--ax-duration-fast": "1ms",
    "--ax-duration-base": "1ms",
    "--ax-duration-transform": "1ms"
  });
});
