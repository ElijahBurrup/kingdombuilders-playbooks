// @ts-check
const { test, expect } = require("@playwright/test");

const PROD = "https://kingdombuilders.ai/playbooks";
const TEST_EMAIL = "elijahburrup323@gmail.com";
const TEST_PASSWORD = "Eli624462!";

test.describe.configure({ mode: "serial" });

test.describe("Sign Out flow on production", () => {
  test("Sign in, then sign out, observe what happens", async ({ page }) => {
    page.on("console", (msg) => {
      if (msg.type() === "error") console.log("PAGE ERROR:", msg.text());
    });

    // 1. Sign in via the auth form
    await page.goto(PROD + "/auth");
    await page.locator('input[type="email"]').first().fill(TEST_EMAIL);
    await page.locator('input[type="password"]').first().fill(TEST_PASSWORD);
    await Promise.all([
      page.waitForURL((url) => !url.toString().includes("/auth"), { timeout: 10000 }),
      page.locator('button[type="submit"]', { hasText: /sign in|log in/i }).first().click(),
    ]);
    console.log("AFTER SIGN IN URL:", page.url());

    // 2. Confirm we're signed in: Sign Out button should appear on the homepage
    await page.goto(PROD + "/");
    const signOutBtn = page
      .locator("button.nav-button", { hasText: "Sign Out" })
      .first();
    await expect(signOutBtn).toBeVisible({ timeout: 8000 });
    console.log("SIGN OUT BUTTON VISIBLE — confirmed logged in");

    // 3. Click Sign Out — capture all navigations
    const navigations = [];
    page.on("framenavigated", (frame) => {
      if (frame === page.mainFrame()) navigations.push(frame.url());
    });

    const respPromise = page.waitForResponse(
      (r) => r.url().includes("/auth/logout"),
      { timeout: 8000 }
    );
    await Promise.all([
      page.waitForURL((u) => !u.toString().includes("/auth/logout"), { timeout: 10000 }),
      signOutBtn.click(),
    ]);
    const resp = await respPromise;
    console.log("LOGOUT RESPONSE STATUS:", resp.status());
    console.log("LOGOUT RESPONSE URL:", resp.url());

    // Wait for the page to settle
    await page.waitForLoadState("domcontentloaded");
    console.log("AFTER SIGN OUT URL:", page.url());
    console.log("NAV CHAIN:", JSON.stringify(navigations));

    // The user should land on the Pathways homepage, NOT a JSON page at /auth/logout
    expect(page.url()).not.toContain("/auth/logout");
    expect(page.url().replace(/\/$/, "")).toBe(PROD);

    // 4. Verify the user is actually signed out via /auth/status
    const statusResp = await page.request.get(PROD + "/auth/status");
    const status = await statusResp.json();
    console.log("AUTH STATUS AFTER LOGOUT:", JSON.stringify(status));

    // 5. The Sign In button (anchor) should be back, no Sign Out button
    await page.goto(PROD + "/");
    const signInLink = page.locator("a.nav-button", { hasText: "Sign In" }).first();
    const signOutStill = page.locator("button.nav-button", { hasText: "Sign Out" });
    console.log("SIGN IN VISIBLE:", await signInLink.isVisible());
    console.log("SIGN OUT STILL PRESENT:", await signOutStill.count());

    // Hard assertions
    expect(status.signed_in).toBe(false);
    await expect(signInLink).toBeVisible({ timeout: 5000 });
    await expect(signOutStill).toHaveCount(0);
  });
});
