import { defineConfig, devices } from "@playwright/test";

const useDevelopmentServer = process.env.AXIGNAL_PLAYWRIGHT_DEV_SERVER === "true";
const useExternalServer = process.env.AXIGNAL_PLAYWRIGHT_EXTERNAL_SERVER === "true";
const baseURL = process.env.AXIGNAL_PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";
const publicOrigin = new URL(baseURL).origin;

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["html", { open: "never" }], ["list"]] : "list",
  use: {
    baseURL,
    extraHTTPHeaders: {
      origin: publicOrigin,
      "sec-fetch-site": "same-origin"
    },
    trace: "retain-on-failure",
    screenshot: "only-on-failure"
  },
  projects: [
    { name: "chromium-desktop", use: { ...devices["Desktop Chrome"] } },
    {
      name: "chromium-tablet",
      use: { ...devices["iPad Pro 11"], browserName: "chromium" }
    }
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
          AXIGNAL_LEGACY_PASSWORD_LOGIN_ENABLED: useDevelopmentServer ? "true" : "false"
        }
      }
});
