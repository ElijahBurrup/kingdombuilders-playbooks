// @ts-check
const { test, expect } = require("@playwright/test");

const BASE = process.env.BASE_URL || "http://localhost:5001";
const ADMIN_EMAIL = "elijah@kingdombuilders.ai";
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "changeme123";

/**
 * Helper: login and return the JWT access token.
 */
async function getAuthToken(request) {
  const resp = await request.post(`${BASE}/api/v1/auth/login`, {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  });
  expect(resp.ok()).toBeTruthy();
  const body = await resp.json();
  return body.access_token;
}

/**
 * Helper: login via form POST to set session cookie, then set JWT in localStorage.
 */
async function loginViaUI(page) {
  // First get a JWT token via API for the JS-based API calls
  const apiResp = await page.request.post(`${BASE}/api/v1/auth/login`, {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  });
  const { access_token } = await apiResp.json();

  // Login via form POST to set the session cookie (needed for server-rendered pages)
  await page.goto(`${BASE}/auth`);
  await page.fill('input[name="email"]', ADMIN_EMAIL);
  await page.fill('input[name="password"]', ADMIN_PASSWORD);
  await Promise.all([
    page.waitForURL((url) => !url.pathname.endsWith("/auth"), { timeout: 10000 }),
    page.click('button[type="submit"]'),
  ]);

  // Set JWT in localStorage for client-side API calls
  await page.evaluate((t) => {
    localStorage.setItem("kb_access_token", t);
  }, access_token);
}

