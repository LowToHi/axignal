import assert from "node:assert/strict";
import test from "node:test";

import {
  authCopy,
  humanizeAuthError,
} from "../components/auth-localization";
import { shellLocales } from "../components/subscriber/subscriber-localization";

const modes = ["login", "signup", "recovery"];

test("keeps the authentication catalog exhaustive for every supported locale", () => {
  const englishKeys = Object.keys(authCopy.en).sort();

  for (const locale of shellLocales) {
    const copy = authCopy[locale];
    assert.deepEqual(Object.keys(copy).sort(), englishKeys);
    assert.deepEqual(Object.keys(copy.tabs).sort(), modes);
    assert.equal(copy.trustItems.length, 3);

    for (const value of [
      copy.workspaceLabel,
      copy.pageFooter,
      copy.cardTitle,
      copy.cardBody,
      copy.loginButton,
      copy.registrationCancelled,
      copy.authenticationCancelled,
      ...copy.trustItems,
      ...Object.values(copy.tabs),
    ]) {
      assert.equal(value.trim().length > 0, true);
    }
  }
});

test("does not leak raw WebAuthn browser diagnostics to the user", () => {
  const raw = new Error(
    "The operation either timed out or was not allowed. See: https://www.w3.org/TR/webauthn-2/#sctn-privacy-considerations-client.",
  );

  for (const locale of shellLocales) {
    const message = humanizeAuthError(
      locale,
      raw,
      "loginFailed",
      "authentication",
    );
    assert.equal(/w3\.org|timed out or was not allowed/i.test(message), false);
    assert.equal(message, authCopy[locale].authenticationCancelled);
  }
});

test("localizes the access experience instead of silently falling back to English", () => {
  for (const locale of shellLocales.filter((value) => value !== "en")) {
    assert.notEqual(authCopy[locale].cardTitle, authCopy.en.cardTitle);
    assert.notEqual(authCopy[locale].loginButton, authCopy.en.loginButton);
    assert.notEqual(authCopy[locale].errorTitle, authCopy.en.errorTitle);
  }
});
