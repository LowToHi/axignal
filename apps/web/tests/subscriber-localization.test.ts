import assert from "node:assert/strict";
import test from "node:test";

import {
  localeNames,
  shellCopy,
  shellLocales,
} from "../components/subscriber/subscriber-localization";

const expectedLocales = ["en", "es", "fr", "de", "pt", "it"];
const criticalNavigationKeys = [
  "commandCenter",
  "opportunities",
  "workspaces",
  "settings",
  "methodology",
  "help",
] as const;

test("defines exactly the six contracted subscriber locales", () => {
  assert.deepEqual([...shellLocales], expectedLocales);
  assert.equal(new Set(Object.values(localeNames)).size, expectedLocales.length);
});

test("keeps Shell and Intelligence catalogs structurally exhaustive", () => {
  const englishNavKeys = Object.keys(shellCopy.en.nav).sort();
  const englishSectionKeys = Object.keys(shellCopy.en.sections).sort();
  const englishIntelligenceKeys = Object.keys(shellCopy.en.intelligence).sort();

  for (const locale of shellLocales) {
    const copy = shellCopy[locale];
    assert.deepEqual(Object.keys(copy.nav).sort(), englishNavKeys);
    assert.deepEqual(Object.keys(copy.sections).sort(), englishSectionKeys);
    assert.deepEqual(
      Object.keys(copy.intelligence).sort(),
      englishIntelligenceKeys,
    );
    assert.equal(copy.readiness(68).includes("68"), true);
    assert.equal(copy.blockingRequirements(3).includes("3"), true);
    assert.equal(copy.currentOrganisation("AXIGNAL").includes("AXIGNAL"), true);
    assert.equal(copy.accountMenuFor("Rafael").includes("Rafael"), true);

    for (const value of [
      ...Object.values(copy.nav),
      ...Object.values(copy.sections),
      ...Object.values(copy.intelligence),
      copy.productNavigation,
      copy.searchTrigger,
      copy.searchCommand,
      copy.accountMenu,
      copy.signOut,
    ]) {
      assert.equal(value.trim().length > 0, true);
    }
  }
});

test("translates critical Shell semantics instead of changing route authority", () => {
  for (const locale of shellLocales.filter((value) => value !== "en")) {
    for (const key of criticalNavigationKeys) {
      assert.notEqual(shellCopy[locale].nav[key], shellCopy.en.nav[key]);
    }
    assert.notEqual(shellCopy[locale].searchCommand, shellCopy.en.searchCommand);
    assert.notEqual(shellCopy[locale].accountSettings, shellCopy.en.accountSettings);
    assert.notEqual(shellCopy[locale].signOut, shellCopy.en.signOut);
  }
});
