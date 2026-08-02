import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  snapshotDir: './snapshots',
  // {testFileDir}/{testFileName} keeps the path readable without .ts-as-directory quirk
  snapshotPathTemplate: '{snapshotDir}/{projectName}/{testFileDir}/{testFileName}/{arg}{ext}',

  // Run tests in parallel within each file
  fullyParallel: true,
  // GitHub Actions ubuntu-latest = 2 vCPUs. Higher values increase screenshot timing
  // variability and make diffs non-deterministic. Use 2 in CI, unlimited locally.
  workers: process.env.CI ? 2 : undefined,

  // ⚠️ Visual regression tests should NOT retry.
  // A retry overwrites diff artifacts, making it impossible to diagnose whether the
  // failure was a flake or a real regression. If you see flakiness, fix it with the
  // visual fixture (Workflow E) instead of masking it with retries.
  retries: 0,

  // Stop after 10 failures in CI — don't waste time if something is globally broken.
  // 0 means "no limit" (unintuitive API — 0 ≠ "stop immediately").
  maxFailures: process.env.CI ? 10 : 0,

  // CI:    'none' — missing baseline = test fails. Baselines must be committed to git.
  //        ⚠️ New tests added in a PR will fail in CI until baselines are generated
  //        via the update-snapshots.yml workflow and committed. This is intentional.
  // Local: 'missing' — create new baselines automatically, never overwrite existing ones.
  //        Use `npx playwright test --update-snapshots` to overwrite changed ones.
  updateSnapshots: process.env.CI ? 'none' : 'missing',

  // Reporter: CI → dot + HTML report (open:'never' — no browser in CI)
  //           Local → list (verbose) + HTML report (opens on failure)
  reporter: process.env.CI
    ? [['dot'], ['html', { open: 'never', outputFolder: 'playwright-report' }]]
    : [['list'], ['html', { open: 'on-failure', outputFolder: 'playwright-report' }]],

  use: {
    // Set your actual dev server URL, or override via env variable:
    //   BASE_URL=https://staging.example.com npx playwright test
    baseURL: process.env.BASE_URL || 'http://localhost:3000',

    // ⚠️ reducedMotion: 'reduce' sets prefers-reduced-motion CSS media query.
    // Apps that respond to this query will render a DIFFERENT visual state
    // (e.g., no fade-in, instant transitions). You are testing the reduced-motion
    // layout, not the default one. If your app doesn't handle prefers-reduced-motion,
    // this has no effect. If it does — make sure your baselines match this state.
    // Remove this line if you want to test the default (animated) visual state.
    reducedMotion: 'reduce',
  },

  expect: {
    toHaveScreenshot: {
      // animations: 'disabled' freezes CSS transitions + Web Animations API at
      // screenshot time via DevTools protocol. This is already the default.
      animations: 'disabled',
      maxDiffPixelRatio: 0.01, // allow up to 1% of pixels to differ
      // threshold: per-pixel color sensitivity (0–1).
      // 0.05 = a pixel must differ by >5% of full color range to count as changed.
      // Increase to 0.1 or 0.2 only if font anti-aliasing causes false positives.
      threshold: 0.05,
    },
  },

  // Uncomment to auto-start your dev server before tests.
  // Without this, start the server manually before running `npx playwright test`.
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:3000',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 30_000,
  // },

  projects: [
    {
      name: 'Desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 900 },
      },
    },
    {
      name: 'Tablet',
      use: {
        // Spread device for correct user agent, touch emulation, deviceScaleFactor.
        // Override viewport to exact dimensions needed.
        ...devices['iPad (gen 7)'],
        viewport: { width: 768, height: 1024 },
      },
    },
    {
      name: 'Mobile',
      use: {
        // Spread device for correct mobile user agent and touch emulation.
        // Override viewport to exact dimensions needed.
        ...devices['iPhone 13'],
        viewport: { width: 375, height: 812 },
      },
    },
  ],
});
