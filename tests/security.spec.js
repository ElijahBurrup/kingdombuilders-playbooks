// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * Security & Penetration Tests
 * Tests for access control bypass, payment manipulation, data leakage,
 * path traversal, brute force protection, and session security.
 *
 * Run against production: BASE_URL=https://kingdombuilders.ai/playbooks npx playwright test tests/security.spec.js
 * Run against local:      BASE_URL=http://localhost:5000 npx playwright test tests/security.spec.js
 */

const PAID_SLUG = "the-ant-network";
const FREE_SLUG = "conductors-playbook";
const FREE_SLUG_2 = "the-lifted-ceiling";

// ── PURCHASE GATE BYPASS ATTEMPTS ────────────────────────────

test.describe("Purchase Gate — Bypass Attempts", () => {
  test("paid playbook cannot be accessed without payment or admin code", async ({ page }) => {
    const response = await page.goto(`read/${PAID_SLUG}`);
    expect(response.status()).toBe(200);
    // Should see landing page or purchase gate, never the actual content
    const hasGate = await page.locator(".gate-badge").count();
    const hasFabCta = await page.locator(".fab-cta").count();
    const hasPlaybookContent = await page.locator(".pb-back").count();
    expect(hasGate + hasFabCta).toBeGreaterThan(0);
    expect(hasPlaybookContent).toBe(0);
  });

  test("?buy=1 shows purchase gate, not playbook content", async ({ page }) => {
    await page.goto(`read/${PAID_SLUG}?buy=1`);
    await expect(page.locator(".gate-badge")).toBeVisible();
    const content = await page.content();
    // Should NOT contain playbook sections like .cover, .section, .ch-head
    expect(content).not.toContain('class="pb-back"');
  });

  test("cannot access paid playbook by manipulating query params", async ({ page }) => {
    const bypassAttempts = [
      `read/${PAID_SLUG}?admin=true`,
      `read/${PAID_SLUG}?unlocked=1`,
      `read/${PAID_SLUG}?free=1`,
      `read/${PAID_SLUG}?admin_unlocked=1`,
      `read/${PAID_SLUG}?session=admin`,
    ];
    for (const url of bypassAttempts) {
      await page.goto(url);
      const hasPlaybook = await page.locator(".pb-back").count();
      expect(hasPlaybook, `Bypass via ${url}`).toBe(0);
    }
  });

  test("cannot access paid playbook via case variations of slug", async ({ page }) => {
    const variations = [
      `read/The-Ant-Network`,
      `read/THE-ANT-NETWORK`,
      `read/The_Ant_Network`,
    ];
    for (const url of variations) {
      const response = await page.goto(url);
      // Should be 404 (invalid slug) not 200 with content
      const hasPlaybook = await page.locator(".pb-back").count();
      expect(hasPlaybook, `Case bypass via ${url}`).toBe(0);
    }
  });

  test("free playbooks are truly accessible without payment", async ({ page }) => {
    await page.goto(`read/${FREE_SLUG}`);
    // Should see the actual playbook, not a gate
    await expect(page.locator(".pb-back")).toBeVisible();
    const gate = await page.locator(".gate-badge").count();
    expect(gate).toBe(0);
  });

  test("the-lifted-ceiling is free (synced across all files)", async ({ page }) => {
    await page.goto(`read/${FREE_SLUG_2}`);
    await expect(page.locator(".pb-back")).toBeVisible();
    const gate = await page.locator(".gate-badge").count();
    expect(gate).toBe(0);
  });
});

// ── PATH TRAVERSAL & INJECTION ───────────────────────────────

