import { expect, test } from "@playwright/test";

/**
 * Smoke E2E for the first vertical workflow.
 * Requires frontend + backend running with a clean environment.
 */

test("register, onboard, create account", async ({ page }) => {
  const stamp = Date.now();
  const email = `user${stamp}@example.com`;

  await page.goto("/register");
  await page.getByLabel("Display name").fill("Primary User");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill("password123");
  await page.getByRole("button", { name: /create account/i }).click();

  await page.waitForURL(/onboarding/);
  await page.getByLabel("Household name").fill("Sample Household");
  await page.getByLabel(/Person 1 name/).fill("Person 1");
  await page.getByRole("button", { name: /complete onboarding/i }).click();

  await page.waitForURL(/accounts/);
  await page.getByLabel("Account name").fill("Everyday Chequing");
  await page.getByRole("button", { name: /create account/i }).click();
  await expect(page.getByText("Everyday Chequing")).toBeVisible();
});
