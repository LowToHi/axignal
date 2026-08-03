import { defineConfig, devices } from "@playwright/test";

const useDevelopmentServer =
  process.env.AXIGNAL_PLAYWRIGHT_DEV_SERVER === "true";
const useExternalServer =
  process.env.AXIGNAL_PLAYWRIGHT_EXTERNAL_SERVER === "true";
const baseURL =
  process.env.AXIGNAL_PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";
const publicOrigin = new URL(baseURL).origin;

export default defineConfig({
  testDir: "./tests/e2e",
  // AXIGNAL Globe uses shared WebGL resources; one worker keeps candidate E2E deterministic.
  workers: 1,
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  // Critical E2E must pass on its first execution; retries may not conceal flakiness.
  retries: 0,
  reporter: process.env.CI ? [["html", { open: "never" }], ["list"]] : "list",
  use: {
    baseURL,
    extraHTTPHeaders: {
      origin: publicOrigin,
      "sec-fetch-site": "same-origin",
    },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium-desktop", use: { ...devices["Desktop Chrome"] } },
    {
      name: "chromium-tablet",
      use: { ...devices["iPad Pro 11"], browserName: "chromium" },
    },
  ],
  webServer: useExternalServer
    ? undefined
    : {
        command: useDevelopmentServer
          ? "pnpm --filter @axignal/web dev"
          : process.env.CI
            ? "pnpm --filter @axignal/web start"
            : "pnpm --filter @axignal/web dev",
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
        env: {
          AXIGNAL_PUBLIC_ORIGIN: publicOrigin,
          AXIGNAL_LEGACY_PASSWORD_LOGIN_ENABLED: useDevelopmentServer
            ? "true"
            : "false",
          // The subscriber candidate must be explicitly enabled in browser acceptance.
          // Fixture mode remains fail-closed and is admitted only in this non-production test runtime.
          AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED: "true",
          AXIGNAL_SUBSCRIBER_WORKSPACE_FIXTURE_MODE: "explicit",
          AXIGNAL_SUBSCRIBER_WORKSPACE_ENVIRONMENT: process.env.CI
            ? "test"
            : "development",
          AXIGNAL_AXENT_ASSISTANT_DEEPSEEK_ENABLED: "false",
        },
      },
});
