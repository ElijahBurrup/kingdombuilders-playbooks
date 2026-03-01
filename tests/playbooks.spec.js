// @ts-check
const { test, expect } = require("@playwright/test");

/**
 * Master registry of all playbooks.
 * When adding a new playbook via SetHut, add an entry here.
 */
const PLAYBOOKS = [
  {
    title: "The Conductor's Playbook",
    route: "/conductorsplaybook",
    readerSlug: "conductors-playbook",
    tag: "Productivity",
  },
  {
    title: "Lay It Down",
    route: "/layitdown",
    readerSlug: "lay-it-down",
    tag: "Faith",
  },
  {
    title: "The Ant Network",
    route: "/theantnetwork",
    readerSlug: "the-ant-network",
    tag: "Technology",
  },
  {
    title: "The Cost Ledger",
    route: "/thecostledger",
    readerSlug: "the-cost-ledger",
    tag: "Mindset",
  },
  {
    title: "The Ghost Frame",
    route: "/theghostframe",
    readerSlug: "the-ghost-frame",
    tag: "Mindset",
  },
  {
    title: "The Gravity Well",
    route: "/thegravitywell",
    readerSlug: "the-gravity-well",
    tag: "Productivity",
  },
  {
    title: "The Narrator",
    route: "/thenarrator",
    readerSlug: "the-narrator",
    tag: "Identity",
  },
  {
    title: "The Salmon Journey",
    route: "/thesalmonjourney",
    readerSlug: "the-salmon-journey",
    tag: "Finance",
  },
  {
    title: "The Squirrel Economy",
    route: "/thesquirreleconomy",
    readerSlug: "the-squirrel-economy",
    tag: "Economics",
  },
  {
    title: "The Wolf's Table",
    route: "/thewolfstable",
    readerSlug: "the-wolfs-table",
    tag: "Relationships",
  },
  {
    title: "The Crow's Gambit",
    route: "/thecrowsgambit",
    readerSlug: "the-crows-gambit",
    tag: "Strategy",
  },
  {
    title: "The Eagle's Lens",
    route: "/theeagleslens",
    readerSlug: "the-eagles-lens",
    tag: "Leadership",
  },
  {
    title: "The Lighthouse Keeper's Log",
    route: "/thelighthousekeeperslog",
    readerSlug: "the-lighthouse-keepers-log",
    tag: "Mindset",
  },
  {
    title: "The Octopus Protocol",
    route: "/theoctopusprotocol",
    readerSlug: "the-octopus-protocol",
    tag: "Finance",
  },
  {
    title: "The Starling's Murmuration",
    route: "/thestarlingsmurmuration",
    readerSlug: "the-starlings-murmuration",
    tag: "Leadership",
  },
  {
    title: "The Chameleon's Code",
    route: "/thechameleonscode",
    readerSlug: "the-chameleons-code",
    tag: "Communication",
  },
  {
    title: "The Spider's Loom",
    route: "/thespidersloom",
    readerSlug: "the-spiders-loom",
    tag: "Productivity",
  },
  {
    title: "The Gecko's Grip",
    route: "/thegeckosgrip",
    readerSlug: "the-geckos-grip",
    tag: "Resilience",
  },
  {
    title: "The Firefly's Signal",
    route: "/thefireflyssignal",
    readerSlug: "the-fireflys-signal",
    tag: "Strategy",
  },
  {
    title: "The Fox's Trail",
    route: "/thefoxstrail",
    readerSlug: "the-foxs-trail",
    tag: "Strategy",
  },
  {
    title: "The Moth's Flame",
    route: "/themothsflame",
    readerSlug: "the-moths-flame",
    tag: "Mindset",
  },
  {
    title: "The Bear's Winter",
    route: "/thebearswinter",
    readerSlug: "the-bears-winter",
    tag: "Mindset",
  },
  {
    title: "The Coyote's Laugh",
    route: "/thecoyoteslaugh",
    readerSlug: "the-coyotes-laugh",
    tag: "Resilience",
  },
  {
    title: "The Pangolin's Armor",
    route: "/thepangolinsarmor",
    readerSlug: "the-pangolins-armor",
    tag: "Mindset",
  },
  {
    title: "The Horse's Gait",
    route: "/thehorsesgait",
    readerSlug: "the-horses-gait",
    tag: "Productivity",
  },
];

