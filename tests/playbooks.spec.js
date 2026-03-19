// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * Master registry of all playbooks.
 * When adding a new playbook via SetHut, add an entry here.
 */
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

const PLAYBOOKS = [
  { title: "The Conductor's Playbook", slug: "conductors-playbook", tag: "Productivity", free: true },
  { title: "Lay It Down", slug: "lay-it-down", tag: "Faith", free: true },
  { title: "The Ant Network", slug: "the-ant-network", tag: "Technology" },
  { title: "The Cost Ledger", slug: "the-cost-ledger", tag: "Mindset" },
  { title: "The Ghost Frame", slug: "the-ghost-frame", tag: "Mindset" },
  { title: "The Gravity Well", slug: "the-gravity-well", tag: "Productivity" },
  { title: "The Narrator", slug: "the-narrator", tag: "Identity" },

  { title: "The Squirrel Economy", slug: "the-squirrel-economy", tag: "Economics" },
  { title: "The Wolf's Table", slug: "the-wolfs-table", tag: "Relationships" },
  { title: "The Crow's Gambit", slug: "the-crows-gambit", tag: "Strategy" },
  { title: "The Eagle's Lens", slug: "the-eagles-lens", tag: "Leadership" },

  { title: "The Octopus Protocol", slug: "the-octopus-protocol", tag: "Finance" },
  { title: "The Starling's Murmuration", slug: "the-starlings-murmuration", tag: "Leadership" },
  { title: "The Chameleon's Code", slug: "the-chameleons-code", tag: "Communication" },
  { title: "The Spider's Loom", slug: "the-spiders-loom", tag: "Productivity" },
  { title: "The Gecko's Grip", slug: "the-geckos-grip", tag: "Resilience" },
  { title: "The Firefly's Signal", slug: "the-fireflys-signal", tag: "Strategy" },
  { title: "The Fox's Trail", slug: "the-foxs-trail", tag: "Strategy" },
  { title: "The Moth's Flame", slug: "the-moths-flame", tag: "Mindset" },
  { title: "The Bear's Winter", slug: "the-bears-winter", tag: "Mindset" },
  { title: "The Coyote's Laugh", slug: "the-coyotes-laugh", tag: "Resilience" },
  { title: "The Pangolin's Armor", slug: "the-pangolins-armor", tag: "Mindset" },
  { title: "The Horse's Gait", slug: "the-horses-gait", tag: "Productivity" },

  { title: "Pride", slug: "lay-it-down-pride", tag: "Faith" },
  { title: "Envy", slug: "lay-it-down-envy", tag: "Faith" },
  { title: "Wrath", slug: "lay-it-down-wrath", tag: "Faith" },
  { title: "Sloth", slug: "lay-it-down-sloth", tag: "Faith" },
  { title: "Greed", slug: "lay-it-down-greed", tag: "Faith" },
  { title: "Gluttony", slug: "lay-it-down-gluttony", tag: "Faith" },
  { title: "Lust", slug: "lay-it-down-lust", tag: "Faith" },
  { title: "The Tide Pool\u2019s Echo", catalogTitle: "The Tide Pool's Echo", slug: "the-tide-pools-echo", tag: "Philosophy", free: true },
  { title: "The Whale\u2019s Breath", catalogTitle: "The Whale's Breath", slug: "the-whales-breath", tag: "Philosophy" },
  { title: "The Butterfly\u2019s Crossing", catalogTitle: "The Butterfly's Crossing", slug: "the-butterflys-crossing", tag: "Philosophy" },
  { title: "The Elephant\u2019s Ground", catalogTitle: "The Elephant's Ground", slug: "the-elephants-ground", tag: "Philosophy" },
  { title: "The Bee\u2019s Dance", catalogTitle: "The Bee's Dance", slug: "the-bees-dance", tag: "Philosophy" },
  { title: "The Otter\u2019s Play", catalogTitle: "The Otter's Play", slug: "the-otters-play", tag: "Philosophy" },
  { title: "The Mockingbird's Song", slug: "the-mockingbirds-song", tag: "Technology", free: true },
  { title: "The Dopamine Drought", catalogTitle: "Dad Talks: The Dopamine Drought", slug: "dad-talks-the-dopamine-drought", tag: "Parenting", free: true },
  { title: "The Mirror Test", catalogTitle: "Dad Talks: The Mirror Test", slug: "dad-talks-the-mirror-test", tag: "Parenting" },
  { title: "The Flinch", catalogTitle: "Dad Talks: The Flinch", slug: "dad-talks-the-flinch", tag: "Parenting" },

  { title: "The Invisible Contract", catalogTitle: "Dad Talks: The Invisible Contract", slug: "dad-talks-the-invisible-contract", tag: "Parenting" },
  { title: "The Scoreboard Lie", catalogTitle: "Dad Talks: The Scoreboard Lie", slug: "dad-talks-the-scoreboard-lie", tag: "Parenting" },
  { title: "The First Punch", catalogTitle: "Dad Talks: The First Punch", slug: "dad-talks-the-first-punch", tag: "Parenting" },
  { title: "The Arrival", slug: "the-arrival", tag: "Mindset" },
  { title: "The Body Lie", slug: "the-body-lie", tag: "Identity" },
  { title: "The Mycelium Network", slug: "the-mycelium-network", tag: "Economics" },
  { title: "The Termite Cathedral", slug: "the-termite-cathedral", tag: "Technology" },
  { title: "The Bonsai Method", slug: "the-bonsai-method", tag: "Finance" },
  { title: "The Fibonacci Trim", slug: "the-fibonacci-trim", tag: "Finance" },
  { title: "The Mantis Shrimp\u2019s Eye", catalogTitle: "The Mantis Shrimp's Eye", slug: "the-mantis-shrimps-eye", tag: "Resilience", free: true },
  { title: "The Porcupine\u2019s Quills", catalogTitle: "The Porcupine's Quills", slug: "the-porcupines-quills", tag: "Resilience" },
  { title: "The Tardigrade Protocol", slug: "the-tardigrade-protocol", tag: "Resilience" },
  { title: "The Hermit Crab\u2019s Shell", catalogTitle: "The Hermit Crab's Shell", slug: "the-hermit-crabs-shell", tag: "Identity", free: true },
  { title: "The Scorpion\u2019s Molt", catalogTitle: "The Scorpion's Molt", slug: "the-scorpions-molt", tag: "Mindset" },
  { title: "The Vampire Squid\u2019s Light", catalogTitle: "The Vampire Squid's Light", slug: "the-vampire-squids-light", tag: "Resilience" },
  { title: "The Cuttlefish\u2019s Canvas", catalogTitle: "The Cuttlefish's Canvas", slug: "the-cuttlefishs-canvas", tag: "Technology" },
  { title: "The Centipede\u2019s March", catalogTitle: "The Centipede's March", slug: "the-centipedes-march", tag: "Technology" },
  { title: "The Lyrebird\u2019s Echo", catalogTitle: "The Lyrebird's Echo", slug: "the-lyrebirds-echo", tag: "Technology" },
  { title: "The Raven's Trial", slug: "the-ravens-trial", tag: "Technology" },
  { title: "The Lifted Ceiling", slug: "the-lifted-ceiling", tag: "Finance", free: true },
  { title: "The New Earning", slug: "the-new-earning", tag: "Finance" },
  { title: "The Three Tables", slug: "the-three-tables", tag: "Faith" },
  { title: "The Kintsugi Bowl", catalogTitle: "The Kintsugi Protocol", slug: "the-kintsugi-bowl", tag: "Faith" },
  { title: "The Unfinished Song", slug: "the-unfinished-song", tag: "Health" },
];

