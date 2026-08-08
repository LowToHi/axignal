import { defineConfig } from "@playwright/test";

const devServer = process.env.AXIGNAL_LANDING_PLAYWRIGHT_DEV_SERVER === "true";

export default defineConfig({
  testDir: ".",
  testMatch: ["landing.spec.ts", "security-boundaries.spec.ts"],
  fullyParallel: false,
  workers: 1,
  timeout: 25_000,
  globalTimeout: 300_000,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3001",
    viewport: { width: 1440, height: 900 },
    actionTimeout: 15_000,
    navigationTimeout: 15_000,
    trace: "off",
    screenshot: "off",
    video: "off"
  },
  webServer: devServer
    ? undefined
    : {
        command:
          "cd D:/AXIGNAL/AXIGNAL_E2E && pnpm --dir apps/landing build && cd apps/landing && npx next start --port 3001",
        url: "http://127.0.0.1:3001",
        reuseExistingServer: !process.env.CI,
        timeout: 240_000,
        env: {
          NODE_ENV: "production",
          AXIGNAL_PUBLIC_ORIGIN: "http://127.0.0.1:3001"
        }
      },
  projects: [
    { name: "landing-desktop", use: { viewport: { width: 1440, height: 900 } } },
    { name: "landing-mobile", use: { viewport: { width: 390, height: 844 }, isMobile: true } }
  ]
});