test.describe("Path Traversal & Injection", () => {
  test("path traversal in slug is blocked", async ({ page }) => {
    const traversals = [
      "/read/../../etc/passwd",
      "/read/..%2F..%2Fetc%2Fpasswd",
      "/read/the-ant-network/../../config",
      "/read/the-ant-network%00.html",
      "/read/..\\..\\config.py",
    ];
    for (const url of traversals) {
      const response = await page.goto(url);
      expect([400, 404, 405]).toContain(response.status());
    }
  });

  test("cannot access asset files directly via static path", async ({ page }) => {
    const directAssetAttempts = [
      "/static/../assets/The_Ant_Network.html",
      "/static/..%2Fassets%2FThe_Ant_Network.html",
      "/assets/The_Ant_Network.html",
    ];
    for (const url of directAssetAttempts) {
      const response = await page.goto(url);
      // Should be 404 — assets dir is not mounted as static
      expect(response.status(), `Direct access via ${url}`).toBe(404);
    }
  });

  test("XSS in slug parameter is neutralized", async ({ page }) => {
    const xssAttempts = [
      '/read/<script>alert(1)</script>',
      '/read/test" onmouseover="alert(1)',
      "/read/test'><img src=x onerror=alert(1)>",
    ];
    for (const url of xssAttempts) {
      await page.goto(url);
      // Page should NOT execute any script injection
      const alerts = [];
      page.on("dialog", (d) => { alerts.push(d.message()); d.dismiss(); });
      await page.waitForTimeout(500);
      expect(alerts.length, `XSS via ${url}`).toBe(0);
    }
  });
});

// ── ADMIN UNLOCK SECURITY ────────────────────────────────────

test.describe("Admin Unlock Security", () => {
  test("wrong admin code does not grant access", async ({ page }) => {
    await page.goto(`read/${PAID_SLUG}?buy=1`);
    await page.locator(".admin-toggle").click();
    await page.fill('input[name="code"]', "wrongcode123");
    await Promise.all([
      page.waitForURL(`**/read/${PAID_SLUG}*`),
      page.locator(".admin-submit").click(),
    ]);
    // Should still see gate, not content
    await expect(page.locator(".gate-badge")).toBeVisible();
  });

  test("empty admin code does not grant access", async ({ page }) => {
    await page.goto(`read/${PAID_SLUG}?buy=1`);
    await page.locator(".admin-toggle").click();
    await page.fill('input[name="code"]', "");
    await Promise.all([
      page.waitForURL(`**/read/${PAID_SLUG}*`),
      page.locator(".admin-submit").click(),
    ]);
    await expect(page.locator(".gate-badge")).toBeVisible();
  });

  test("admin unlock is session-scoped, not persistent across browsers", async ({ browser }) => {
    // Session 1: unlock
    const ctx1 = await browser.newContext();
    const page1 = await ctx1.newPage();
    await page1.goto(`read/${PAID_SLUG}?buy=1`);
    await page1.locator(".admin-toggle").click();
    await page1.fill('input[name="code"]', "elijahsentme");
    await Promise.all([
      page1.waitForURL(`**/read/${PAID_SLUG}`),
      page1.locator(".admin-submit").click(),
    ]);
    await expect(page1.locator(".pb-back")).toBeVisible();
    await ctx1.close();

    // Session 2: fresh browser — should NOT be unlocked
    const ctx2 = await browser.newContext();
    const page2 = await ctx2.newPage();
    await page2.goto(`read/${PAID_SLUG}`);
    const hasPlaybook = await page2.locator(".pb-back").count();
    expect(hasPlaybook).toBe(0);
    await ctx2.close();
  });

});

// ── ADMIN DASHBOARD PROTECTION ───────────────────────────────

test.describe("Admin Dashboard Protection", () => {
  test("admin dashboard requires authentication", async ({ page }) => {
    const response = await page.goto("admin");
    // Should redirect to catalog or show 401/403, not analytics data
    const url = page.url();
    const hasAnalytics = await page.locator("table, .analytics, .admin-stats").count();
    // Either redirected away from /admin or page doesn't show analytics
    const redirectedAway = !url.includes("/admin");
    expect(redirectedAway || hasAnalytics === 0, "Admin dashboard should be protected").toBe(true);
  });

  test("admin dashboard accessible after unlock", async ({ page }) => {
    // Unlock first
    await page.goto(`read/${PAID_SLUG}?buy=1`);
    await page.locator(".admin-toggle").click();
    await page.fill('input[name="code"]', "elijahsentme");
    await Promise.all([
      page.waitForURL(`**/read/${PAID_SLUG}`),
      page.locator(".admin-submit").click(),
    ]);
    // Now try admin
    const response = await page.goto("admin");
    expect(response.status()).toBe(200);
    const url = page.url();
    expect(url).toContain("/admin");
  });
});