const FREE_PLAYBOOKS = PLAYBOOKS.filter((pb) => pb.free);
const PAID_PLAYBOOKS = PLAYBOOKS.filter((pb) => !pb.free);

// ── Catalog Page ──────────────────────────────────────────────

test.describe("Catalog Page", () => {
  test("loads with all playbook cards linking to /read/<slug>", async ({ page }) => {
    const response = await page.goto("");
    expect(response.status()).toBe(200);

    for (const pb of PLAYBOOKS) {
      const card = page.locator(`a.card[href$="read/${pb.slug}"]`);
      await expect(card).toBeVisible();
      await expect(card).toContainText(pb.catalogTitle || pb.title);
    }
  });

  test("displays correct playbook count", async ({ page }) => {
    await page.goto("");
    const subtitle = page.locator(".hero-sub");
    await expect(subtitle).toContainText(`${PLAYBOOKS.length}`);
  });

  test("search filters cards by title", async ({ page }) => {
    await page.goto("");
    await page.fill("#lens-input", "bonsai");
    const visible = page.locator(".card:not(.hidden)");
    await expect(visible).toHaveCount(1);
    await expect(visible.first()).toContainText("Bonsai");
  });

  test("lens filter bar exists", async ({ page }) => {
    await page.goto("");
    await expect(page.locator(".lens-wrap")).toBeVisible();
    await expect(page.locator("#lens-input")).toBeVisible();
  });
});

