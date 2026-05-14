// @ts-check
const { test, expect } = require("@playwright/test");

const PROD = "https://kingdombuilders.ai/playbooks";

// CSS breakpoint: @media(max-width:780px) — under that, hamburger replaces topnav buttons
const isNarrow = (page) =>
  page.viewportSize()?.width !== undefined && page.viewportSize().width <= 780;

test.describe("Sign In reachability — desktop topnav + mobile drawer", () => {
  test("Pathways homepage: Sign In is reachable", async ({ page }) => {
    await page.goto(PROD + "/");

    if (isNarrow(page)) {
      // Mobile: hamburger → drawer → Sign In
      const hamburger = page.locator(".nav-hamburger");
      await expect(hamburger).toBeVisible();
      await hamburger.click();

      const drawerSignIn = page.locator(".nav-drawer a.drawer-cta", {
        hasText: "Sign In",
      });
      await expect(drawerSignIn).toBeVisible();

      const href = await drawerSignIn.getAttribute("href");
      expect(href).toBe("/playbooks/auth");

      await Promise.all([page.waitForURL(/\/playbooks\/auth/), drawerSignIn.click()]);
      expect(page.url()).toContain("/playbooks/auth");
    } else {
      // Desktop: topnav Sign In button
      const btn = page.locator(".nav-button", { hasText: "Sign In" });
      await expect(btn).toBeVisible();

      const href = await btn.getAttribute("href");
      expect(href).toBe("/playbooks/auth");

      await Promise.all([page.waitForURL(/\/playbooks\/auth/), btn.click()]);
      expect(page.url()).toContain("/playbooks/auth");
    }
  });

  test("Archive page: Sign In is reachable", async ({ page }) => {
    await page.goto(PROD + "/archive");

    if (isNarrow(page)) {
      const hamburger = page.locator(".nav-hamburger");
      await expect(hamburger).toBeVisible();
      await hamburger.click();
      const link = page.locator(".nav-drawer a", { hasText: "Sign In" });
      await expect(link).toBeVisible();
      expect(await link.getAttribute("href")).toBe("/playbooks/auth");
    } else {
      const btn = page.locator(".nav-button", { hasText: "Sign In" });
      await expect(btn).toBeVisible();
      expect(await btn.getAttribute("href")).toBe("/playbooks/auth");
    }
  });

  test("Direct /auth route serves the sign-in form", async ({ page }) => {
    const response = await page.goto(PROD + "/auth");
    expect(response?.status()).toBe(200);
    // The page has both a sign-in and a register panel — scope to the visible one
    await expect(page.locator('input[type="email"]').first()).toBeVisible();
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
  });
});
