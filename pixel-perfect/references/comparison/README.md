# Comparison — Running Visual Tests

## Run Tests

```bash
# Compare all pages against baseline
npx playwright test

# Specific test file
npx playwright test tests/visual.spec.ts

# Specific viewport/project
npx playwright test --project=Desktop
npx playwright test --project=Mobile
```

## Read Results

```
✓ homepage (Desktop) — passed
✗ dashboard (Desktop) — 1243 pixels differ (0.86%)
✓ homepage (Mobile) — passed
```

## Open HTML Report with Visual Diffs

```bash
npx playwright show-report
```

Report shows:
- Side-by-side: **Expected** | **Actual** | **Diff** (red = changed pixels)
- Pixel diff count and percentage
- Which viewport failed

## Interpreting Diffs

| Diff Pattern | Likely Cause | Fix |
|---|---|---|
| Red pixels scattered everywhere | Font rendering / anti-aliasing | Increase `threshold` to `0.3` |
| Solid red block | Element moved or changed | Review layout change |
| Red at bottom of page | Content height changed | Check new content added |
| Thin red line | Border or shadow changed | Verify design intent |
| Entire page differs | Cross-platform baseline mismatch | Regenerate baseline in Docker |

## Common Fixes

**False positives (fonts, shadows):**
```typescript
await expect(page).toHaveScreenshot('page.png', {
  maxDiffPixelRatio: 0.02,  // allow 2%
  threshold: 0.3,            // less sensitive per-pixel
});
```

**Ignore dynamic areas:**
```typescript
await expect(page).toHaveScreenshot('page.png', {
  mask: [page.locator('.animated-counter'), page.locator('[data-live]')],
});
```

**Clip to specific element only:**
```typescript
const section = page.locator('.hero-section');
await expect(section).toHaveScreenshot('hero.png');
```

**Still flaky after masking? Use the production fixture:**
The [fixtures/visual.ts](../fixtures/visual.ts) handles JS animation frameworks
(Framer Motion, GSAP, Lottie), lazy-loaded images, and font loading at the
fixture level — no per-test boilerplate required.

```typescript
// Replace the standard import with the fixture:
import { test, expect } from '../fixtures/visual';
```

**Entire page is different (cross-platform):**
If baselines were captured on macOS but CI runs Linux, regenerate baselines in Docker:
```bash
docker run --rm -v $(pwd):/work -w /work \
  mcr.microsoft.com/playwright:v1.50.1-noble \
  npx playwright test --update-snapshots
```