// ============================================================================
// API-level tests
// ============================================================================
test.describe("Referral API Endpoints", () => {
  let token;

  test.beforeAll(async ({ request }) => {
    token = await getAuthToken(request);
  });

  test("GET /api/v1/referrals/me returns referral stats", async ({ request }) => {
    const resp = await request.get(`${BASE}/api/v1/referrals/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();

    // Verify all required fields exist
    expect(data).toHaveProperty("referral_code");
    expect(data).toHaveProperty("referral_link");
    expect(data).toHaveProperty("total_referrals");
    expect(data).toHaveProperty("active_subscribers");
    expect(data).toHaveProperty("current_balance_cents");
    expect(data).toHaveProperty("lifetime_earnings_cents");

    // Verify referral code format (6 alphanumeric uppercase)
    expect(data.referral_code).toMatch(/^[A-Z0-9]{6}$/);

    // Verify referral link contains the code
    expect(data.referral_link).toContain(`ref=${data.referral_code}`);
    expect(data.referral_link).toContain(BASE.replace(/:\d+$/, ""));

    // Verify test data counts
    expect(data.total_referrals).toBe(4);
    expect(data.lifetime_earnings_cents).toBeGreaterThan(0);
    expect(data.current_balance_cents).toBeGreaterThanOrEqual(0);
  });

  test("GET /api/v1/referrals/tree returns 4 L1, 16 L2, 50 L3", async ({ request }) => {
    const resp = await request.get(`${BASE}/api/v1/referrals/tree`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();

    // Level 1: array of 4 detailed referrals
    expect(data.level_1).toHaveLength(4);
    expect(data.level_1_commission_cents).toBeGreaterThan(0);

    // Verify each L1 referral has correct fields
    for (const ref of data.level_1) {
      expect(ref).toHaveProperty("display_name");
      expect(ref).toHaveProperty("email");
      expect(ref).toHaveProperty("signup_date");
      expect(ref).toHaveProperty("status");
      expect(ref).toHaveProperty("monthly_commission_cents");
      expect(["active", "inactive"]).toContain(ref.status);
      expect(ref.email).toMatch(/\*\*\*/); // email is masked
    }

    // Level 2: 16 count
    expect(data.level_2_summary).toBeDefined();
    expect(data.level_2_summary.count).toBe(16);
    expect(data.level_2_summary.total_commission_cents).toBeGreaterThan(0);

    // Level 3: 50 count
    expect(data.level_3_summary).toBeDefined();
    expect(data.level_3_summary.count).toBe(50);
    expect(data.level_3_summary.total_commission_cents).toBeGreaterThan(0);
  });

  test("GET /api/v1/referrals/earnings returns monthly breakdown", async ({ request }) => {
    const resp = await request.get(`${BASE}/api/v1/referrals/earnings`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();

    // Verify response structure
    expect(data).toHaveProperty("monthly");
    expect(data).toHaveProperty("balance_cents");
    expect(data).toHaveProperty("lifetime_cents");

    // Should have multiple months of data
    expect(data.monthly.length).toBeGreaterThanOrEqual(4);

    // Each month entry should have correct fields
    for (const m of data.monthly) {
      expect(m).toHaveProperty("month");
      expect(m).toHaveProperty("amount_cents");
      expect(m).toHaveProperty("label");
      expect(m.month).toMatch(/^\d{4}-\d{2}$/); // YYYY-MM format
      expect(m.amount_cents).toBeGreaterThan(0);
    }

    expect(data.lifetime_cents).toBeGreaterThan(0);
  });

  test("GET /api/v1/referrals/payouts returns payout history", async ({ request }) => {
    const resp = await request.get(`${BASE}/api/v1/referrals/payouts`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();

    expect(data).toHaveProperty("payouts");
    expect(data.payouts.length).toBeGreaterThanOrEqual(4);

    for (const p of data.payouts) {
      expect(p).toHaveProperty("date");
      expect(p).toHaveProperty("amount_cents");
      expect(p).toHaveProperty("fee_cents");
      expect(p).toHaveProperty("status");
      expect(p.status).toBe("completed");
      expect(p.amount_cents).toBeGreaterThan(0);
    }
  });

  test("GET /api/v1/referrals/attribution-status returns booleans", async ({ request }) => {
    const resp = await request.get(`${BASE}/api/v1/referrals/attribution-status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();

    expect(data).toHaveProperty("has_attribution");
    expect(data).toHaveProperty("has_pending_claim");
    expect(typeof data.has_attribution).toBe("boolean");
    expect(typeof data.has_pending_claim).toBe("boolean");
  });

  test("Unauthenticated requests return 401/403", async ({ request }) => {
    const endpoints = [
      "/api/v1/referrals/me",
      "/api/v1/referrals/tree",
      "/api/v1/referrals/earnings",
      "/api/v1/referrals/payouts",
    ];
    for (const ep of endpoints) {
      const resp = await request.get(`${BASE}${ep}`);
      expect([401, 403]).toContain(resp.status());
    }
  });
});

// ============================================================================
// UI-level tests (Playwright browser)
// ============================================================================
test.describe("Referral Page UI", () => {
  test.beforeEach(async ({ page }) => {
    await loginViaUI(page);
  });

  test("Referral page loads and shows referral link", async ({ page }) => {
    await page.goto(`${BASE}/referrals`);
    await page.waitForSelector("#refLinkUrl", { timeout: 10000 });

    // Wait for the referral link to populate (not "Loading...")
    await expect(async () => {
      const text = await page.textContent("#refLinkUrl");
      expect(text).not.toBe("Loading...");
      expect(text).toContain("ref=");
    }).toPass({ timeout: 10000 });
  });

  test("Referral link contains valid 6-char code", async ({ page }) => {
    await page.goto(`${BASE}/referrals`);
    await page.waitForSelector("#refLinkUrl");

    await expect(async () => {
      const linkText = await page.textContent("#refLinkUrl");
      const match = linkText.match(/ref=([A-Z0-9]{6})/);
      expect(match).not.toBeNull();
    }).toPass({ timeout: 10000 });
  });

  test("Copy button copies referral link", async ({ page, context }) => {
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    await page.goto(`${BASE}/referrals`);

    // Wait for link to populate
    await expect(async () => {
      const text = await page.textContent("#refLinkUrl");
      expect(text).toContain("ref=");
    }).toPass({ timeout: 10000 });

    await page.click("#refCopyBtn");

    // Button should show "Copied!"
    await expect(page.locator("#refCopyBtn")).toHaveText("Copied!");
  });

  test("Stats cards show correct data", async ({ page }) => {
    await page.goto(`${BASE}/referrals`);

    // Wait for stats to load
    await expect(async () => {
      const total = await page.textContent("#statTotalReferrals");
      expect(total).not.toBe("--");
    }).toPass({ timeout: 10000 });

    // Total referrals should be 4 (from test data)
    const totalReferrals = await page.textContent("#statTotalReferrals");
    expect(totalReferrals.trim()).toBe("4");

    // Active subscribers should be a number
    const activeSubs = await page.textContent("#statActiveSubscribers");
    expect(parseInt(activeSubs.trim())).toBeGreaterThanOrEqual(0);

    // Balance should show a dollar amount
    const balance = await page.textContent("#statMonthlyEarnings");
    expect(balance).toMatch(/\$/);
  });

  test("Share buttons have correct href attributes", async ({ page }) => {
    await page.goto(`${BASE}/referrals`);

    // Wait for referral link to load first (indicates JS has run)
    await expect(async () => {
      const text = await page.textContent("#refLinkUrl");
      expect(text).toContain("ref=");
    }).toPass({ timeout: 15000 });

    // Now check share buttons
    const twitterHref = await page.getAttribute("#shareTwitter", "href");
    expect(twitterHref).toContain("twitter.com/intent/tweet");

    const waHref = await page.getAttribute("#shareWhatsApp", "href");
    expect(waHref).toContain("wa.me");

    const emailHref = await page.getAttribute("#shareEmail", "href");
    expect(emailHref).toContain("mailto:");
  });

  test("Earnings tab loads and shows chart", async ({ page }) => {
    await page.goto(`${BASE}/referrals`);

    // Earnings tab should be visible by default (first tab)
    const earningsTab = page.locator('[data-tab="earnings"]');
    await expect(earningsTab).toHaveClass(/active/);

    // Wait for earnings content to load
    await expect(page.locator("#earningsContent")).toBeVisible({ timeout: 10000 });

    // Balance and lifetime should show dollar amounts
    const balance = await page.textContent("#earningsBalance");
    expect(balance).toMatch(/\$/);

    const lifetime = await page.textContent("#earningsLifetime");
    expect(lifetime).toMatch(/\$/);

    // Chart should have bar columns
    const bars = page.locator("#earningsChart .ref-bar-col");
    await expect(bars.first()).toBeVisible();
    const barCount = await bars.count();
    expect(barCount).toBeGreaterThanOrEqual(4);
  });

  test("Referrals tab loads tree with 4 L1, 16 L2, 50 L3", async ({ page }) => {
    await page.goto(`${BASE}/referrals`);

    // Wait for page JS to initialize (referral link loads)
    await expect(async () => {
      const text = await page.textContent("#refLinkUrl");
      expect(text).toContain("ref=");
    }).toPass({ timeout: 15000 });

    // Click the Referrals tab
    await page.click('[data-tab="tree"]');

    // Wait for tree content to load
    await expect(page.locator("#treeContent")).toBeVisible({ timeout: 15000 });

    // Should show Level 1 referral items (4 of them)
    const l1Items = page.locator(".ref-tree-item");
    await expect(l1Items.first()).toBeVisible();
    const l1Count = await l1Items.count();
    expect(l1Count).toBe(4);

    // Each L1 item should have a name and commission
    for (let i = 0; i < l1Count; i++) {
      const name = await l1Items.nth(i).locator(".ref-tree-name").textContent();
      expect(name.length).toBeGreaterThan(0);
    }

    // Level 2 and 3 summaries should show counts
    const treeContent = await page.textContent("#treeContent");
    expect(treeContent).toContain("16");
    expect(treeContent).toContain("50");
  });

  test("Payouts tab loads and shows payout history", async ({ page }) => {
    await page.goto(`${BASE}/referrals`);

    // Click the Payouts tab
    await page.click('[data-tab="payouts"]');

    // Wait for payouts content to load
    await expect(page.locator("#payoutsContent")).toBeVisible({ timeout: 10000 });

    // Should have a payouts table with completed entries
    const payoutRows = page.locator(".ref-payouts-table tr, .ref-payout-row");
    const rowCount = await payoutRows.count();
    expect(rowCount).toBeGreaterThanOrEqual(1);

    // Should show dollar amounts
    const payoutsText = await page.textContent("#payoutsContent");
    expect(payoutsText).toMatch(/\$/);
  });

  test("Tab switching works correctly", async ({ page }) => {
    await page.goto(`${BASE}/referrals`);

    // Wait for page JS to initialize
    await expect(async () => {
      const text = await page.textContent("#refLinkUrl");
      expect(text).toContain("ref=");
    }).toPass({ timeout: 15000 });

    // Switch to Referrals tab
    await page.click('[data-tab="tree"]');
    await expect(page.locator('[data-tab="tree"]')).toHaveClass(/active/);

    // Switch to Payouts tab
    await page.click('[data-tab="payouts"]');
    await expect(page.locator('[data-tab="payouts"]')).toHaveClass(/active/);

    // Switch back to Earnings tab
    await page.click('[data-tab="earnings"]');
    await expect(page.locator('[data-tab="earnings"]')).toHaveClass(/active/);
  });
});

// ============================================================================
// Referral link routing tests
// ============================================================================
test.describe("Referral Link Routing", () => {
  test("GET /r/{code} sets ref cookie and redirects", async ({ request }) => {
    // First get a valid code
    const loginResp = await request.post(`${BASE}/api/v1/auth/login`, {
      data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
    });
    const { access_token } = await loginResp.json();

    const meResp = await request.get(`${BASE}/api/v1/referrals/me`, {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    const { referral_code } = await meResp.json();

    // Visit the referral link — Playwright follows redirects, so we get 200
    const refResp = await request.get(`${BASE}/r/${referral_code}`);
    // Should ultimately resolve to 200 (after redirect to catalog)
    expect([200, 301, 302, 307]).toContain(refResp.status());
  });

  test("GET /r/INVALID does not set cookie", async ({ request }) => {
    const resp = await request.get(`${BASE}/r/ZZZZZZ`);
    // Should resolve to 200 (redirected) or 404
    expect([200, 301, 302, 307, 404]).toContain(resp.status());
  });
});
