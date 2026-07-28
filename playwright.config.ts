import { defineConfig, devices } from "@playwright/test";

const useDevelopmentServer = process.env.AXIGNAL_PLAYWRIGHT_DEV_SERVER === "true";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["html", { open: "never" }], ["list"]] : "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure"
  },
  projects: [
    { name: "chromium-desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "chromium-tablet", use: { ...devices["iPad Pro 11"] } }
  ],
  webServer: {
    command: useDevelopmentServer
      ? "pnpm --filter @axignal/web dev"
      : process.env.CI
        ? "pnpm --filter @axignal/web start"
        : "pnpm --filter @axignal/web dev",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000
  }
});