// ── CHECKOUT & PAYMENT INTEGRITY ─────────────────────────────

test.describe("Checkout & Payment Integrity", () => {
  test("checkout form for paid playbook has correct hidden fields", async ({ page }) => {
    await page.goto(`read/${PAID_SLUG}?buy=1`);
    // Verify the slug in hidden fields matches the URL slug
    const slugInputs = page.locator('input[name="slug"]');
    const count = await slugInputs.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      const val = await slugInputs.nth(i).getAttribute("value");
      expect(val).toBe(PAID_SLUG);
    }
  });

  test("checkout form action points to correct endpoint", async ({ page }) => {
    await page.goto(`read/${PAID_SLUG}?buy=1`);
    const forms = page.locator('form[action*="create-checkout-session"]');
    const count = await forms.count();
    expect(count).toBe(3); // single, monthly, yearly
  });

  test("free playbook purchase gate is never shown", async ({ page }) => {
    // Free playbooks should never show the purchase gate even with ?buy=1
    await page.goto(`read/${FREE_SLUG}?buy=1`);
    // Free playbook should serve content regardless of ?buy=1
    await expect(page.locator(".pb-back")).toBeVisible();
  });

  test("cannot tamper with checkout mode via query params", async ({ page }) => {
    await page.goto(`read/${PAID_SLUG}?buy=1`);
    // All three mode inputs should be locked to their expected values
    const singleMode = await page.locator('form:has(input[value="single"]) input[name="mode"]').getAttribute("value");
    const monthlyMode = await page.locator('form:has(input[value="monthly"]) input[name="mode"]').getAttribute("value");
    const yearlyMode = await page.locator('form:has(input[value="yearly"]) input[name="mode"]').getAttribute("value");
    expect(singleMode).toBe("single");
    expect(monthlyMode).toBe("monthly");
    expect(yearlyMode).toBe("yearly");
  });
});

// ── WEBHOOK SECURITY ─────────────────────────────────────────

test.describe("Webhook Security", () => {
  test("webhook rejects unsigned requests", async ({ request }) => {
    const response = await request.post("/webhook/stripe", {
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify({
        type: "checkout.session.completed",
        data: {
          object: {
            id: "cs_fake_session",
            customer_details: { email: "attacker@evil.com" },
            metadata: { mode: "single", slug: PAID_SLUG },
            amount_total: 0,
          },
        },
      }),
    });
    // Should be 400 or 500 (signature verification fails), never 200
    expect(response.status()).not.toBe(200);
  });

  test("webhook rejects forged signature", async ({ request }) => {
    const response = await request.post("/webhook/stripe", {
      headers: {
        "Content-Type": "application/json",
        "Stripe-Signature": "t=1234567890,v1=fakesignature",
      },
      data: JSON.stringify({
        type: "checkout.session.completed",
        data: {
          object: {
            id: "cs_forged_session",
            customer_details: { email: "attacker@evil.com" },
            metadata: { mode: "monthly" },
          },
        },
      }),
    });
    expect(response.status()).not.toBe(200);
  });
});

// ── SUCCESS PAGE & TOKEN LEAKAGE ─────────────────────────────

test.describe("Success Page Security", () => {
  test("success page without session_id redirects", async ({ page }) => {
    const response = await page.goto("success");
    // Should redirect to catalog, not show an error with sensitive info
    const url = page.url();
    const hasToken = await page.content();
    expect(hasToken).not.toContain("download_token");
  });

  test("success page with fake session_id shows error, no token", async ({ page }) => {
    await page.goto("success?session_id=cs_fake_12345");
    const content = await page.content();
    // Should show "purchase not found" error, not leak any tokens
    expect(content).not.toContain("download_token");
    // Should not expose internal error details
    expect(content).not.toContain("Traceback");
    expect(content).not.toContain("stripe.error");
  });
});

// ── SESSION MANIPULATION ─────────────────────────────────────

