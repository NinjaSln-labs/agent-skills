---
name: pixel-perfect
description: >
  Visual regression testing — pixel-by-pixel screenshot comparison against a baseline.
  TRIGGER when: user mentions "pixel-perfect", "visual regression", "screenshot diff",
  "snapshot mismatch", "toHaveScreenshot", "UI looks broken after changes",
  "compare before/after screenshots", "visual QA", "catch visual bugs",
  "design implementation check", "tests failing with screenshot", or wants to verify
  that code changes didn't break the UI visually.
  DO NOT TRIGGER when: user wants functional/behavioral testing (use playwright-skill),
  just wants a single screenshot (use screenshots skill), or asks about accessibility.
metadata:
  category: technique
  triggers: pixel-perfect, visual regression, screenshot diff, visual QA, UI comparison, toHaveScreenshot, visual bug, design check, before after screenshot, snapshot mismatch, baseline
allowed-tools: Bash, Read, Write, Glob
---

# Pixel-Perfect Visual Regression Testing

Compare UI screenshots pixel-by-pixel against a baseline. Catch unintended visual changes. Built on `@playwright/test` — no third-party services.

> **Working directory:** All commands run from the project root — the directory containing `package.json`. Do not `cd` between steps.
>
> **Package manager:** This skill uses npm. If your project uses yarn or pnpm, adapt install and CI commands accordingly.

> **分工**：默认视觉回归工具（免费——pixel-by-pixel）。需 Chromatic/Percy 商业路线时用 visual-regression-tester。

## Step 1: Check State

Run all three commands, then use the table to choose your workflow.

```bash
ls playwright.config.ts 2>/dev/null && echo "CONFIG_EXISTS" || echo "CONFIG_MISSING"
find snapshots/ -name "*.png" 2>/dev/null | head -1 | grep -q . && echo "BASELINES_EXIST" || echo "BASELINES_MISSING"
curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000 2>/dev/null | grep -q "^2" && echo "SERVER_OK" || echo "NO_SERVER"
```

> If your dev server runs on a port other than 3000, adjust the URL in the curl command above.

| Config | Baselines | Server | → Do this |
|--------|-----------|--------|-----------|
| CONFIG_MISSING | any | any | **→ Workflow A** (Full Setup) |
| CONFIG_EXISTS | BASELINES_MISSING | SERVER_OK | **→ Workflow B** (Capture Baseline) |
| CONFIG_EXISTS | BASELINES_EXIST | SERVER_OK | Run `npx playwright test`. If all tests pass ✓, done. If tests fail → see **Step 2**. |
| CONFIG_EXISTS | BASELINES_EXIST | NO_SERVER | STOP. Tell the user: "Dev server is not running. Start it first, then re-check." |
| CONFIG_EXISTS | BASELINES_MISSING | NO_SERVER | STOP. Tell the user: "No baselines and no dev server. Start the server first." |

Do not guess the next step — use the table.

## Step 2: If Tests Fail

Only consult this section after running `npx playwright test` and seeing a failure.

```
What kind of failure?
│
├─ "screenshot doesn't match" / snapshot diff
│  │
│  │  STOP. Ask the user:
│  │  "Was this visual change intentional (design update) or unexpected (possible bug)?"
│  │  Wait for an explicit answer — do NOT infer from context.
│  │  If the answer is ambiguous, ask again: "Please answer 'intentional' or 'bug'."
│  │
│  ├─ "Intentional" → Workflow C: Update Baseline
│  └─ "Bug" / "Unexpected" → Workflow D: Debug Comparison
│
├─ Tests flaky (pass sometimes, fail sometimes)
│  └─ → Workflow E: Fix Flakiness with Fixture
│
└─ Config errors / tests won't run
   └─ Check Node.js version (v18+), re-run `npx playwright install chromium`
```

---

## Workflow A: Full Setup

**Precondition:** Step 1 returned `CONFIG_MISSING`.

**Exit condition:** `npx playwright test --list` prints test names without errors.

**Step 1.** Check for existing `package.json`:
```bash
ls package.json 2>/dev/null && echo "EXISTS" || echo "MISSING"
```
If MISSING: run `npm init -y` first. If EXISTS: skip — do not re-initialize.

**Step 2.** Install Playwright:
```bash
npm install -D @playwright/test
npx playwright install chromium
```
If this fails: check `node -v` — requires v18+.

**Step 3.** Ask the user: "What URL does your dev server run on? (e.g. http://localhost:3000)"
Wait for their answer. Save it — you will use it in Step 4 and in Workflow B.

