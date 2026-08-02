// Basic tests — standard @playwright/test
import { test, expect } from '@playwright/test';

// With the production fixture (fonts, JS animations, lazy images):
// import { test, expect, waitForPageReady } from '../fixtures/visual';

// ─────────────────────────────────────────────
// Basic: full page screenshot
// ─────────────────────────────────────────────
test('homepage', async ({ page }) => {
  await page.goto('/');

  // locator.waitFor() is the modern API — prefer over page.waitForSelector()
  await page.locator('h1').waitFor();

  // If using fixture: await waitForPageReady(page);

  await expect(page).toHaveScreenshot('homepage.png', {
    fullPage: true,
  });
});

// ─────────────────────────────────────────────
// Element-level screenshot
// ─────────────────────────────────────────────
test('heading', async ({ page }) => {
  await page.goto('/');
  await page.locator('h1').waitFor();

  await expect(page.locator('h1')).toHaveScreenshot('heading.png');
});

// ─────────────────────────────────────────────
// With dynamic content masked (adapt selectors to your app)
// ─────────────────────────────────────────────
// test('page with live data', async ({ page }) => {
//   await page.goto('/your-route');
//   await page.locator('[data-testid="loaded"]').waitFor();
//
//   await expect(page).toHaveScreenshot('page-live-data.png', {
//     fullPage: true,
//     mask: [
//       page.locator('[data-testid="live-price"]'),
//       page.locator('[data-testid="timestamp"]'),
//     ],
//   });
// });

// ─────────────────────────────────────────────
// With fixture: fonts + JS animations + lazy images
// ─────────────────────────────────────────────
// import { test, expect, waitForPageReady } from '../fixtures/visual';
//
// test('page with animations', async ({ page }) => {
//   await page.goto('/');
//   await page.locator('h1').waitFor();
//   await waitForPageReady(page);   // freeze fonts, images, GSAP
//   await expect(page).toHaveScreenshot('animated-page.png', { fullPage: true });
// });