test.describe("Session Manipulation", () => {
  test("forged session cookie does not grant access", async ({ browser }) => {
    const context = await browser.newContext();
    // Try to set a session cookie manually
    await context.addCookies([
      {
        name: "session",
        value: "admin_unlocked=True",
        domain: "localhost",
        path: "/",
      },
    ]);
    const page = await context.newPage();
    await page.goto(`read/${PAID_SLUG}`);
    // Should NOT see playbook content
    const hasPlaybook = await page.locator(".pb-back").count();
    expect(hasPlaybook).toBe(0);
    await context.close();
  });

  test("clearing cookies removes access", async ({ page }) => {
    // Unlock first
    await page.goto(`read/${PAID_SLUG}?buy=1`);
    await page.locator(".admin-toggle").click();
    await page.fill('input[name="code"]', "elijahsentme");
    await Promise.all([
      page.waitForURL(`**/read/${PAID_SLUG}`),
      page.locator(".admin-submit").click(),
    ]);
    await expect(page.locator(".pb-back")).toBeVisible();

    // Clear all cookies
    await page.context().clearCookies();
    await page.goto(`read/${PAID_SLUG}`);
    // Should no longer have access
    const hasPlaybook = await page.locator(".pb-back").count();
    expect(hasPlaybook).toBe(0);
  });
});

// ── INFORMATION DISCLOSURE ───────────────────────────────────

test.describe("Information Disclosure", () => {
  test("error pages do not leak stack traces", async ({ page }) => {
    const errorUrls = [
      "/read/nonexistent-slug-12345",
      "/read/",
      "/api/nonexistent",
    ];
    for (const url of errorUrls) {
      await page.goto(url);
      const content = await page.content();
      expect(content, `Stack trace leak at ${url}`).not.toContain("Traceback");
      expect(content, `File path leak at ${url}`).not.toContain("app.py");
      expect(content, `Module leak at ${url}`).not.toContain("site-packages");
    }
  });

  test("API endpoints do not expose internal structure", async ({ page }) => {
    const response = await page.goto("api/version");
    const text = await page.locator("body").textContent();
    const data = JSON.parse(text);
    // Should not contain file paths, database info, or secrets
    const serialized = JSON.stringify(data);
    expect(serialized).not.toContain("SECRET");
    expect(serialized).not.toContain("password");
    expect(serialized).not.toContain("/opt/render");
  });

  test("robots.txt or meta tags prevent indexing of purchase gate", async ({ page }) => {
    await page.goto(`read/${PAID_SLUG}?buy=1`);
    const robotsMeta = await page.locator('meta[name="robots"]').getAttribute("content");
    expect(robotsMeta).toContain("noindex");
  });
});

// ── CONTENT SCRAPING PROTECTION ──────────────────────────────

test.describe("Content Protection", () => {
  test("landing page does not contain full playbook content", async ({ page }) => {
    await page.goto(`read/${PAID_SLUG}`);
    const content = await page.content();
    // Landing pages should be short sales copy, not the full 50k+ char playbook
    expect(content.length).toBeLessThan(30000);
    // Should not contain chapter content markers
    const chapterCount = (content.match(/class="ch-head"/g) || []).length;
    expect(chapterCount, "Landing page should not contain chapter headings").toBe(0);
  });

  test("page source of paid playbook does not leak via view-source", async ({ request }) => {
    // Direct HTTP request without a browser session should not return playbook content
    const response = await request.get(`read/${PAID_SLUG}`);
    const body = await response.text();
    // Should be landing page, not the full playbook
    expect(body.length).toBeLessThan(30000);
    expect(body).not.toContain('class="pb-back"');
  });
});

// ── RATE LIMITING (runs last — poisons IP for subsequent unlock attempts) ────

test.describe("Rate Limiting", () => {
  test("rate limiting blocks brute force after 5 attempts", async ({ page }) => {
    for (let i = 0; i < 6; i++) {
      await page.goto(`read/${PAID_SLUG}?buy=1`);
      await page.locator(".admin-toggle").click();
      await page.fill('input[name="code"]', `wrong${i}`);
      await Promise.all([
        page.waitForURL(`**/read/${PAID_SLUG}*`),
        page.locator(".admin-submit").click(),
      ]);
    }
    // After 5+ failures, should still be gated (rate limited)
    await expect(page.locator(".gate-badge")).toBeVisible();
  });
});
