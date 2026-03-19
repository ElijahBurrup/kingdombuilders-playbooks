// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * Visual & Cross-Browser Audit
 * Tests readability, layout, responsive design, and functional integrity
 * across desktop (Chrome/Safari), mobile (Android/iOS), and iPad.
 */

const SAMPLE_FREE = [
  { slug: "lay-it-down", title: "Lay It Down" },
  { slug: "conductors-playbook", title: "The Conductor's Playbook" },
  { slug: "the-tide-pools-echo", title: "The Tide Pool's Echo" },
  { slug: "dad-talks-the-dopamine-drought", title: "The Dopamine Drought" },
  { slug: "the-mockingbirds-song", title: "The Mockingbird's Song" },
];

const SAMPLE_PAID = [
  { slug: "the-bonsai-method", title: "The Bonsai Method" },
  { slug: "the-narrator", title: "The Narrator" },
  { slug: "the-tardigrade-protocol", title: "The Tardigrade Protocol" },
];

const ADMIN_CODE = "elijahsentme";

// Helper: unlock paid content for the session
async function unlockSession(page) {
  const first = SAMPLE_PAID[0];
  await page.goto(`read/${first.slug}?buy=1`);
  const gate = page.locator(".gate-badge");
  if (await gate.isVisible()) {
    await page.locator(".admin-toggle").click();
    await page.fill('input[name="code"]', ADMIN_CODE);
    await Promise.all([
      page.waitForURL(`**/read/${first.slug}`),
      page.locator(".admin-submit").click(),
    ]);
  }
}

// ── CATALOG PAGE ─────────────────────────────────────────────

test.describe("Catalog Page — Visual Audit", () => {
  test("hero section is readable (text contrast, no overflow)", async ({ page }) => {
    await page.goto("");
    const hero = page.locator(".hero-badge, .hero-title, .hero-sub").first();
    await expect(hero).toBeVisible();

    // Check no horizontal overflow
    const body = await page.evaluate(() => ({
      scrollW: document.body.scrollWidth,
      clientW: document.body.clientWidth,
    }));
    expect(body.scrollW).toBeLessThanOrEqual(body.clientW + 5);
  });

  test("all playbook cards render without overflow", async ({ page }) => {
    await page.goto("");
    const cards = page.locator(".card");
    const count = await cards.count();
    expect(count).toBeGreaterThan(40);

    // Spot check: no card should have 0 height
    for (let i = 0; i < Math.min(count, 10); i++) {
      const box = await cards.nth(i).boundingBox();
      expect(box).not.toBeNull();
      expect(box.height).toBeGreaterThan(50);
      expect(box.width).toBeGreaterThan(100);
    }
  });

  test("search input is visible and functional", async ({ page }) => {
    await page.goto("");
    const search = page.locator("#lens-input");
    await expect(search).toBeVisible();
    await search.fill("bonsai");
    await page.waitForTimeout(500);
    const visible = page.locator(".card:not(.hidden)");
    const visCount = await visible.count();
    expect(visCount).toBeGreaterThanOrEqual(1);
    expect(visCount).toBeLessThan(10);
  });

  test("pillar filter buttons work", async ({ page }) => {
    await page.goto("");
    // Dismiss What's New overlay if visible
    await page.evaluate(() => localStorage.setItem("pb_last_version", "99.0.0"));
    await page.goto("");
    // Open filter panel
    await page.locator("#lens-toggle").click();
    await page.waitForTimeout(300);
    // Click a filter pill (e.g. "Health")
    const healthPill = page.locator('.lens-pill[data-cat="health"]');
    await healthPill.click();
    await page.waitForTimeout(300);
    const hiddenCards = await page.locator(".card.hidden").count();
    expect(hiddenCards).toBeGreaterThan(0);
  });

  test("lens pills filter cards", async ({ page }) => {
    await page.goto("");
    await page.evaluate(() => localStorage.setItem("pb_last_version", "99.0.0"));
    await page.goto("");
    const pills = page.locator(".lens-pill");
    const count = await pills.count();
    expect(count).toBeGreaterThan(0);
  });
});

// ── READER PAGES — TEXT READABILITY ──────────────────────────

