---
name: visual-regression-tester
description: >-
  Visual Regression Tester: screenshot comparison, diff detection, and CI integration
  using Playwright or Chromatic. Use when users request visual testing, screenshot
  testing, UI regression, visual diff, or Chromatic setup. For free local
  flows prefer a no-service comparator; use this when you need hosted Chromatic baselines.
slug: visual-regression-tester
version: 1.1.1
displayName: visual-regression-tester
---

# Visual Regression Tester

**Note:** Use pixel-perfect by default (free); use this skill for hosted Chromatic baselines.

## When to use / NOT for

- **Use when**: the user asks to set up visual regression / screenshot testing, a visual diff pipeline, hosted Chromatic baselines, or to debug why screenshots changed.
- **NOT for**: functional/E2E behavior testing (assert behavior, not pixels — this skill never replaces behavioral assertions); performance testing; purely local one-off pixel comparisons without a baseline pipeline (`pixel-perfect` covers that). If the user only wants "check this page looks right once", propose `pixel-perfect` first and use this skill when they need baselines + CI.

## Core Workflow
1. **Choose tool**: Playwright, Chromatic

2. **Setup baseline**: Capture initial screenshots
3. **Configure thresholds**: Define acceptable diff
4. **Integrate CI**: Automated testing
5. **Review changes**: Approve or reject
6. **Update baselines**: Accept intentional changes

## Playwright Visual Testing

### Installation

```bash
npm install -D @playwright/test
npx playwright install
```

### Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/visual',
  testMatch: '**/*.visual.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  // Snapshot configuration
  snapshotDir: './tests/visual/__snapshots__',
  snapshotPathTemplate: '{snapshotDir}/{testFilePath}/{arg}{ext}',
  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 100,
      maxDiffPixelRatio: 0.01,
      threshold: 0.2,
      animations: 'disabled',
    },
    toMatchSnapshot: {
      maxDiffPixelRatio: 0.01,
    },
  },
  use: {
    baseURL: 'http://<app-host>:<port>',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'Desktop Chrome',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
    },
    {
      name: 'Desktop Firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1280, height: 720 },
      },
    },
    {
      name: 'Mobile Safari',
      use: {
        ...devices['iPhone 13'],
      },
    },
    {
      name: 'Tablet',
      use: {
        viewport: { width: 768, height: 1024 },
      },
    },
  ],
  webServer: {
    command: 'npm run start',
    url: 'http://<app-host>:<port>',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
```

### Visual Test Examples

```typescript
// tests/visual/homepage.visual.ts
import { test, expect } from '@playwright/test';

test.describe('Homepage Visual Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');

    // Wait for fonts and images to load
    await page.waitForLoadState('networkidle');

    // Disable animations for consistent screenshots
    await page.addStyleTag({
      content: `
        *,
        *::before,
        *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
        }
      `,
    });
  });

  test('full page screenshot', async ({ page }) => {
    await expect(page).toHaveScreenshot('homepage-full.png', {
      fullPage: true,
    });
  });

  test('hero section', async ({ page }) => {
    const hero = page.locator('[data-testid="hero-section"]');
    await expect(hero).toHaveScreenshot('hero-section.png');
  });

  test('navigation bar', async ({ page }) => {
    const nav = page.locator('nav');
    await expect(nav).toHaveScreenshot('navigation.png');
  });

  test('footer', async ({ page }) => {
    const footer = page.locator('footer');
    await footer.scrollIntoViewIfNeeded();
    await expect(footer).toHaveScreenshot('footer.png');
  });
});
```

### Component Visual Tests

```typescript
// tests/visual/components.visual.ts
import { test, expect } from '@playwright/test';

test.describe('Button Component', () => {
  test('all variants', async ({ page }) => {
    await page.goto('/storybook/button');

    // Primary button
    const primary = page.locator('[data-testid="button-primary"]');
    await expect(primary).toHaveScreenshot('button-primary.png');

    // Secondary button
    const secondary = page.locator('[data-testid="button-secondary"]');
    await expect(secondary).toHaveScreenshot('button-secondary.png');

    // Hover state
    await primary.hover();
    await expect(primary).toHaveScreenshot('button-primary-hover.png');

    // Focus state
    await primary.focus();
    await expect(primary).toHaveScreenshot('button-primary-focus.png');

    // Disabled state
    const disabled = page.locator('[data-testid="button-disabled"]');
    await expect(disabled).toHaveScreenshot('button-disabled.png');
  });
});

