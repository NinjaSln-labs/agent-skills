# Baseline — Capturing Reference Screenshots

Baseline = the "source of truth" screenshots. Stored in `snapshots/`. **Commit them to git.**

## First Run (create baseline)

### Recommended: generate inside Docker (cross-platform safe)

macOS and Linux render fonts differently. Use the Playwright Docker image to generate
baselines in the same environment as your Linux CI:

```bash
docker run --rm \
  -v $(pwd):/work -w /work \
  mcr.microsoft.com/playwright:v1.50.1-noble \
  npx playwright test --update-snapshots
```

Then commit:

```bash
git add snapshots/
git commit -m "chore: add visual regression baselines"
```

### Alternative: generate locally

Only if your CI also runs on the same OS (e.g., macOS CI, or same-platform team):

```bash
npx playwright test --update-snapshots
```

## When to Update Baseline

Update when you **intentionally changed** the design (not a bug):

```bash
# Recommended: via Docker (cross-platform safe)
docker run --rm \
  -v $(pwd):/work -w /work \
  mcr.microsoft.com/playwright:v1.50.1-noble \
  npx playwright test --update-snapshots

# Or locally (if OS matches CI)
npx playwright test --update-snapshots

# Update specific test only
npx playwright test tests/visual.spec.ts --update-snapshots
```

> **⚠️ Never auto-update in CI.**
> If CI automatically updates snapshots on failure, regressions are silently hidden.
> Use the [update-snapshots workflow](../../.github/workflows/update-snapshots.yml)
> for intentional updates — it requires a reason and commits with attribution.

## Baseline File Structure

Playwright organizes snapshots by project name and test file path.
With the default `snapshotPathTemplate` in `playwright.config.ts`:

```
snapshots/
├── Desktop/
│   └── tests/
│       └── visual.spec.ts/
│           ├── homepage.png
│           └── dashboard.png
└── Mobile/
    └── tests/
        └── visual.spec.ts/
            ├── homepage.png
            └── dashboard.png
```

> Structure depends on your `snapshotPathTemplate`.
> Template `{snapshotDir}/{projectName}/{testFilePath}/{arg}{ext}` → structure above.

## Mask Dynamic Content

Prices, timestamps, and live data cause false positives. Mask them:

```typescript
await expect(page).toHaveScreenshot('page.png', {
  mask: [
    page.locator('.live-price'),
    page.locator('.timestamp'),
    page.locator('[data-testid="animated-counter"]'),
  ],
  fullPage: true,
});
```

## .gitignore Guidance

```gitignore
# Never commit — generated diffs and test artifacts
test-results/
playwright-report/

# Always commit — the baseline
# snapshots/   ← do NOT gitignore this
```
