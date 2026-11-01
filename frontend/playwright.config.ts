import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  retries: 0,
  use: { baseURL: "http://127.0.0.1:5174", channel: "chrome", headless: true },
  webServer: [
    {
      command: "../.venv/bin/python ../scripts/e2e_server.py",
      url: "http://127.0.0.1:8011/api/health",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --port 5174",
      url: "http://127.0.0.1:5174",
      reuseExistingServer: false,
      env: { RULEREPLAY_API_TARGET: "http://127.0.0.1:8011" },
    },
  ],
});
