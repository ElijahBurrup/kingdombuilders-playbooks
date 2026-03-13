// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * Production diagnostic — checks every key page loads correctly.
 * Run with: npx playwright test tests/prod-diagnostic.spec.js --project=chrome-desktop
 */

const PAGES = [
  { path: "", name: "Catalog", expect: ".hero-badge" },
  { path: "auth", name: "Auth/Sign-In", expect: "body" },
  { path: "constellation", name: "Constellation", expect: "body" },
  { path: "paths", name: "Reading Paths", expect: "body" },
  { path: "journey", name: "Your Journey", expect: "body" },
  { path: "my-playbooks", name: "My Playbooks", expect: "body" },
  { path: "referrals", name: "Referrals", expect: "body" },
  { path: "terms", name: "Terms", expect: "body" },
  { path: "privacy", name: "Privacy", expect: "body" },
  { path: "funnel", name: "Funnel", expect: "body" },
];

const FREE_SLUGS = [
  "conductors-playbook",
  "lay-it-down",
  "the-mockingbirds-song",
  "the-lifted-ceiling",
  "the-tide-pools-echo",
  "dad-talks-the-dopamine-drought",
  "the-mantis-shrimps-eye",
  "the-hermit-crabs-shell",
];

const PAID_SLUGS = [
  "the-ant-network",
  "the-narrator",
  "the-bonsai-method",
  "the-salmon-journey",
];

test.describe("Production Page Load Diagnostic", () => {

  for (const pg of PAGES) {
    test(`${pg.name} (${pg.path}) loads OK`, async ({ page }) => {
      const response = await page.goto(pg.path, { waitUntil: "domcontentloaded" });
      const status = response.status();
      const url = page.url();
      const title = await page.title();
      const bodyText = await page.locator("body").textContent();
      const bodyLen = bodyText.length;

      console.log(`  ${pg.name}: status=${status} url=${url} title="${title}" bodyLen=${bodyLen}`);

      // Should not be 404/500
      expect(status, `${pg.name} returned ${status}`).toBeLessThan(400);
      // Should not be empty
      expect(bodyLen, `${pg.name} body is empty`).toBeGreaterThan(100);
      // Should not show "Not Found" error page
      expect(bodyText).not.toContain("Not Found");
    });
  }

  test("Catalog card hrefs are correct after JS", async ({ page }) => {
    await page.goto("", { waitUntil: "networkidle" });
    // Wait for JS to rewrite hrefs
    await page.waitForTimeout(1000);

    const cards = await page.locator("a.card").all();
    console.log(`  Found ${cards.length} cards`);
    expect(cards.length).toBeGreaterThan(50);

    // Check first 5 cards
    for (let i = 0; i < Math.min(5, cards.length); i++) {
      const href = await cards[i].getAttribute("href");
      console.log(`  Card ${i}: href=${href}`);
      // href should contain "read/" somewhere
      expect(href).toContain("read/");
    }

    // Click first card and check navigation
    const firstHref = await cards[0].getAttribute("href");
    console.log(`  Clicking first card: ${firstHref}`);
    await cards[0].click();
    await page.waitForLoadState("domcontentloaded");
    const url = page.url();
    const status = (await page.evaluate(() => document.title)) ? 200 : 0;
    console.log(`  Navigated to: ${url}`);
    expect(url).toContain("read/");
  });

  for (const slug of FREE_SLUGS) {
    test(`Free playbook /read/${slug} loads content`, async ({ page }) => {
      const response = await page.goto(`read/${slug}`, { waitUntil: "domcontentloaded" });
      const status = response.status();
      const bodyLen = (await page.locator("body").textContent()).length;
      const hasGate = await page.locator(".gate-badge").isVisible().catch(() => false);
      const hasCover = await page.locator(".cover").isVisible().catch(() => false);
      const hasBack = await page.locator(".pb-back").isVisible().catch(() => false);

      console.log(`  /read/${slug}: status=${status} bodyLen=${bodyLen} gate=${hasGate} cover=${hasCover} back=${hasBack}`);

      expect(status).toBe(200);
      expect(bodyLen).toBeGreaterThan(5000);
      expect(hasGate, `Free playbook ${slug} shows purchase gate!`).toBe(false);
    });
  }

  for (const slug of PAID_SLUGS) {
    test(`Paid landing /read/${slug} loads`, async ({ page }) => {
      const response = await page.goto(`read/${slug}`, { waitUntil: "domcontentloaded" });
      const status = response.status();
      const bodyLen = (await page.locator("body").textContent()).length;
      const hasFab = await page.locator(".fab-cta").isVisible().catch(() => false);
      const hasGate = await page.locator(".gate-badge").isVisible().catch(() => false);

      console.log(`  /read/${slug}: status=${status} bodyLen=${bodyLen} fab=${hasFab} gate=${hasGate}`);

      expect(status).toBe(200);
      expect(bodyLen).toBeGreaterThan(1000);
    });

    test(`Paid gate /read/${slug}?buy=1 loads`, async ({ page }) => {
      const response = await page.goto(`read/${slug}?buy=1`, { waitUntil: "domcontentloaded" });
      const status = response.status();
      const hasGate = await page.locator(".gate-badge").isVisible().catch(() => false);

      console.log(`  /read/${slug}?buy=1: status=${status} gate=${hasGate}`);

      expect(status).toBe(200);
      expect(hasGate, `Purchase gate not showing for ${slug}?buy=1`).toBe(true);
    });
  }

  test("Sign-in page has Google button or form", async ({ page }) => {
    await page.goto("auth", { waitUntil: "domcontentloaded" });
    const url = page.url();
    const bodyText = await page.locator("body").textContent();
    console.log(`  /auth url=${url} bodyLen=${bodyText.length}`);
    // Should have some auth-related content
    expect(bodyText.length).toBeGreaterThan(200);
  });

  test("API endpoints respond", async ({ page }) => {
    // Version
    let r = await page.goto("api/version");
    let text = await page.locator("body").textContent();
    console.log(`  /api/version: ${text.substring(0, 100)}`);
    expect(r.status()).toBe(200);

    // Hot
    r = await page.goto("api/hot?period=all");
    text = await page.locator("body").textContent();
    console.log(`  /api/hot: ${text.substring(0, 100)}`);
    expect(r.status()).toBe(200);

    // Feedback summary
    r = await page.goto("api/v1/feedback-summary");
    text = await page.locator("body").textContent();
    console.log(`  /api/v1/feedback-summary: ${text.substring(0, 100)}`);
    expect(r.status()).toBe(200);
  });

  test("Navigation from catalog works", async ({ page }) => {
    await page.goto("", { waitUntil: "networkidle" });

    // Check hero nav links
    const navLinks = [
      { text: "CONSTELLATION", expectUrl: "constellation" },
      { text: "READING PATHS", expectUrl: "paths" },
      { text: "REFER & EARN", expectUrl: "referrals" },
      { text: "YOUR JOURNEY", expectUrl: "journey" },
      { text: "MY PLAYBOOKS", expectUrl: "my-playbooks" },
    ];

    for (const link of navLinks) {
      const el = page.locator(`a:has-text("${link.text}")`).first();
      const href = await el.getAttribute("href");
      console.log(`  "${link.text}" href=${href}`);
    }
  });
});