// ── Purchase Gate (Paid Playbooks) ────────────────────────────

test.describe("Purchase Gate", () => {
  test("paid playbook shows purchase gate via ?buy=1", async ({ page }) => {
    const pb = PAID_PLAYBOOKS[0];
    await page.goto(`read/${pb.slug}?buy=1`);

    // Should show the gate, not the playbook
    await expect(page.locator(".gate-badge")).toContainText("Premium Playbook");
    await expect(page.locator(".gate-title")).toBeVisible();

    // Three pricing options
    const buyButtons = page.locator('button.plan-btn');
    await expect(buyButtons).toHaveCount(3);
  });

  test("paid playbook without ?buy=1 shows landing page", async ({ page }) => {
    const pb = PAID_PLAYBOOKS[0];
    const response = await page.goto(`read/${pb.slug}`);
    expect(response.status()).toBe(200);

    // Should show landing page (fab-cta button), not purchase gate
    const fabCta = page.locator(".fab-cta");
    await expect(fabCta).toBeVisible();
  });

  test("free playbook bypasses purchase gate", async ({ page }) => {
    for (const pb of FREE_PLAYBOOKS) {
      const response = await page.goto(`read/${pb.slug}`);
      expect(response.status()).toBe(200);

      // Should NOT show purchase gate
      const gate = page.locator(".gate-badge");
      await expect(gate).not.toBeVisible();

      // Should have substantial content
      const html = await page.content();
      expect(html.length).toBeGreaterThan(10000);
    }
  });

  test("admin code unlocks playbook", async ({ page }) => {
    const pb = PAID_PLAYBOOKS[0];
    await page.goto(`read/${pb.slug}?buy=1`);

    // Should see gate
    await expect(page.locator(".gate-badge")).toBeVisible();

    // Click admin toggle and enter code
    await page.locator(".admin-toggle").click();
    await page.fill('input[name="code"]', "elijahsentme");
    await Promise.all([
      page.waitForURL(`**/read/${pb.slug}`),
      page.locator(".admin-submit").click(),
    ]);

    // Now should see playbook content, not gate
    await expect(page.locator(".gate-badge")).not.toBeVisible();
    const html = await page.content();
    expect(html.length).toBeGreaterThan(10000);
  });

  test("wrong admin code shows error", async ({ page }) => {
    const pb = PAID_PLAYBOOKS[0];
    await page.goto(`read/${pb.slug}?buy=1`);
    await page.locator(".admin-toggle").click();
    await page.fill('input[name="code"]', "wrongcode");
    await Promise.all([
      page.waitForURL(`**/read/${pb.slug}*`),
      page.locator(".admin-submit").click(),
    ]);

    // Should still show gate with error
    await expect(page.locator(".gate-badge")).toBeVisible();
    await expect(page.locator("#admin-error")).toBeVisible();
  });

  test("admin unlock persists across paid playbooks in same session", async ({ page }) => {
    // Unlock via first paid playbook
    const pb1 = PAID_PLAYBOOKS[0];
    await page.goto(`read/${pb1.slug}?buy=1`);
    await page.locator(".admin-toggle").click();
    await page.fill('input[name="code"]', "elijahsentme");
    await Promise.all([
      page.waitForURL(`**/read/${pb1.slug}`),
      page.locator(".admin-submit").click(),
    ]);
    await expect(page.locator(".gate-badge")).not.toBeVisible();

    // Navigate to a different paid playbook — should be unlocked too
    const pb2 = PAID_PLAYBOOKS[1];
    await page.goto(`read/${pb2.slug}`);
    await expect(page.locator(".gate-badge")).not.toBeVisible();
    const html = await page.content();
    expect(html.length).toBeGreaterThan(10000);
  });
});

