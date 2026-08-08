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
    {
      name: "chromium-mobile",
      testMatch: /subscriber-.*\.spec\.ts/,
      use: { ...devices["iPhone 13"], browserName: "chromium" },
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
          AXIGNAL_TEST_RUNTIME_ENABLED: "true",
          // Only this internal aggregate suite keeps the canonical InvestigationShell
          // at `/`; external P21/P25/P26 topologies must exercise their real auth root.
          AXIGNAL_CANONICAL_LEGACY_ROOT_TEST_ENABLED: "true",
          AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED: "true",
          AXIGNAL_SUBSCRIBER_WORKSPACE_FIXTURE_MODE: "explicit",
          AXIGNAL_SUBSCRIBER_WORKSPACE_ENVIRONMENT: process.env.CI
            ? "test"
            : "development",
          AXIGNAL_AXENT_ASSISTANT_DEEPSEEK_ENABLED: "false",
          // Test-runtime legacy identity so the AXENT assistant E2E can
          // exercise the REAL browser -> Next proxy -> FastAPI -> PostgreSQL
          // path (login then grounded conversation).
          AXIGNAL_AUTH_REQUIRED: "true",
          AXIGNAL_AUTH_EMAIL: "test-runtime@axignal.test",
          AXIGNAL_AUTH_SUBJECT: "test-runtime-subject",
          AXIGNAL_AUTH_TENANT_ID: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
          AXIGNAL_SESSION_SECRET: "local-dev-session-secret-32-bytes-minimum!",
          AXIGNAL_AUTH_PASSWORD_SCRYPT:
            "scrypt$a1b2c3d4e5f60718293a4b5c6d7e8f90$f7287b6c2d361d0b0357d4ec8b691fa91ba2699dcf571a09c98c415fd4b7930d",
        },
      },
});