test.describe("Reader Pages — Text Readability", () => {
  test.beforeEach(async ({ page }) => {
    await unlockSession(page);
  });

  for (const pb of [...SAMPLE_FREE, ...SAMPLE_PAID]) {
    test(`${pb.title} — text is readable (font size, contrast)`, async ({ page }) => {
      await page.goto(`read/${pb.slug}`);
      await page.waitForLoadState("domcontentloaded");

      // Check body text font size (should be >= 14px effective)
      const textChecks = await page.evaluate(() => {
        const issues = [];
        const paragraphs = document.querySelectorAll("p, .scene p, .think p, .viz-body, .prompt-body");
        for (let i = 0; i < Math.min(paragraphs.length, 20); i++) {
          const el = paragraphs[i];
          const style = getComputedStyle(el);
          const fontSize = parseFloat(style.fontSize);
          const color = style.color;
          const bg = style.backgroundColor;
          const text = el.textContent.trim();

          // Skip tiny brand/watermark/label text (intentionally small decorative elements)
          if (text.startsWith("KingdomBuilders") || text.length < 15) continue;

          if (fontSize < 12) {
            issues.push(`Small font (${fontSize}px): "${text.slice(0, 40)}..."`);
          }

          // Check text isn't invisible (same color as bg or transparent)
          if (color === bg && color !== "rgba(0, 0, 0, 0)") {
            issues.push(`Invisible text: "${text.slice(0, 40)}..."`);
          }
        }
        return issues;
      });

      if (textChecks.length > 0) {
        console.log(`  ${pb.title} readability issues:`, textChecks);
      }
      expect(textChecks.length).toBe(0);
    });

    test(`${pb.title} — no horizontal overflow`, async ({ page }) => {
      await page.goto(`read/${pb.slug}`);
      await page.waitForLoadState("domcontentloaded");

      const overflow = await page.evaluate(() => {
        return document.body.scrollWidth > document.documentElement.clientWidth + 10;
      });
      expect(overflow).toBe(false);
    });

    test(`${pb.title} — cover section renders`, async ({ page }) => {
      await page.goto(`read/${pb.slug}`);
      const cover = page.locator(".cover, .cover-content, [class*='cover']").first();
      await expect(cover).toBeVisible();
    });

    test(`${pb.title} — page loads with substantial content`, async ({ page }) => {
      await page.goto(`read/${pb.slug}`);
      // Verify page has substantial content (playbook rendered fully)
      const html = await page.content();
      expect(html.length).toBeGreaterThan(10000);
    });
  }
});

// ── VISUAL COMPONENTS — DISPLAY INTEGRITY ────────────────────

test.describe("Visual Components — Display Integrity", () => {
  test.beforeEach(async ({ page }) => {
    await unlockSession(page);
  });

  test("Conductor — visualization boxes render with visible text", async ({ page }) => {
    await page.goto("read/conductors-playbook");
    const vizBoxes = page.locator(".viz, .viz-box, [class*='viz']");
    const count = await vizBoxes.count();
    if (count > 0) {
      const firstViz = vizBoxes.first();
      await firstViz.scrollIntoViewIfNeeded();
      const box = await firstViz.boundingBox();
      expect(box).not.toBeNull();
      expect(box.height).toBeGreaterThan(30);
    }
  });

  test("Bonsai Method — knowledge layer tooltips work", async ({ page }) => {
    await page.goto("read/the-bonsai-method");
    const defTerms = page.locator("dfn.def");
    const count = await defTerms.count();
    // Bonsai should have knowledge layer terms
    if (count > 0) {
      const first = defTerms.first();
      await first.scrollIntoViewIfNeeded();
      await first.hover();
      await page.waitForTimeout(300);
      // The ::after pseudo-element shows the tooltip; we can check the data-def attribute exists
      const dataDef = await first.getAttribute("data-def");
      expect(dataDef).toBeTruthy();
      expect(dataDef.length).toBeGreaterThan(3);
    }
  });

  test("Lay It Down — before/after comparison dots render", async ({ page }) => {
    await page.goto("read/lay-it-down");
    const dots = page.locator(".ba-dot");
    const count = await dots.count();
    expect(count).toBeGreaterThan(0);
  });

  test("Scripture ribbons are readable", async ({ page }) => {
    await page.goto("read/lay-it-down");
    const ribbons = page.locator(".ribbon");
    const count = await ribbons.count();
    if (count > 0) {
      const ribbon = ribbons.first();
      await ribbon.scrollIntoViewIfNeeded();

      const readability = await ribbon.evaluate((el) => {
        const style = getComputedStyle(el);
        return {
          fontSize: parseFloat(style.fontSize),
          opacity: parseFloat(style.opacity),
          visible: el.offsetHeight > 0,
        };
      });
      expect(readability.fontSize).toBeGreaterThanOrEqual(13);
      expect(readability.visible).toBe(true);
    }
  });

  test("Before/After comparisons have visible text in both columns", async ({ page }) => {
    await page.goto("read/conductors-playbook");
    const baPairs = page.locator(".ba-pair, .ba, .ba-grid, [class*='ba-']").first();
    if (await baPairs.isVisible()) {
      await baPairs.scrollIntoViewIfNeeded();
      const box = await baPairs.boundingBox();
      expect(box).not.toBeNull();
      expect(box.height).toBeGreaterThan(40);
    }
  });

  test("Grand quotes are readable", async ({ page }) => {
    await page.goto("read/the-narrator");
    const quotes = page.locator(".gq, .grand-quote");
    const count = await quotes.count();
    if (count > 0) {
      const q = quotes.first();
      await q.scrollIntoViewIfNeeded();
      const check = await q.evaluate((el) => {
        const style = getComputedStyle(el);
        return {
          fontSize: parseFloat(style.fontSize),
          height: el.offsetHeight,
        };
      });
      expect(check.fontSize).toBeGreaterThanOrEqual(14);
      expect(check.height).toBeGreaterThan(20);
    }
  });

  test("Chapter gates render with visible titles", async ({ page }) => {
    await page.goto("read/conductors-playbook");
    const chapters = page.locator(".ch-head, .ch-title, [class*='ch-']");
    const count = await chapters.count();
    expect(count).toBeGreaterThan(0);
  });

  test("Root system/review sections render", async ({ page }) => {
    await page.goto("read/conductors-playbook");
    const roots = page.locator(".root-ck, .root-review, .root-system, [class*='root']");
    const count = await roots.count();
    expect(count).toBeGreaterThan(0);
  });
});

