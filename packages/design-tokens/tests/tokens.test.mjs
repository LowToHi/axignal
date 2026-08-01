import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const css = await readFile(
  new URL("../src/tokens.css", import.meta.url),
  "utf8"
);

function tokenValue(name) {
  const match = css.match(new RegExp(`--${name}:\\s*([^;]+);`));
  assert.ok(match, `Missing design token --${name}`);
  return match[1].trim();
}

test("design system exposes the required semantic token surface", () => {
  const required = [
    "ax-bg-canvas",
    "ax-bg-panel",
    "ax-fg-primary",
    "ax-fg-secondary",
    "ax-border-default",
    "ax-brand-signal",
    "ax-support",
    "ax-contradiction",
    "ax-critical",
    "ax-font-ui",
    "ax-font-mono",
    "ax-radius-md",
    "ax-space-4",
    "ax-duration-base",
    "ax-ease-standard"
  ];

  for (const name of required) tokenValue(name);
});

test("dark and light themes expose explicit color-scheme contracts", () => {
  assert.match(css, /:root\s*{[^}]*color-scheme:\s*dark;/s);
  assert.match(css, /\[data-theme="light"\]\s*{[^}]*color-scheme:\s*light;/s);
  assert.notEqual(tokenValue("ax-bg-canvas"), tokenValue("ax-bg-panel"));
});

test("reduced-motion preference collapses every motion duration", () => {
  const reducedMotion = css.match(
    /@media\s*\(prefers-reduced-motion:\s*reduce\)\s*{([\s\S]+)}\s*$/
  );
  assert.ok(reducedMotion, "Missing reduced-motion contract");
  const block = reducedMotion[1];

  assert.match(block, /--ax-duration-fast:\s*1ms;/);
  assert.match(block, /--ax-duration-base:\s*1ms;/);
  assert.match(block, /--ax-duration-transform:\s*1ms;/);
});

test("spacing and radius tokens remain positive bounded CSS dimensions", () => {
  for (const name of [
    "ax-radius-xs",
    "ax-radius-sm",
    "ax-radius-md",
    "ax-radius-lg",
    "ax-space-1",
    "ax-space-2",
    "ax-space-3",
    "ax-space-4",
    "ax-space-6"
  ]) {
    assert.match(tokenValue(name), /^\d+(?:\.\d+)?(?:px|rem)$/);
  }
});