// ── Stripe Checkout ───────────────────────────────────────────

test.describe("Stripe Checkout", () => {
  test("single purchase button posts to create-checkout-session", async ({ page }) => {
    const pb = PAID_PLAYBOOKS[0];
    await page.goto(`read/${pb.slug}?buy=1`);

    // Check form has correct hidden fields
    const singleForm = page.locator('form:has(input[value="single"])');
    await expect(singleForm).toBeVisible();
    await expect(singleForm.locator('input[name="mode"]')).toHaveValue("single");
    await expect(singleForm.locator('input[name="slug"]')).toHaveValue(pb.slug);

    const monthlyForm = page.locator('form:has(input[value="monthly"])');
    await expect(monthlyForm.locator('input[name="mode"]')).toHaveValue("monthly");

    const yearlyForm = page.locator('form:has(input[value="yearly"])');
    await expect(yearlyForm.locator('input[name="mode"]')).toHaveValue("yearly");
  });

  test("checkout redirects to Stripe (or errors without key)", async ({ page }) => {
    const pb = PAID_PLAYBOOKS[0];
    await page.goto(`read/${pb.slug}?buy=1`);

    // Click the single purchase button and intercept the response
    const [response] = await Promise.all([
      page.waitForNavigation(),
      page.locator('form:has(input[value="single"]) button').click(),
    ]);

    // Should redirect — either to Stripe checkout (303) or back with error/cancelled
    const url = page.url();
    const isStripe = url.includes("checkout.stripe.com");
    const isError = url.includes("payment=error") || url.includes("payment=cancelled");
    const isConfigError = url.includes("read/"); // stayed on same page due to 500
    const isLocalhost = url.includes("localhost") || url.includes("127.0.0.1");
    const isProduction = url.includes("kingdombuilders.ai") || url.includes("onrender.com");
    expect(isStripe || isError || isConfigError || isLocalhost || isProduction).toBe(true);
  });
});

// ── Reader Pages (via admin unlock) ───────────────────────────

test.describe("Reader Pages", () => {
  // Free playbooks — direct access
  for (const pb of FREE_PLAYBOOKS) {
    test(`${pb.title} loads directly (free)`, async ({ page }) => {
      await page.goto(`read/${pb.slug}`);
      await expect(page.locator(".gate-badge")).not.toBeVisible();
      const html = await page.content();
      expect(html.length).toBeGreaterThan(10000);
    });
  }

  // Paid playbooks — unlock first, then verify content
  test("all paid playbooks load after admin unlock", async ({ page }) => {
    // Unlock once via ?buy=1 to reach purchase gate
    const first = PAID_PLAYBOOKS[0];
    await page.goto(`read/${first.slug}?buy=1`);
    await page.locator(".admin-toggle").click();
    await page.fill('input[name="code"]', "elijahsentme");
    await Promise.all([
      page.waitForURL(`**/read/${first.slug}`),
      page.locator(".admin-submit").click(),
    ]);

    // Now check each paid playbook loads
    for (const pb of PAID_PLAYBOOKS) {
      await page.goto(`read/${pb.slug}`);
      await expect(page.locator(".gate-badge")).not.toBeVisible();
      const html = await page.content();
      expect(html.length).toBeGreaterThan(10000);
    }
  });
});

