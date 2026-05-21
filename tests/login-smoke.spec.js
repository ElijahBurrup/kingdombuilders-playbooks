// @ts-check
// Smoke test: real end-to-end login. Run on every deploy.
const { test, expect } = require("@playwright/test");

const PROD = "https://kingdombuilders.ai/playbooks";
// Real subscriber account. Replace or extend with additional accounts as
// passwords are confirmed. djburrup@gmail.com / luckydjb is stale on prod
// and was removed 2026-05-21 after this test surfaced "Invalid email or
// password" on every login.
const ACCOUNTS = [
  { label: "Subscriber A", email: "elijahburrup323@gmail.com", password: "Eli624462!" },
];

for (const acct of ACCOUNTS) {
  test(`Login + see protected content — ${acct.label}`, async ({ page }) => {
    // 1. Land on /auth
    await page.goto(PROD + "/auth", { waitUntil: "domcontentloaded" });

    // 2. Capture what we see (screenshot for diagnosis on failure)
    await page.screenshot({ path: `test-results/login-${acct.label.replace(/\W+/g, "-")}-1-auth.png`, fullPage: true });

    // 3. Find login form scope. The auth page has tabs that ALSO say "Sign In"
    //    so we must scope to the active login panel's form to avoid clicking
    //    a tab instead of the submit button.
    const loginForm = page.locator('form[action$="/auth/login"]').first();
    const emailInput = loginForm.locator('input[name="email"]');
    const passwordInput = loginForm.locator('input[name="password"]');
    const submitButton = loginForm.locator('button[type="submit"]');

    await expect(emailInput, "email input is on the page").toBeVisible({ timeout: 10000 });
    await expect(passwordInput, "password input is on the page").toBeVisible();
    await expect(submitButton, "submit button is on the page").toBeVisible();

    // 4. Fill + submit
    await emailInput.fill(acct.email);
    await passwordInput.fill(acct.password);

    // 5. Wait for navigation away from /auth (success) OR for an error message
    const navPromise = page.waitForURL((url) => !url.toString().includes("/auth"), { timeout: 15000 }).catch(() => null);
    await submitButton.click();
    await navPromise;

    // 6. Where are we now?
    const finalUrl = page.url();
    await page.screenshot({ path: `test-results/login-${acct.label.replace(/\W+/g, "-")}-2-after-submit.png`, fullPage: true });

    // 7. Check we landed somewhere logged-in (not auth) and the body says so
    expect(finalUrl, `should not still be on /auth after login`).not.toContain("/auth");

    // 8. Verify we can hit a paid playbook (proves session works)
    await page.goto(PROD + "/read/the-conductors-playbook", { waitUntil: "domcontentloaded" });
    await page.screenshot({ path: `test-results/login-${acct.label.replace(/\W+/g, "-")}-3-protected-content.png`, fullPage: true });

    // Subscriber should see the playbook content, not the paywall
    // The paywall typically has language like "Subscribe" or "Sign in to read"
    const bodyText = await page.locator("body").innerText();
    const onPaywall = /sign in to read|subscribe to access|please sign in/i.test(bodyText);
    expect(onPaywall, `should NOT see paywall on a paid playbook when logged in`).toBe(false);
  });
}
