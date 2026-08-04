#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const SOURCE_EXTENSIONS = new Set([
  ".js",
  ".jsx",
  ".mjs",
  ".cjs",
  ".ts",
  ".tsx",
  ".vue",
  ".svelte",
]);
const IGNORED_DIRECTORIES = new Set([
  ".git",
  ".next",
  ".turbo",
  "build",
  "coverage",
  "dist",
  "node_modules",
  "test-results",
]);

function makeIssue(severity, code, file, text, index, message) {
  const line = text.slice(0, Math.max(index, 0)).split(/\r?\n/u).length;
  return { severity, code, file, line, message };
}

function firstMatch(text, pattern) {
  const match = pattern.exec(text);
  pattern.lastIndex = 0;
  return match;
}

function auditSources(sources) {
  const issues = [];
  const gsapSources = sources.filter(({ text }) =>
    /\bgsap\.|["']gsap(?:\/|["'])|["']@gsap\/react["']|\bScrollTrigger\b/u.test(
      text,
    ),
  );

  if (gsapSources.length === 0) {
    return { issues, scanned: sources.length, gsapFiles: 0 };
  }

  const combined = gsapSources.map(({ text }) => text).join("\n");
  const reducedMotionPattern =
    /prefers-reduced-motion|gsap\.matchMedia|useReducedMotion|reduceMotion|reducedMotion|motionPreference|useAxignalMotion/u;

  if (!reducedMotionPattern.test(combined)) {
    const source = gsapSources[0];
    issues.push(
      makeIssue(
        "error",
        "reduced-motion-missing",
        source.file,
        source.text,
        0,
        "GSAP usage has no detectable reduced-motion strategy.",
      ),
    );
  }

  const registrationTargets = new Set();
  for (const { text } of gsapSources) {
    for (const match of text.matchAll(
      /import\s+(?:\{[^}]*\b([A-Z][A-Za-z0-9]*)\b[^}]*\}|([A-Z][A-Za-z0-9]*))\s+from\s+["']gsap\/([A-Za-z0-9]+)["']/gu,
    )) {
      registrationTargets.add(match[1] ?? match[2] ?? match[3]);
    }
    if (/from\s+["']@gsap\/react["']/u.test(text)) {
      registrationTargets.add("useGSAP");
    }
  }

  for (const plugin of registrationTargets) {
    const registered = new RegExp(
      String.raw`gsap\.registerPlugin\s*\([^)]*\b${plugin}\b[^)]*\)`,
      "u",
    ).test(combined);
    if (!registered) {
      const source =
        gsapSources.find(({ text }) => text.includes(plugin)) ?? gsapSources[0];
      issues.push(
        makeIssue(
          "error",
          "plugin-registration-missing",
          source.file,
          source.text,
          Math.max(source.text.indexOf(plugin), 0),
          `${plugin} is imported but no gsap.registerPlugin(${plugin}) call was found.`,
        ),
      );
    }
  }

  for (const source of gsapSources) {
    const { file, text } = source;
    const reactFile = /\.(?:jsx|tsx)$/u.test(file);
    const hasSelectorTarget =
      /\bgsap\.(?:to|from|fromTo|set|quickTo)\s*\(\s*["'`]/u.test(text);
    const usesScopedHook = /useGSAP\s*\([\s\S]*?\{[\s\S]*?\bscope\s*:/u.test(
      text,
    );
    const usesScopedContext =
      /gsap\.context\s*\([\s\S]*?,\s*[A-Za-z_$][\w$]*(?:\.current)?\s*\)/u.test(
        text,
      );
    const hasLifecycleCleanup =
      /useGSAP\s*\(|gsap\.context\s*\(|\.revert\s*\(|\.kill\s*\(/u.test(text);

    if (reactFile && !hasLifecycleCleanup) {
      issues.push(
        makeIssue(
          "error",
          "react-cleanup-missing",
          file,
          text,
          0,
          "React GSAP code has no detectable useGSAP, gsap.context, revert, or kill lifecycle.",
        ),
      );
    }

    if (
      reactFile &&
      hasSelectorTarget &&
      !usesScopedHook &&
      !usesScopedContext
    ) {
      const match = firstMatch(
        text,
        /\bgsap\.(?:to|from|fromTo|set|quickTo)\s*\(\s*["'`]/u,
      );
      issues.push(
        makeIssue(
          "error",
          "selector-scope-missing",
          file,
          text,
          match?.index ?? 0,
          "Selector-based React animation is not detectably scoped to a component root.",
        ),
      );
    }

    const hardFailures = [
      {
        code: "production-markers",
        pattern: /\bmarkers\s*:\s*true\b/u,
        message: "ScrollTrigger markers must not ship enabled.",
      },
      {
        code: "deprecated-match-media",
        pattern: /\bScrollTrigger\.matchMedia\s*\(/u,
        message: "Use gsap.matchMedia() instead of ScrollTrigger.matchMedia().",
      },
      {
        code: "legacy-private-registry",
        pattern: /npm\.greensock\.com|(?:GREENSOCK|GSAP)_AUTH_TOKEN/u,
        message:
          "Legacy private registries and GreenSock auth tokens are prohibited.",
      },
    ];

    for (const failure of hardFailures) {
      const match = firstMatch(text, failure.pattern);
      if (match) {
        issues.push(
          makeIssue(
            "error",
            failure.code,
            file,
            text,
            match.index,
            failure.message,
          ),
        );
      }
    }

    const warnings = [
      {
        code: "layout-property-animation",
        pattern:
          /\b(?:width|height|top|left|right|bottom|margin|padding)\s*:\s*(?:[+\-*/]?=)?["'`]?-?\d/u,
        message:
          "A layout-affecting property is animated; prefer transforms when behavior allows.",
      },
      {
        code: "infinite-motion",
        pattern: /\brepeat\s*:\s*-1\b/u,
        message:
          "Infinite motion requires a declared semantic owner, a stop mechanism, and reduced-motion fallback.",
      },
      {
        code: "scroll-smoother-review",
        pattern: /\bScrollSmoother\b/u,
        message:
          "ScrollSmoother requires explicit native-scroll, focus, anchor, reduced-motion, and low-end-device evidence.",
      },
      {
        code: "development-tools",
        pattern: /\bGSDevTools\b/u,
        message: "Verify GSDevTools is excluded from production bundles.",
      },
      {
        code: "blanket-force3d",
        pattern: /\bforce3D\s*:\s*true\b/u,
        message:
          "Avoid blanket force3D promotion; measure before retaining this optimization.",
      },
    ];

    for (const warning of warnings) {
      const match = firstMatch(text, warning.pattern);
      if (match) {
        issues.push(
          makeIssue(
            "warning",
            warning.code,
            file,
            text,
            match.index,
            warning.message,
          ),
        );
      }
    }
  }

  return { issues, scanned: sources.length, gsapFiles: gsapSources.length };
}

function collectSources(inputs) {
  const files = [];

  function visit(candidate) {
    const resolved = path.resolve(candidate);
    if (!fs.existsSync(resolved)) {
      throw new Error(`Path does not exist: ${candidate}`);
    }

    const stat = fs.lstatSync(resolved);
    if (stat.isSymbolicLink()) return;
    if (stat.isDirectory()) {
      if (IGNORED_DIRECTORIES.has(path.basename(resolved))) return;
      for (const entry of fs.readdirSync(resolved)) {
        visit(path.join(resolved, entry));
      }
      return;
    }

    if (stat.isFile() && SOURCE_EXTENSIONS.has(path.extname(resolved))) {
      files.push({
        file: path.relative(process.cwd(), resolved) || path.basename(resolved),
        text: fs.readFileSync(resolved, "utf8"),
      });
    }
  }

  for (const input of inputs) visit(input);
  return files;
}

function runSelfTest() {
  const compliant = [
    {
      file: "Compliant.tsx",
      text: `
        import { useRef } from "react";
        import { gsap } from "gsap";
        import { useGSAP } from "@gsap/react";
        gsap.registerPlugin(useGSAP);
        export function Compliant() {
          const root = useRef(null);
          useGSAP(() => {
            const media = gsap.matchMedia();
            media.add("(prefers-reduced-motion: no-preference)", () => {
              gsap.to(".target", { x: 12, autoAlpha: 1 });
            });
            return () => media.revert();
          }, { scope: root });
          return <div ref={root}><span className="target" /></div>;
        }
      `,
    },
  ];
  const unsafe = [
    {
      file: "Unsafe.tsx",
      text: `
        import { gsap } from "gsap";
        import { ScrollTrigger } from "gsap/ScrollTrigger";
        const legacyRegistry = "https://npm.greensock.com";
        export function Unsafe() {
          gsap.to(".target", {
            left: 100,
            repeat: -1,
            scrollTrigger: { markers: true }
          });
          return <div className="target" />;
        }
      `,
    },
  ];

  const compliantResult = auditSources(compliant);
  const unsafeResult = auditSources(unsafe);
  const unsafeCodes = new Set(unsafeResult.issues.map(({ code }) => code));
  const requiredCodes = [
    "reduced-motion-missing",
    "plugin-registration-missing",
    "react-cleanup-missing",
    "selector-scope-missing",
    "production-markers",
    "legacy-private-registry",
  ];

  if (
    compliantResult.issues.some(({ severity }) => severity === "error") ||
    requiredCodes.some((code) => !unsafeCodes.has(code))
  ) {
    console.error("AXIGNAL GSAP motion auditor self-test FAILED");
    console.error(
      JSON.stringify({ compliantResult, unsafeResult, requiredCodes }, null, 2),
    );
    return 1;
  }

  console.log(
    `AXIGNAL GSAP motion auditor self-test PASS (${requiredCodes.length} unsafe patterns rejected)`,
  );
  return 0;
}

function printHuman(result) {
  if (result.gsapFiles === 0) {
    console.log(
      `AXIGNAL GSAP motion audit SKIP (${result.scanned} source files, no GSAP usage)`,
    );
    return;
  }

  const order = { error: 0, warning: 1 };
  for (const issue of [...result.issues].sort(
    (a, b) =>
      order[a.severity] - order[b.severity] ||
      a.file.localeCompare(b.file) ||
      a.line - b.line,
  )) {
    console.log(
      `${issue.severity.toUpperCase()} ${issue.code} ${issue.file}:${issue.line} ${issue.message}`,
    );
  }

  const errors = result.issues.filter(
    ({ severity }) => severity === "error",
  ).length;
  const warnings = result.issues.length - errors;
  console.log(
    `AXIGNAL GSAP motion audit ${errors ? "FAIL" : "PASS"} (${result.gsapFiles} GSAP files, ${errors} errors, ${warnings} warnings)`,
  );
}

const args = process.argv.slice(2);
if (args.includes("--self-test")) {
  process.exitCode = runSelfTest();
} else {
  const json = args.includes("--json");
  const inputs = args.filter((arg) => arg !== "--json");

  if (inputs.length === 0) {
    console.error(
      "Usage: node audit-gsap-motion.mjs [--json] <file-or-directory> [...]\n       node audit-gsap-motion.mjs --self-test",
    );
    process.exitCode = 2;
  } else {
    try {
      const result = auditSources(collectSources(inputs));
      if (json) {
        console.log(JSON.stringify(result, null, 2));
      } else {
        printHuman(result);
      }
      process.exitCode = result.issues.some(
        ({ severity }) => severity === "error",
      )
        ? 1
        : 0;
    } catch (error) {
      console.error(`AXIGNAL GSAP motion audit ERROR: ${error.message}`);
      process.exitCode = 2;
    }
  }
}
