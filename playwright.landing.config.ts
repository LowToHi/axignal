import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/landing",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["html", { open: "never" }], ["list"]] : "list",
  use: {
    baseURL: "http://127.0.0.1:3001",
    trace: "retain-on-failure",
    screenshot: "only-on-failure"
  },
  projects: [
    { name: "landing-desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "landing-mobile", use: { ...devices["Pixel 7"] } }
  ],
  webServer: {
    command: process.env.CI
      ? "pnpm --filter @axignal/landing start"
      : "pnpm --filter @axignal/landing dev",
    url: "http://127.0.0.1:3001",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000
  }
});
