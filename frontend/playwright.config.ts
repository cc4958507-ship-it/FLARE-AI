import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests",
  timeout: 45000,
  workers: 1,
  use: {
    baseURL: process.env.FLARE_E2E_BASE_URL || "http://127.0.0.1:8100",
    headless: true,
    launchOptions: {
      ...(process.platform === 'win32' ? {channel:'chrome'} : {executablePath:'/usr/bin/chromium', args:['--no-sandbox']}),
    },
    trace: "retain-on-failure",
  },
  reporter: [["list"], ["json", { outputFile: "../work/e2e-results.json" }]],
  outputDir: "../work/playwright",
});
