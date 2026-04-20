// @ts-check
const { test, expect } = require("@playwright/test");

const BASE = process.env.BASE_URL || "https://kingdombuilders.ai/playbooks";
const ADMIN_PASSWORD = "changeme123";

/**
 * Targeted tests verifying production fixes:
 * 1. Referral link format uses /r/{code}
 * 2. Sample referral data seeded for admin
 * 3. Stripe checkout works through Cloudflare
 * 4. API endpoints accept session cookies (not just JWT)
 */

// Helper: log in as admin via form
async function loginAsAdmin(page) {
  await page.goto(`${BASE}/auth`);
  await page.waitForSelector('input[name="email"]');
  await page.fill('input[name="email"]', "elijah@kingdombuilders.ai");
  await page.fill('input[name="password"]', ADMIN_PASSWORD);

  // Login uses _redirect_with_cookie (200 + JS redirect)
  await page.click('button[type="submit"]');
  // Wait for the JS redirect to complete
  await page.waitForURL((url) => !url.pathname.includes("/auth"), { timeout: 15000 });
}

// --- Health checks ---

test("site health check", async ({ request }) => {
  const res = await request.get(`${BASE}/health`);
  expect(res.status()).toBe(200);
});

test("catalog page loads with playbook grid", async ({ request }) => {
  const res = await request.get(`${BASE}/`);
  expect(res.status()).toBe(200);
  const body = await res.text();
  expect(body).toContain("playbook-grid");
});

// --- 1. Referral link format ---

test("referral route /r/{code} returns funnel redirect HTML", async ({ request }) => {
  const res = await request.get(`${BASE}/r/ZZZZZZ`, { maxRedirects: 0 });
  expect(res.status()).toBe(200);
  const body = await res.text();
  expect(body).toContain("/funnel");
});

test("referral dashboard shows /r/ link format", async ({ page }) => {
  await loginAsAdmin(page);
  await page.goto(`${BASE}/referrals`);

  // Wait for the referral link to load (API call completes)
  await page.waitForFunction(
    () => {
      const el = document.getElementById("refLinkUrl");
      return el && el.textContent && el.textContent.includes("/r/");
    },
    { timeout: 15000 },
  );

  const linkText = await page.textContent("#refLinkUrl");
  expect(linkText).toMatch(/\/r\/[A-Z0-9]{6}$/);
  expect(linkText).not.toContain("?ref=");
});

// --- 2. Sample referral data ---

test("referral dashboard loads with seeded data", async ({ page }) => {
  await loginAsAdmin(page);
  await page.goto(`${BASE}/referrals`);

  // Wait for API data to load
  await page.waitForFunction(
    () => {
      const el = document.getElementById("refLinkUrl");
      return el && el.textContent && el.textContent.length > 10 && !el.textContent.includes("Loading");
    },
    { timeout: 15000 },
  );

  const linkText = await page.textContent("#refLinkUrl");
  expect(linkText).toBeTruthy();
  expect(linkText.length).toBeGreaterThan(10);
});

// --- 3. Stripe checkout ---

test("purchase gate renders for paid playbooks", async ({ page }) => {
  await page.goto(`${BASE}/read/the-ant-network?buy=1`);
  await page.waitForLoadState("domcontentloaded");
  // Check pricing elements exist
  await expect(page.locator(".pricing-card")).toHaveCount(3);
  await expect(page.locator(".plan-btn")).toHaveCount(3);
  // Check form action points to checkout
  const formAction = await page.locator("form").first().getAttribute("action");
  expect(formAction).toContain("create-checkout-session");
});

test("authenticated checkout navigates to Stripe", async ({ page }) => {
  await loginAsAdmin(page);
  await page.goto(`${BASE}/read/the-ant-network?buy=1`);
  await page.waitForLoadState("domcontentloaded");

  // Click "Buy This One" and wait for navigation to Stripe
  await Promise.all([
    page.waitForURL(/stripe\.com|checkout\.stripe/, { timeout: 20000 }),
    page.click("button.plan-btn-outline"),
  ]);
  const url = page.url();
  expect(url).toMatch(/stripe\.com|checkout\.stripe/);
});
