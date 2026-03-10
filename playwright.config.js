// @ts-check
const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests",
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: process.env.BASE_URL || "https://kingdombuilders.ai/playbooks",
    ignoreHTTPSErrors: true,
  },
  reporter: [["list"], ["html", { open: "never" }]],
});
