import { defineConfig } from "@playwright/test";
export default defineConfig({ testDir: "./tests/e2e", use: { baseURL: process.env.E2E_BASE_URL || "http://localhost:3000" }, webServer: process.env.CI ? undefined : { command: "npm run dev", port: 3000, reuseExistingServer: true } });