**Step 4.** Write the config file. Use the Read tool to load the template:
Read file: `references/examples/playwright.config.ts`
Write it to: `./playwright.config.ts`
If the user's URL differs from `http://localhost:3000`, use the Edit tool to find the exact string `'http://localhost:3000'` inside `playwright.config.ts` and replace it with the user's URL.

**Step 5.** Write the test file:
Read file: `references/examples/visual.spec.ts`
Write it to: `./tests/visual.spec.ts`

**Step 6.** Verify setup is functional:
```bash
npx playwright test --list
```
If this errors or prints `0 tests`: show the output to the user and stop. Do not proceed to Workflow B.

**Optional:** If the project uses custom fonts, JS animations (GSAP, Framer Motion), or lazy-loaded images, also install the fixture now — see **Workflow E** Steps 1–2.

**Workflow A complete** → continue to **Workflow B**.

---

## Workflow B: Capture Baseline

**Precondition:** CONFIG_EXISTS + BASELINES_MISSING + SERVER_OK. (Or: just completed Workflow A.)

**Exit condition:** `find snapshots/ -name "*.png" | wc -l` prints a non-zero number and snapshots are committed to git.

**Step 1.** Verify the dev server responds. Use the `baseURL` from `playwright.config.ts` (default: `http://localhost:3000`). Replace the URL in the command if yours differs:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```
Expected: `200`. If not 200: STOP. Tell the user the server is not responding and ask them to start it.

**Step 2.** Check if Docker is available:
```bash
docker --version 2>/dev/null && echo "DOCKER_OK" || echo "NO_DOCKER"
```

If DOCKER_OK — capture inside Docker (matches Linux CI, avoids font rendering diffs):
```bash
docker run --rm --ipc=host -v "$(pwd):/work" -w /work \
  mcr.microsoft.com/playwright:v1.50.1-noble \
  npx playwright test --update-snapshots
```

If NO_DOCKER — ask the user:
> "Docker is not available. Baselines captured locally on macOS can cause false CI failures due to font rendering differences. Do you want to proceed locally (acceptable if you won't use CI), or install Docker first?"
Wait for their answer before proceeding. If they confirm local: run `npx playwright test --update-snapshots`.

**Step 3.** Verify snapshots were created:
```bash
find snapshots/ -name "*.png" | wc -l
```
If output is `0` or command errors: STOP. Show the user the test output and ask to debug.

**Step 4.** Commit baselines:
```bash
if ! git rev-parse --is-inside-work-tree 2>/dev/null; then
  echo "Not a git repository — skipping commit."
elif git check-ignore -q snapshots/ 2>/dev/null; then
  echo "⚠️  snapshots/ is listed in .gitignore — remove it so baselines can be committed."
else
  git add snapshots/
  if git diff --staged --quiet; then
    echo "Snapshots already committed — nothing to add."
  else
    git commit -m "chore: add visual baselines"
    echo "Done. Push to remote: git push"
  fi
fi
```

**Workflow B complete.** Baselines are now the source of truth.

---

## Workflow C: Update Baseline

**Precondition:** Tests failing with 'screenshot doesn't match' and the user confirmed the change is **intentional**.

Use when a design change is intentional and the current baseline is outdated.

**Before Step 1.** Ask the user:
> "What is the reason for updating these baselines? (e.g., 'updated button design', 'new header font')"
Wait for their answer. Save it. You will use it in Step 2. Do not proceed until you have a clear answer.

**Step 1.** Check if Docker is available:
```bash
docker --version 2>/dev/null && echo "DOCKER_OK" || echo "NO_DOCKER"
```

If DOCKER_OK — update snapshots inside Docker:
```bash
docker run --rm --ipc=host -v "$(pwd):/work" -w /work \
  mcr.microsoft.com/playwright:v1.50.1-noble \
  npx playwright test --update-snapshots
