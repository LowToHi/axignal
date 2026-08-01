import { expect, test, type TestInfo } from "@playwright/test";

function projectOrigin(testInfo: TestInfo): string {
  const baseURL = testInfo.project.use.baseURL;
  if (typeof baseURL !== "string") throw new Error("Playwright baseURL is required");
  return new URL(baseURL).origin;
}

const invalidIntake = {
  email: "invalid",
  role: "Other",
  company: "Example",
  useCase: "too short",
  consent: false,
  website: "",
  messageVersion: "b2g-opportunity-v1.0"
};

test("rejects missing and cross-origin landing mutations", async (
  { request },
  testInfo
) => {
  const missing = await request.post("/api/pilot-intake", { data: invalidIntake });
  expect(missing.status()).toBe(403);
  await expect(missing.json()).resolves.toMatchObject({ code: "origin_required" });

  const crossOrigin = await request.post("/api/pilot-intake", {
    headers: {
      origin: "https://attacker.example",
      "sec-fetch-site": "cross-site"
    },
    data: invalidIntake
  });
  expect(crossOrigin.status()).toBe(403);
  await expect(crossOrigin.json()).resolves.toMatchObject({
    code: "cross_origin_forbidden"
  });

  const sameOrigin = await request.post("/api/pilot-intake", {
    headers: {
      origin: projectOrigin(testInfo),
      "sec-fetch-site": "same-origin"
    },
    data: invalidIntake
  });
  expect(sameOrigin.status()).toBe(422);
});

test("publishes hardened landing response headers", async ({ request }) => {
  const response = await request.get("/");
  expect(response.status()).toBe(200);
  const headers = response.headers();

  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["x-frame-options"]).toBe("DENY");
  expect(headers["cross-origin-opener-policy"]).toBe("same-origin");
  expect(headers["content-security-policy"]).toContain(
    "https://challenges.cloudflare.com"
  );
  expect(headers["content-security-policy"]).not.toContain("'unsafe-eval'");
  expect(headers["strict-transport-security"]).toContain("includeSubDomains");
});
