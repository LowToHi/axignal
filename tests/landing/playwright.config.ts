import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: "landing.spec.ts",
  fullyParallel: false,
  workers: 1,
  timeout: 10_000,
  globalTimeout: 50_000,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3001",
    viewport: { width: 1440, height: 1000 },
    actionTimeout: 10_000,
    navigationTimeout: 10_000,
    trace: "off",
    screenshot: "off",
    video: "off"
  }
});