// ── Catalog Page ──────────────────────────────────────────────

test.describe("Catalog Page", () => {
  test("loads successfully with all playbook cards", async ({ page }) => {
    const response = await page.goto("/");
    expect(response.status()).toBe(200);

    // Verify every playbook has a card in the catalog
    for (const pb of PLAYBOOKS) {
      const card = page.locator(`a.card[href="${pb.route}"]`);
      await expect(card).toBeVisible();
      await expect(card).toContainText(pb.title);
    }
  });

  test("displays correct playbook count in subtitle", async ({ page }) => {
    await page.goto("/");
    const subtitle = page.locator(".hero-sub");
    await expect(subtitle).toContainText(`${PLAYBOOKS.length}`);
  });

  test("all catalog card links are clickable and resolve", async ({ page }) => {
    await page.goto("/");
    for (const pb of PLAYBOOKS) {
      const card = page.locator(`a.card[href="${pb.route}"]`);
      const href = await card.getAttribute("href");
      expect(href).toBe(pb.route);
    }
  });
});

// ── Landing Pages ─────────────────────────────────────────────

test.describe("Landing Pages", () => {
  for (const pb of PLAYBOOKS) {
    test(`${pb.title} landing page loads (${pb.route})`, async ({ page }) => {
      const response = await page.goto(pb.route);
      expect(response.status()).toBe(200);

      // Should NOT be the error page
      const errorIcon = page.locator(".error-icon");
      await expect(errorIcon).not.toBeVisible();

      // Should contain the playbook title somewhere
      await expect(page.locator("body")).toContainText(pb.title.replace(/'/g, "\u2019").replace(/'/g, "'"));
    });

    test(`${pb.title} landing page has a read CTA`, async ({ page }) => {
      await page.goto(pb.route);

      // Every landing page should have a link to /read/<slug>
      const ctaLink = page.locator(`a[href="/read/${pb.readerSlug}"]`);
      await expect(ctaLink).toBeVisible();
    });
  }
});

// ── Reader Pages (Full Playbook) ──────────────────────────────

test.describe("Reader Pages", () => {
  for (const pb of PLAYBOOKS) {
    test(`${pb.title} full playbook loads (/read/${pb.readerSlug})`, async ({
      page,
    }) => {
      const response = await page.goto(`/read/${pb.readerSlug}`);
      expect(response.status()).toBe(200);

      // Should NOT be the error page
      const errorIcon = page.locator(".error-icon");
      await expect(errorIcon).not.toBeVisible();

      // Full playbook should have substantial content (> 10KB)
      const html = await page.content();
      expect(html.length).toBeGreaterThan(10000);
    });
  }
});

// ── End to End: Catalog → Landing → Reader ────────────────────

test.describe("Full Navigation Flow", () => {
  for (const pb of PLAYBOOKS) {
    test(`${pb.title}: catalog → landing → reader`, async ({ page }) => {
      // Step 1: Start at catalog
      await page.goto("/");

      // Step 2: Click the playbook card
      const card = page.locator(`a.card[href="${pb.route}"]`);
      await card.click();
      await page.waitForURL(`**${pb.route}`);
      expect(page.url()).toContain(pb.route);

      // Step 3: Click the read CTA
      const ctaLink = page.locator(`a[href="/read/${pb.readerSlug}"]`);
      await ctaLink.click();
      await page.waitForURL(`**/read/${pb.readerSlug}`);
      expect(page.url()).toContain(`/read/${pb.readerSlug}`);

      // Step 4: Verify full playbook rendered (not error page)
      const errorIcon = page.locator(".error-icon");
      await expect(errorIcon).not.toBeVisible();
      const html = await page.content();
      expect(html.length).toBeGreaterThan(10000);
    });
  }
});

// ── Error Handling ────────────────────────────────────────────

test.describe("Error Handling", () => {
  test("nonexistent reader slug returns 404 error page", async ({ page }) => {
    const response = await page.goto("/read/does-not-exist");
    expect(response.status()).toBe(404);

    const errorIcon = page.locator(".error-icon");
    await expect(errorIcon).toBeVisible();
  });

  test("nonexistent route returns 404", async ({ page }) => {
    const response = await page.goto("/nonexistentplaybook");
    expect(response.status()).toBe(404);
  });
});