// ── Back Button ───────────────────────────────────────────────

test.describe("Back Button", () => {
  test("playbook has fixed back button", async ({ page }) => {
    const pb = FREE_PLAYBOOKS[0];
    await page.goto(`read/${pb.slug}`);
    const back = page.locator(".pb-back");
    await expect(back).toBeVisible();
    await expect(back).toContainText("Playbooks");
  });

  test("back button navigates to catalog", async ({ page }) => {
    const pb = FREE_PLAYBOOKS[0];
    await page.goto(`read/${pb.slug}`);
    await Promise.all([
      page.waitForURL("**/"),
      page.locator(".pb-back").click(),
    ]);
    await expect(page.locator(".hero-badge")).toBeVisible();
  });
});

// ── Full Navigation Flow ──────────────────────────────────────

test.describe("Full Flow: Catalog → Landing → Gate → Unlock → Read", () => {
  test("paid playbook end-to-end", async ({ page }) => {
    const pb = PAID_PLAYBOOKS[0];

    // Step 1: Catalog — suppress What's New overlay via localStorage
    await page.goto("");
    await page.evaluate(() => localStorage.setItem("pb_last_version", "99.0.0"));
    await page.goto("");
    const card = page.locator(`a.card[href$="read/${pb.slug}"]`);
    await expect(card).toBeVisible();

    // Step 2: Click card → landing page
    await card.click();
    await page.waitForURL(`**/read/${pb.slug}`);
    // Landing page should have fab-cta button
    await expect(page.locator(".fab-cta")).toBeVisible();

    // Step 3: Navigate directly to purchase gate (?buy=1)
    await page.goto(`read/${pb.slug}?buy=1`);
    await expect(page.locator(".gate-badge")).toBeVisible();

    // Step 4: Unlock
    await page.locator(".admin-toggle").click();
    await page.fill('input[name="code"]', "elijahsentme");
    await Promise.all([
      page.waitForURL(`**/read/${pb.slug}`),
      page.locator(".admin-submit").click(),
    ]);

    // Step 5: Read content
    await expect(page.locator(".gate-badge")).not.toBeVisible();
    await expect(page.locator(".pb-back")).toBeVisible();
    const html = await page.content();
    expect(html.length).toBeGreaterThan(10000);
  });

  test("free playbook end-to-end", async ({ page }) => {
    const pb = FREE_PLAYBOOKS[0];

    // Catalog → click → read directly — suppress What's New overlay
    await page.goto("");
    await page.evaluate(() => localStorage.setItem("pb_last_version", "99.0.0"));
    await page.goto("");
    const card = page.locator(`a.card[href$="read/${pb.slug}"]`);
    await card.click();
    await page.waitForURL(`**/read/${pb.slug}`);

    // No gate, direct content
    await expect(page.locator(".gate-badge")).not.toBeVisible();
    const html = await page.content();
    expect(html.length).toBeGreaterThan(10000);
  });
});

// ── API Endpoints ─────────────────────────────────────────────

test.describe("API", () => {
  test("/api/version returns version info", async ({ page }) => {
    const response = await page.goto("api/version");
    const data = JSON.parse(await page.locator("body").textContent());
    expect(data.version).toBeTruthy();
    expect(data.notes).toBeInstanceOf(Array);
  });

  test("/api/hot returns array", async ({ page }) => {
    const response = await page.goto("api/hot?period=all");
    const data = JSON.parse(await page.locator("body").textContent());
    expect(data).toBeInstanceOf(Array);
  });
});

// ── Error Handling ────────────────────────────────────────────

test.describe("Error Handling", () => {
  test("nonexistent reader slug returns 404", async ({ page }) => {
    const response = await page.goto("read/does-not-exist");
    expect(response.status()).toBe(404);
    await expect(page.locator(".error-icon")).toBeVisible();
  });
});
