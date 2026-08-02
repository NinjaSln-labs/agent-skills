# 🎯 pixel-perfect (Visual Regression)

> A Claude Code skill for **automated visual regression testing** using Playwright's built-in screenshot comparison engine.

![Claude Skill](https://img.shields.io/badge/Claude-Skill-6B48FF?logo=anthropic&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-45ba4b?logo=playwright&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

> ### Looking for a manual design audit?
>
> This skill does **automated screenshot comparison** (before/after code changes).
> If you need to **manually audit a live site against a brandbook / design system** — checking colors, typography, spacing, component consistency — use **[claude-pixel-perfect-agent](https://github.com/maxrihter/claude-pixel-perfect-agent)** instead.
>
> | | This skill (visual regression) | [claude-pixel-perfect-agent](https://github.com/maxrihter/claude-pixel-perfect-agent) |
> |---|---|---|
> | **Purpose** | Catch unintended visual changes after code updates | Verify implementation matches design specs |
> | **How** | Automated Playwright screenshot diffing | Manual CSS inspection via Chrome MCP |
> | **Input** | Baseline screenshots | Design system / brandbook |
> | **Output** | HTML diff report (pass/fail) | Structured bug report (Excel/Markdown) |
> | **When** | CI/CD pipeline, PR checks | Pre-launch design QA, redesign verification |

---

## What It Does

Enables Claude to set up, run, and interpret **pixel-perfect visual regression tests** — comparing UI screenshots against a baseline to catch unintended visual changes.

Built on `@playwright/test`'s native `toHaveScreenshot()` — no extra dependencies, no third-party services.

```
Baseline capture → Code change → Re-run → HTML diff report
     ✅                 🛠️           ▶️          🔍
```

---

## Triggers

Claude activates this skill when you say things like:

- _"Run pixel-perfect tests on this page"_
- _"Check for visual regressions"_
- _"Tests failing with snapshot mismatch"_
- _"Compare screenshots before and after"_
- _"Set up visual testing with Playwright"_

---

## Features

- ✅ Baseline management (capture, update, version in git)
- ✅ Multi-viewport testing (Desktop / Tablet / Mobile)
- ✅ HTML report with side-by-side diffs
- ✅ Dynamic content masking (prices, dates, animations)
- ✅ Configurable tolerance (`maxDiffPixelRatio`, `threshold`)
- ✅ Production fixture — handles fonts, CSS/JS animations, lazy images
- ✅ Cross-platform consistency via Docker (macOS ↔ Linux CI)
- ✅ GitHub Actions workflows (PR checks + manual snapshot update)
- ✅ `retries`, `maxFailures`, `updateSnapshots: 'missing'` configured

---

## Quick Start

```bash
# 1. Install
npm install -D @playwright/test
npx playwright install chromium

# 2. Capture baseline (in Docker — consistent with Linux CI)
docker run --rm -v $(pwd):/work -w /work \
  mcr.microsoft.com/playwright:v1.50.1-noble \
  npx playwright test --update-snapshots

# 3. Run comparison
npx playwright test

# 4. Open visual diff report
npx playwright show-report
```

---

## Skill Structure

```
pixel-perfect/
├── SKILL.md                             # Claude reads this — decision tree + workflows
├── README.md                            # You are here
├── LICENSE
├── .github/
│   └── workflows/
│       ├── visual-tests.yml             # Runs on every PR (with permissions + cache)
│       └── update-snapshots.yml         # Manual trigger — requires reason, commits with attribution
└── references/
    ├── setup/
    │   └── README.md                    # Install, package.json, tsconfig, config, SPA guide
    ├── baseline/
    │   └── README.md                    # Capture, Docker, cross-platform, masking
    ├── comparison/
    │   └── README.md                    # Running tests, reading diffs, fixing false positives
    ├── fixtures/
    │   └── visual.ts                    # Production fixture: addInitScript + waitForPageReady
    └── examples/
        ├── playwright.config.ts         # Ready-to-use config (retries, updateSnapshots, viewports)
        └── visual.spec.ts               # Example tests with locator.waitFor() + fixture usage
```

---

## Example Test

```typescript
import { test, expect, waitForPageReady } from '../fixtures/visual';

test('homepage', async ({ page }) => {
  await page.goto('/');
  await page.locator('h1').waitFor();

  // Stabilize: fonts + images + GSAP freeze (via addInitScript + evaluate)
  await waitForPageReady(page);

  await expect(page).toHaveScreenshot('homepage.png', {
    fullPage: true,
    maxDiffPixelRatio: 0.01,
    mask: [page.locator('.live-price')], // mask dynamic content
  });
});
```

---

## Viewport Defaults

| Viewport | Width | Height |
|----------|-------|--------|
| Desktop  | 1440  | 900    |
| Tablet   | 768   | 1024   |
| Mobile   | 375   | 812    |

---

## Reading the Diff Report

| Diff Pattern | Likely Cause | Fix |
|---|---|---|
| Scattered red pixels | Font anti-aliasing | Increase `threshold` to `0.3` |
| Solid red block | Element moved/changed | Review layout change |
| Red at bottom | Content height changed | Check new content added |
| Thin red line | Border/shadow changed | Verify design intent |
| Entire page differs | macOS vs Linux baseline | Regenerate baseline in Docker |

---

## Cross-Platform Consistency

macOS and Linux render fonts differently. Generate baselines in Docker to match CI:

```bash
docker run --rm -v $(pwd):/work -w /work \
  mcr.microsoft.com/playwright:v1.50.1-noble \
  npx playwright test --update-snapshots
```

---

## Installation into Claude Code

```bash
git clone https://github.com/maxrihter/claude-skill-visual-regression \
  ~/.claude/skills/pixel-perfect
```

Claude Code auto-discovers the skill on next session start.

---

## References

- [Playwright Visual Comparisons Docs](https://playwright.dev/docs/test-snapshots)
- [Playwright Docker images](https://playwright.dev/docs/docker)
- [pixelmatch](https://github.com/mapbox/pixelmatch) — the diff engine under the hood

---

## License

MIT © [maxrihter](https://github.com/maxrihter)