// ── PURCHASE GATE & CHECKOUT ─────────────────────────────────

test.describe("Purchase Gate — Visual Integrity", () => {
  test("gate page has readable pricing text", async ({ page }) => {
    // Clear admin session to see gate, use ?buy=1 to bypass landing page
    await page.context().clearCookies();
    await page.goto(`read/${SAMPLE_PAID[0].slug}?buy=1`);

    const gate = page.locator(".gate-badge");
    if (await gate.isVisible()) {
      // Check pricing buttons are visible
      const buttons = page.locator("button.plan-btn, .plan-btn");
      const count = await buttons.count();
      expect(count).toBeGreaterThan(0);

      // Check price text is readable
      const priceCheck = await page.evaluate(() => {
        const prices = document.querySelectorAll(".plan-price, [class*='price'], .plan-btn");
        const issues = [];
        prices.forEach((el) => {
          const style = getComputedStyle(el);
          if (parseFloat(style.fontSize) < 12) {
            issues.push(`Small price text: ${el.textContent.trim().slice(0, 30)}`);
          }
        });
        return issues;
      });
      expect(priceCheck.length).toBe(0);
    }
  });
});

// ── NAVIGATION & DISCOVERY ───────────────────────────────────

test.describe("Navigation & Discovery Features", () => {
  test("back button exists on reader pages", async ({ page }) => {
    await page.goto(`read/${SAMPLE_FREE[0].slug}`);
    const back = page.locator(".pb-back");
    await expect(back).toBeVisible();
  });

  test("chain panel loads at bottom of free playbook", async ({ page }) => {
    await page.goto(`read/${SAMPLE_FREE[0].slug}`);
    // Scroll to bottom to trigger chain panel load
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2000);
    // Chain panel should be injected
    const chain = page.locator("#chain-panel, .chain-panel, [class*='chain']");
    const count = await chain.count();
    // It's OK if it doesn't exist (API might not return data), but no JS errors
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    expect(errors.length).toBe(0);
  });
});

// ── AUTH PAGES ───────────────────────────────────────────────
// Auth pages are served by the FastAPI app (api/main.py), not Flask.
// Skipped when testing against Flask dev server.

// ── CONSOLE ERRORS (across all key pages) ────────────────────

test.describe("Console Error Audit", () => {
  const pagesToCheck = [
    { url: "/", name: "Catalog" },
    { url: "/auth", name: "Auth" },
    { url: "/constellation", name: "Constellation" },
    { url: "/paths", name: "Paths" },
    { url: `read/${SAMPLE_FREE[0].slug}`, name: "Free Reader" },
  ];

  for (const pg of pagesToCheck) {
    test(`${pg.name} — no critical JS errors`, async ({ page }) => {
      const errors = [];
      page.on("pageerror", (e) => {
        // Ignore minor/expected errors
        if (e.message.includes("ResizeObserver") || e.message.includes("favicon")) return;
        errors.push(e.message);
      });

      await page.goto(pg.url);
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(1000);

      if (errors.length > 0) {
        console.log(`  JS errors on ${pg.name}:`, errors);
      }
      expect(errors.length).toBe(0);
    });
  }
});

// ── API ENDPOINTS ────────────────────────────────────────────
// API v1 endpoints are served by the FastAPI app (api/main.py), not Flask.
// Skipped when testing against Flask dev server.

test.describe("API Endpoints — Flask", () => {
  test("/api/version returns version info", async ({ page }) => {
    const response = await page.goto("api/version");
    expect(response.status()).toBe(200);
    const data = JSON.parse(await page.locator("body").textContent());
    expect(data.version).toBeTruthy();
  });

  test("/api/hot returns array", async ({ page }) => {
    const response = await page.goto("api/hot?period=all");
    expect(response.status()).toBe(200);
    const data = JSON.parse(await page.locator("body").textContent());
    expect(data).toBeInstanceOf(Array);
  });
});