test.describe('Form Components', () => {
  test('input states', async ({ page }) => {
    await page.goto('/storybook/input');

    const input = page.locator('[data-testid="input-default"]');

    // Default state
    await expect(input).toHaveScreenshot('input-default.png');

    // Focused state
    await input.focus();
    await expect(input).toHaveScreenshot('input-focused.png');

    // With value
    await input.fill('Test value');
    await expect(input).toHaveScreenshot('input-with-value.png');

    // Error state
    const errorInput = page.locator('[data-testid="input-error"]');
    await expect(errorInput).toHaveScreenshot('input-error.png');
  });
});
```

### Responsive Testing

```typescript
// tests/visual/responsive.visual.ts
import { test, expect, devices } from '@playwright/test';

const viewports = [
  { name: 'mobile', width: 375, height: 667 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 720 },
  { name: 'wide', width: 1920, height: 1080 },
];

for (const viewport of viewports) {
  test.describe(`${viewport.name} viewport`, () => {
    test.use({ viewport: { width: viewport.width, height: viewport.height } });

    test('homepage layout', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveScreenshot(`homepage-${viewport.name}.png`, {
        fullPage: true,
      });
    });

    test('navigation menu', async ({ page }) => {
      await page.goto('/');

      if (viewport.width < 768) {
        // Mobile: test hamburger menu
        const menuButton = page.locator('[data-testid="mobile-menu-button"]');
        await menuButton.click();
        await expect(page.locator('[data-testid="mobile-menu"]')).toHaveScreenshot(
          `mobile-menu-${viewport.name}.png`
        );
      } else {
        // Desktop: test full nav
        await expect(page.locator('nav')).toHaveScreenshot(
          `nav-${viewport.name}.png`
        );
      }
    });
  });
}
```

### Dark Mode Testing

```typescript
// tests/visual/dark-mode.visual.ts
import { test, expect } from '@playwright/test';

test.describe('Dark Mode', () => {
  test('homepage in dark mode', async ({ page }) => {
    await page.goto('/');
    // Enable dark mode via color scheme
    await page.emulateMedia({ colorScheme: 'dark' });
    await expect(page).toHaveScreenshot('homepage-dark.png', {
      fullPage: true,
    });
  });

  test('homepage in light mode', async ({ page }) => {
    await page.goto('/');
    await page.emulateMedia({ colorScheme: 'light' });
    await expect(page).toHaveScreenshot('homepage-light.png', {
      fullPage: true,
    });
  });

  test('theme toggle', async ({ page }) => {
    await page.goto('/');
    // Toggle theme via button
    const themeToggle = page.locator('[data-testid="theme-toggle"]');
    await themeToggle.click();
    // Wait for transition
    await page.waitForTimeout(300);
    await expect(page).toHaveScreenshot('homepage-toggled-theme.png');
  });
});
```

## Chromatic Integration

Full Chromatic setup (install, `.storybook/main.ts` config, CI workflow with `CHROMATIC_PROJECT_TOKEN`, multi-viewport/pseudo-state story parameters) is extracted to **`references/chromatic.md`** — read it when the user chooses Chromatic. Requires a Chromatic project token; without it the publish step exits non-zero with an auth error.

## CI Integration

```yaml
# .github/workflows/visual-tests.yml
name: Visual Regression Tests
on:
  pull_request:
    branches: [main]