```
This updates all existing baselines AND creates new ones.

If NO_DOCKER — existing baselines need updating, so local font rendering on macOS may differ from Linux CI:
1. Install Docker (recommended) and rerun this step.
2. Or run `npx playwright test --update-snapshots` locally and accept that CI may need a re-run after push (CI captures its own Linux baselines).

Ask the user which they prefer before proceeding.

**Step 2.** Commit with the reason the user gave you:
```bash
git add snapshots/ && git commit -m "chore: update visual baselines — USER_REASON"
```
Replace `USER_REASON` with the exact answer from the user. Do not invent a reason. If the user's reason contains backticks, `$(`, or newlines, ask for a simpler version — those characters cause shell injection in the commit command.

> ⚠️ Never auto-update snapshots in CI. Use the [update-snapshots workflow](.github/workflows/update-snapshots.yml) for intentional updates — it requires a reason and commits with attribution.

---

## Workflow D: Debug Comparison

**Precondition:** Tests failing with 'screenshot doesn't match' and the user confirmed it is a **bug** (unexpected change).

**Step 1.** Run tests and capture output:
```bash
npx playwright test 2>&1 | tail -30
```

**Step 2.** Find diff images (CLI-friendly — no browser needed):
```bash
find playwright-report/ -name "*-diff.png" -o -name "*-actual.png" 2>/dev/null | head -20
find test-results/ -name "*.png" 2>/dev/null | head -20
```
Show the user the list of diff image paths. Ask them to open the files to see what changed.

**Step 3.** If the user has a browser available, they can run the HTML report themselves:
```
npx playwright show-report
```
Do NOT run `show-report` yourself — it starts a web server and blocks the terminal indefinitely.

---

## Workflow E: Fix Flakiness with Fixture

**Precondition:** Tests are flaky (pass sometimes, fail sometimes) — not a consistent snapshot mismatch.

For pages with custom fonts, JS animations (Framer Motion, GSAP), or lazy-loaded images.

**Step 1.** Copy fixture to your project using the Read and Write tools:
Read file: `references/fixtures/visual.ts`
Write it to: `./tests/fixtures/visual.ts`

**Step 2.** In your test file (e.g. `tests/visual.spec.ts`), find the import line:
```typescript
import { test, expect } from '@playwright/test';
```
Replace it with:
```typescript
import { test, expect, waitForPageReady } from './fixtures/visual';
```
(Adjust the relative path if your test file is in a different location.)

**Step 3.** In every test that calls `toHaveScreenshot()`, add these two lines immediately before the `toHaveScreenshot` call:
```typescript
await page.locator('TODO_REPLACE_WITH_KEY_SELECTOR').waitFor();  // key element confirming page is loaded (e.g. 'h1', '.hero', '[data-testid="loaded"]')
await waitForPageReady(page);              // fonts + images + GSAP freeze
```
Replace `TODO_REPLACE_WITH_KEY_SELECTOR` with the actual selector for the main content element on that page.

The fixture uses `addInitScript` (runs before any app JS) to:
- Mock `IntersectionObserver` (lazy loaders fire immediately)
- Set `window.__PLAYWRIGHT__ = true` (for Framer Motion / app-level animation disabling)

---

## Workflow F: GitHub Actions

**Precondition:** Workflow B is complete — baselines are committed and pushed to git.

**Exit condition:** Both workflow files exist at `.github/workflows/visual-tests.yml` and `.github/workflows/update-snapshots.yml`, and CI runs green on push.

**Step 1.** Read and write the workflow files:
Read file: `.github/workflows/visual-tests.yml`
Write it to: `./.github/workflows/visual-tests.yml`

Read file: `.github/workflows/update-snapshots.yml`
Write it to: `./.github/workflows/update-snapshots.yml`

**Step 2.** Configure `BASE_URL` for CI. Ask the user:
> "What URL should CI run visual tests against? (e.g. https://staging.example.com)"

Then add it as a repository secret in GitHub (**Settings → Secrets and variables → Actions → New repository secret**, name: `BASE_URL`). The workflows already read `BASE_URL` from secrets — no edits needed.

If the user has no staging URL yet (tests run against localhost only), skip this step. CI will fail at the network step until a server is available.

**Key requirements:**
- Baselines must be committed to git before running in CI
- `CI=true` is set automatically by GitHub Actions
- Both workflows use `--ipc=host` to prevent Chromium crashes in Docker
- `update-snapshots.yml` runs only on branches, never on tags (prevents corrupting release tags)
- ⚠️ Keep the Docker image version in sync with `@playwright/test` in `package.json`. To check: `node -e "console.log(require('./package-lock.json').packages['node_modules/@playwright/test'].version)"`

---

## Key Options

| Option | Default | Use |
|--------|---------|-----|
| `maxDiffPixelRatio` | `0.01` | % pixels allowed to differ (`0.01` = 1%). Set to `0` for zero tolerance |
| `threshold` | `0.05` | Per-pixel color sensitivity (0–1). Raise to `0.1` only for font anti-aliasing false positives |
| `reducedMotion` | `'reduce'` | Sets `prefers-reduced-motion` CSS media query. Remove if you want to test the default (animated) visual state |
| `mask` | `[]` | Locators to black out (prices, timestamps, live data) |
| `fullPage` | `false` | Capture entire scrollable page |
| `animations` | `'disabled'` | Default — CSS + Web Animations API stopped at screenshot time |

## Quick Commands

```bash
npx playwright test                             # compare vs baseline
npx playwright test --project=Desktop           # specific viewport
npx playwright test tests/visual.spec.ts        # specific file
npx playwright test --update-snapshots          # update changed baselines
npx playwright test --update-snapshots=missing  # only add new baselines
```
