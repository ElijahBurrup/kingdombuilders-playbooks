// @ts-check
const { test, expect } = require("@playwright/test");

const PROD = "https://kingdombuilders.ai/playbooks";

test.describe("Sign In button diagnostic", () => {
  test("Pathways homepage: Sign In button exists, has correct href, is clickable", async ({ page }) => {
    const consoleErrors = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) => consoleErrors.push("pageerror: " + err.message));

    const response = await page.goto(PROD + "/");
    console.log("HOMEPAGE STATUS:", response?.status());

    const btn = page.locator(".nav-button", { hasText: "Sign In" });
    await expect(btn).toBeVisible();

    const href = await btn.getAttribute("href");
    console.log("SIGN IN HREF:", href);

    // Check what element is at the click position
    const box = await btn.boundingBox();
    if (box) {
      const cx = box.x + box.width / 2;
      const cy = box.y + box.height / 2;
      const elAtPoint = await page.evaluate(
        ({ x, y }) => {
          const el = document.elementFromPoint(x, y);
          if (!el) return "no element";
          return {
            tag: el.tagName,
            class: el.className,
            id: el.id,
            text: el.textContent?.slice(0, 50),
          };
        },
        { x: cx, y: cy }
      );
      console.log("ELEMENT AT BUTTON CENTER:", JSON.stringify(elAtPoint));
    }

    // Try clicking and see where we land
    const navPromise = page
      .waitForNavigation({ timeout: 5000 })
      .catch((e) => `no nav: ${e.message}`);
    await btn.click({ force: false });
    const navResult = await navPromise;

    console.log("NAV RESULT:", typeof navResult === "string" ? navResult : navResult?.url());
    console.log("CURRENT URL:", page.url());
    console.log("CONSOLE ERRORS:", consoleErrors);
  });

  test("Archive page: Sign In button check", async ({ page }) => {
    const response = await page.goto(PROD + "/archive");
    console.log("ARCHIVE STATUS:", response?.status());

    const btn = page.locator(".nav-button", { hasText: "Sign In" });
    const visible = await btn.isVisible();
    console.log("ARCHIVE SIGN IN VISIBLE:", visible);

    if (visible) {
      const href = await btn.getAttribute("href");
      console.log("ARCHIVE SIGN IN HREF:", href);
    }
  });

  test("Direct /auth route should serve auth page", async ({ page }) => {
    const response = await page.goto(PROD + "/auth");
    console.log("AUTH ROUTE STATUS:", response?.status());
    console.log("AUTH FINAL URL:", page.url());

    // Look for sign-in form elements
    const hasEmail = await page.locator('input[type="email"]').count();
    const hasPassword = await page.locator('input[type="password"]').count();
    const title = await page.title();
    console.log("AUTH TITLE:", title);
    console.log("AUTH HAS EMAIL INPUT:", hasEmail > 0);
    console.log("AUTH HAS PASSWORD INPUT:", hasPassword > 0);
  });
});