jobs:
  visual-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - name: Install Playwright Browsers
        run: npx playwright install --with-deps chromium
      - name: Build application
        run: npm run build
      - name: Run visual tests
        run: npx playwright test --project="Desktop Chrome"
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: |
            playwright-report/
            test-results/
          retention-days: 30
      - name: Upload diff images
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: visual-diffs
          path: tests/visual/__snapshots__/*-diff.png
          retention-days: 7
```

### Update Baselines Script

```json
// package.json
{
  "scripts": {
    "test:visual": "playwright test --project='Desktop Chrome'",
    "test:visual:update": "playwright test --update-snapshots",
    "test:visual:ui": "playwright test --ui",
    "test:visual:report": "playwright show-report"
  }
}
```

## Best Practices

1. **Disable animations**: Consistent screenshots
2. **Wait for network**: Ensure content loaded
3. **Use stable selectors**: data-testid attributes
4. **Test multiple viewports**: Responsive coverage
5. **Set thresholds**: Allow minor pixel differences
6. **Review in CI**: Block merges on failures
7. **Organize snapshots**: Clear naming convention
8. **Update intentionally**: Review all baseline changes

## Minimal worked example

Precondition: npm project with `@playwright/test` installed (per Installation above), app served by the `webServer` command in the config.

Command (default values: all 4 projects in the config, 3 retries in CI, `maxDiffPixelRatio: 0.01`):

```bash
npx playwright test --project="Desktop Chrome"
```

Output excerpt, first run (no baselines yet — Playwright writes them and fails):

```
Error: A snapshot doesn't exist at tests/visual/__snapshots__/homepage-visual-ts-homepage-full-darwin.png, writing actual.
  1 failed
```

Second run after reviewing and committing the written baseline:

```
✓  homepage.visual.ts:16:5 › full page screenshot (1.2s)
  3 passed (4.1s)
```

A real regression shows a `*-diff.png` under `test-results/` highlighting changed pixels; review it before touching baselines.

## Failure exits (troubleshooting)

| Situation | Observable signal | Exit action |
|-----------|-------------------|-------------|
| Browsers not installed | `Executable doesn't exist ... run "npx playwright install"` (non-zero exit) | Run `npx playwright install --with-deps chromium`, then rerun. |
| No network / blocked CDN during browser download | `npx playwright install` fails with a download error | Set `PLAYWRIGHT_DOWNLOAD_HOST` to an accessible mirror and retry; if the machine is fully offline, stop and report "cannot install browsers" — do not ship a setup that was never run. |
| Baseline missing (first run on a new machine/OS) | `A snapshot doesn't exist at ...` | Verify the screenshot is actually correct, then run `npx playwright test --update-snapshots` once and commit the baselines. |
| App never comes up | `webServer` timeout after 120s ("Timed out waiting for...") | Confirm `npm run start` works standalone; fix the `webServer.url`/command in the config, not the tests. |
| Diffs on every run, unrelated to the change | Small pixel-count failures across many tests, especially after deploy | Check animations are disabled and `networkidle` was awaited (see Best Practices); platform font differences → generate baselines in the same environment as CI (Playwright Docker image). |
| Chromatic publish fails | non-zero exit with auth error | `CHROMATIC_PROJECT_TOKEN` missing/invalid — get the token from the Chromatic dashboard and add it to CI secrets (see `references/chromatic.md`). |

## FAQ (wrong way → right way)

| Wrong | Right |
|-------|-------|
| Running `--update-snapshots` to make a red build green without inspecting diffs | Review each `*-diff.png`; update baselines only for intentional visual changes |
| Generating baselines locally on macOS while CI runs Linux | Produce and accept baselines in the same platform as CI (Playwright Docker image), or diffs will fire on every run |
| Asserting exact pixel equality with no threshold | Set `maxDiffPixels` / `maxDiffPixelRatio` per config above; 0 tolerance is flaky across renders |
| Testing one viewport only | Cover at least mobile + desktop (see Responsive Testing); the config's 4 projects exist for this |
| Auto-running visual tests on every trivial UI edit unprompted | Run when the user asks for visual regression setup or a screenshot diff investigation; propose the setup first |

## Output Checklist

Every visual testing setup should include:

- [ ] Playwright/Chromatic configuration
- [ ] Baseline screenshots
- [ ] Multi-viewport testing
- [ ] Dark mode coverage
- [ ] Component state testing
- [ ] Animation disabling
- [ ] CI integration
- [ ] Diff threshold configuration
- [ ] Baseline update workflow
- [ ] Artifact storage

## 中文速览（Quick Guide）

- **做什么**：用 Playwright 或 Chromatic 搭截图对比与视觉回归流水线：基线生成、diff 检测、多视口/暗色模式覆盖与 CI 集成。
- **何时用**：用户要求视觉回归/截图测试/视觉 diff 或托管 Chromatic 基线时；免费本地对比优先 pixel-perfect。
- **核心步骤**：①选工具并安装配置 ②首跑生成基线并人工确认 ③跑 diff 排查变化原因 ④补多视口与暗色覆盖 ⑤接入 CI 并约定基线更新流程。
- **国内可达性**：`npx playwright install` 下载浏览器走境外 CDN，失败时设 `PLAYWRIGHT_DOWNLOAD_HOST` 指向可达镜像重试（正文 Failure Exits 已给该出口），完全离线则停手报告；Chromatic 为境外托管服务且需项目 token，不可用即退回纯 Playwright 本地对比。
