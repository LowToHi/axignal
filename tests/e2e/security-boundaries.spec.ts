import { expect, test, type TestInfo } from "@playwright/test";

function projectOrigin(testInfo: TestInfo): string {
  const baseURL = testInfo.project.use.baseURL;
  if (typeof baseURL !== "string")
    throw new Error("Playwright baseURL is required");
  return new URL(baseURL).origin;
}

test("rejects missing, cross-origin and cross-site web mutations", async ({
  request,
}, testInfo) => {
  const origin = projectOrigin(testInfo);

  const missing = await request.post("/api/auth/logout", {
    headers: { origin: "", "sec-fetch-site": "" },
  });
  expect(missing.status()).toBe(403);
  await expect(missing.json()).resolves.toMatchObject({
    code: "origin_required",
  });

  const crossOrigin = await request.post("/api/auth/logout", {
    headers: {
      origin: "https://attacker.example",
      "sec-fetch-site": "cross-site",
    },
  });
  expect(crossOrigin.status()).toBe(403);
  await expect(crossOrigin.json()).resolves.toMatchObject({
    code: "cross_origin_forbidden",
  });

  const crossSite = await request.post("/api/auth/logout", {
    headers: {
      origin,
      "sec-fetch-site": "same-site",
    },
  });
  expect(crossSite.status()).toBe(403);
  await expect(crossSite.json()).resolves.toMatchObject({
    code: "cross_site_forbidden",
  });
});

test("allows an exact-origin web mutation and hides legacy password login", async ({
  request,
}, testInfo) => {
  const origin = projectOrigin(testInfo);
  const headers = { origin, "sec-fetch-site": "same-origin" };

  const logout = await request.post("/api/auth/logout", { headers });
  expect(logout.status()).toBe(200);

  const login = await request.post("/api/auth/login", {
    headers,
    data: {
      email: "validation@example.test",
      password: "validation-ci-password",
    },
  });
  expect(login.status()).toBe(404);
});

test("publishes hardened web response headers", async ({ request }) => {
  const response = await request.get("/");
  expect(response.status()).toBe(200);
  const headers = response.headers();

  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["x-frame-options"]).toBe("DENY");
  expect(headers["cross-origin-opener-policy"]).toBe("same-origin");
  expect(headers["content-security-policy"]).toContain(
    "https://challenges.cloudflare.com",
  );
  expect(headers["content-security-policy"]).not.toContain("'unsafe-eval'");
  expect(headers["strict-transport-security"]).toContain("includeSubDomains");
});
