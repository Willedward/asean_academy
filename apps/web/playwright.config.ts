import { defineConfig, devices } from "@playwright/test";

const databaseUrl = process.env.E2E_DATABASE_URL;
if (!databaseUrl) throw new Error("Set E2E_DATABASE_URL to a prepared disposable database.");

export const e2eSecret = "asean-academy-local-e2e-secret-2026-only";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  timeout: 60_000,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "uv run --project ../../services/learning_api --locked uvicorn learning_api.main:app --host 127.0.0.1 --port 8100",
      port: 8100,
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        ASEAN_ACADEMY_ALLOW_DRAFT_CONTENT: "true",
        ASEAN_ACADEMY_CORS_ORIGINS: "http://127.0.0.1:3100",
        ASEAN_ACADEMY_DATABASE_URL: databaseUrl,
        ASEAN_ACADEMY_DEVELOPMENT_LEARNER_ID: "",
        ASEAN_ACADEMY_E2E_AUTH_SECRET: e2eSecret,
        ASEAN_ACADEMY_ENV: "test",
        ASEAN_ACADEMY_REPOSITORY_ROOT: "../..",
      },
    },
    {
      command: "corepack pnpm dev --hostname 127.0.0.1 --port 3100",
      port: 3100,
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        ASEAN_ACADEMY_E2E_AUTH_SECRET: e2eSecret,
        ASEAN_ACADEMY_ENV: "test",
        LEARNING_API_URL: "http://127.0.0.1:8100",
        NEXT_PUBLIC_USE_API_FIXTURES: "false",
      },
    },
  ],
});
