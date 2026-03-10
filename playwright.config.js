// @ts-check
const { defineConfig, devices } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests",
  timeout: 45000,
  retries: 1,
  use: {
    baseURL: process.env.BASE_URL || "https://kingdombuilders.ai/playbooks",
    ignoreHTTPSErrors: true,
  },
  reporter: [["list"], ["html", { open: "never" }]],
  projects: [
    // Desktop browsers
    {
      name: "chrome-desktop",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "safari-desktop",
      use: { ...devices["Desktop Safari"] },
    },
    // Mobile
    {
      name: "android-mobile",
      use: { ...devices["Pixel 7"] },
    },
    {
      name: "ios-mobile",
      use: { ...devices["iPhone 14"] },
    },
    // Tablet
    {
      name: "ipad",
      use: { ...devices["iPad (gen 7)"] },
    },
  ],
});
