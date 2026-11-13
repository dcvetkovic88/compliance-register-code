import { test } from "@playwright/test";

test("waits for the worker", async ({ page }) => {
  await page.waitForTimeout(500);
});
