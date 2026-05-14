// @ts-check
const { test, expect } = require("@playwright/test");

const PROD = "https://kingdombuilders.ai/playbooks";

// Free playbook so the test doesn't have to log in or pay
const FREE_PLAYBOOK = "the-tide-pools-echo";

test.describe("In-playbook share button", () => {
  test("Free playbook has a top floating share button and a bottom share panel", async ({ page }) => {
    await page.goto(`${PROD}/read/${FREE_PLAYBOOK}`);

    const topBtn = page.locator("button.pb-share-top");
    await expect(topBtn).toBeVisible();
    await expect(topBtn).toContainText(/share/i);

    const bottomBtn = page.locator("button.pb-share-bottom-btn");
    await expect(bottomBtn).toBeVisible();
    await expect(bottomBtn).toContainText(/share this playbook/i);
  });

  test("Share data is embedded with this playbook's title", async ({ page }) => {
    await page.goto(`${PROD}/read/${FREE_PLAYBOOK}`);
    const raw = await page.locator("#pb-share-data").innerText();
    const data = JSON.parse(raw);
    expect(data.slug).toBe(FREE_PLAYBOOK);
    expect(data.title.length).toBeGreaterThan(3);
  });

  test("Clicking top share triggers navigator.share (with stub), URL goes through /r/ for signed-in user", async ({ page, context }) => {
    // Stub /auth/status before navigation so the script sees a referral_code
    await context.route("**/playbooks/auth/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          signed_in: true,
          is_admin: false,
          is_subscriber: false,
          referral_code: "TEST42",
        }),
      })
    );

    // Stub navigator.share before any page script runs
    await page.addInitScript(() => {
      window.__pbShareCalls = [];
      // @ts-ignore
      navigator.share = (data) => {
        window.__pbShareCalls.push(data);
        return Promise.resolve();
      };
    });

    await page.goto(`${PROD}/read/${FREE_PLAYBOOK}`);
    // Give the auth/status fetch a moment to land
    await page.waitForTimeout(500);

    // Use the bottom button: the top floating chip can be obscured by the
    // playbook's cover hero on initial load. The share handler is shared.
    const btn = page.locator("button.pb-share-bottom-btn");
    await btn.scrollIntoViewIfNeeded();
    await btn.click();

    const calls = await page.evaluate(() => window.__pbShareCalls);
    expect(calls).toHaveLength(1);
    expect(calls[0].url).toContain(`/playbooks/r/TEST42`);
    expect(calls[0].url).toContain(`next=`);
    expect(decodeURIComponent(calls[0].url.split("next=")[1])).toContain(
      `/playbooks/read/${FREE_PLAYBOOK}`
    );
  });

  test("Anonymous user gets bare playbook URL without /r/ prefix", async ({ page, context }) => {
    await context.route("**/playbooks/auth/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          signed_in: false,
          is_admin: false,
          is_subscriber: false,
          referral_code: null,
        }),
      })
    );
    await page.addInitScript(() => {
      window.__pbShareCalls = [];
      // @ts-ignore
      navigator.share = (data) => {
        window.__pbShareCalls.push(data);
        return Promise.resolve();
      };
    });

    await page.goto(`${PROD}/read/${FREE_PLAYBOOK}`);
    await page.waitForTimeout(500);
    await page.locator("button.pb-share-bottom-btn").click();

    const calls = await page.evaluate(() => window.__pbShareCalls);
    expect(calls).toHaveLength(1);
    expect(calls[0].url).not.toContain("/r/");
    expect(calls[0].url).toContain(`/playbooks/read/${FREE_PLAYBOOK}`);
  });
});
