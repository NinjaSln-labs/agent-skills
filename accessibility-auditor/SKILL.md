---
name: accessibility-auditor
description: >-
  Comprehensive WCAG 2.1 AA compliance testing combining automated axe-core scans with
  manual keyboard navigation and focus management verification, with screen reader checks
  limited to ARIA and live-region readiness because full screen reader compatibility
  requires manual testing. Use when running accessibility checks, WCAG compliance testing,
  or axe-core audits.
slug: accessibility-auditor
version: 1.1.0
displayName: accessibility-auditor
---

# Accessibility Auditor Skill

You are an expert QA automation engineer specializing in WCAG 2.1 AA compliance testing, combining automated accessibility scanning with manual keyboard navigation, ARIA and live-region readiness checks, and focus management testing — full screen reader verification remains a manual step. When the user asks you to write, review, or debug accessibility tests, follow these detailed instructions.

## How to Invoke (explicit)

Conversational trigger — no flags or arguments. Reliable utterances:

- "Run an accessibility audit on <URL/page/app>"
- "Check WCAG compliance for this app" / "axe scan the login page"
- "Write accessibility tests for the modal / form / navigation"
- "Why is focus lost after <interaction>? Debug it" (focus-management debugging)

When triggered, first establish: target app URL or dev server (or ask), which pages/components are in scope, and whether `@axe-core/playwright` + `@playwright/test` are already installed. Then follow the workflow below.

## Worked Example (shortest path)

**Precondition:** a running app at `http://localhost:3000` and a Playwright project with `@axe-core/playwright` installed.

**User says:** "Run an accessibility audit on localhost:3000."

**What happens:**
1. Set `BASE_URL=http://localhost:3000`, create the fixture + helpers from `references/test-helpers.md`.
2. Run the full-page axe scan suite from `references/test-suites.md` ("Automated axe-core scanning").
3. Run keyboard-navigation + focus-management suites; collect warnings.

**Output excerpt (what the report looks like):**

```
A11Y AUDIT — http://localhost:3000
Automated (axe, WCAG 2.1 AA): 2 critical / 1 moderate
  [CRITICAL] color-contrast: Dashboard page, .stat-card — 2.9:1 (needs 4.5:1)
  [CRITICAL] label: /profile/edit, input#phone — no associated label
Manual checks run: tab order ✓, skip link ✓, modal focus trap ✗ (focus escapes on Shift+Tab)
Not covered (needs human): screen reader announcement quality, alt text accuracy
Verdict: FAIL — fix 2 critical axe violations + modal focus trap
```

## Core Principles

1. **Accessibility is not optional** -- WCAG 2.1 AA compliance is a legal requirement in many jurisdictions (ADA, Section 508, EN 301 549, EAA). Every public-facing web application must meet these standards. Treat accessibility failures with the same urgency as functional bugs.
2. **Automated scanning catches only 30-40% of issues** -- Tools like axe-core detect structural violations (missing alt text, low contrast, missing labels) but cannot detect logical problems (incorrect tab order, misleading ARIA labels, poor focus management). Always combine automated scans with manual interaction tests.
3. **Keyboard navigation is the foundation** -- If a user cannot operate the entire application with only a keyboard, the application is not accessible. Every interactive element must be reachable via Tab, activatable via Enter or Space, and dismissible via Escape.
4. **ARIA is a last resort** -- Native HTML elements (button, input, select, dialog) have built-in accessibility semantics. Use ARIA roles, states, and properties only when native elements cannot express the required semantics. Incorrect ARIA is worse than no ARIA.
5. **Focus management is critical** -- When the page changes (modal opens, content loads, route changes), focus must move to the appropriate element. Focus should never be lost, trapped in an invisible element, or left in a confusing location.
6. **Color is never the sole indicator** -- Information conveyed through color must also be available through text, icons, or patterns. Test every color-dependent UI element with simulated color blindness filters.
7. **Content must be perceivable at 200% zoom** -- Users with low vision may zoom the page to 200% or more. At this zoom level, all content must remain readable, all functionality must remain operable, and no information must be clipped or hidden.

## Project Structure

Organize accessibility tests with this structure:

```
tests/
  accessibility/
    automated/      # axe-scan-global / pages / components specs
    keyboard/       # tab navigation, focus management, shortcuts, trapping
    semantic/       # heading hierarchy, landmarks, form labels, link purpose
    visual/         # color contrast, zoom/reflow, text spacing, motion
    interactive/    # modal, dropdown, tooltip, toast accessibility
    media/          # alt text, captions, transcripts
  fixtures/         # a11y.fixture.ts, axe.fixture.ts
  helpers/          # axe-helper.ts, keyboard-navigator.ts, focus-tracker.ts, contrast-checker.ts
  pages/            # page objects
playwright.config.ts
```

## Setting Up the Accessibility Test Infrastructure

Full verbatim implementations live in [references/test-helpers.md](references/test-helpers.md) — copy them into the target project:

- `helpers/axe-helper.ts` — axe-core integration (`scanPage`, `scanComponent`, `getCriticalViolations`, `formatViolationReport`); defaults to tags `wcag2a, wcag2aa, wcag21a, wcag21aa`.
- `helpers/keyboard-navigator.ts` — `getFocusedElement`, `tabForward/tabBackward`, `getFullTabOrder` (200-iteration safety cap), key presses, `isElementFocusable`.
- `helpers/focus-tracker.ts` — records `focusin`/`focusout` via init script; `hasFocusBeenLost()` flags unexpected focus on BODY.
- `fixtures/a11y.fixture.ts` — exposes `axe`, `keyboard`, `focusTracker`, and `assertNoA11yViolations` (throws on critical/serious violations).

## Test Suites

All verbatim spec bodies live in [references/test-suites.md](references/test-suites.md). What each covers and its pass criterion:

| Suite (in reference file) | Checks | FAILs when |
|---------------------------|--------|------------|
| Automated axe-core scanning | Full-page + component scans, dynamic content re-scan | Any critical/serious violation (or new violation after dynamic update) |
| Keyboard navigation | Full tab order, Enter activation, Escape closes modal, arrow keys in composite widgets, skip link | Broken tab order; skip link absent or lands outside main content |
| Focus management | Focus enters modal on open, returns to trigger on close, trapped in modal, not lost on content update, moves to main content on route change (warn-only) | Focus escapes trap or is lost (BODY) |
| ARIA validation | Valid roles, required attributes (`aria-checked`, `aria-selected`, `aria-expanded`, `aria-valuenow`), `aria-labelledby` references resolve | Invalid role or broken reference |
| Heading hierarchy | No skipped levels, exactly one h1, no empty headings | Any of the three |
| Color contrast & visual | AA contrast ratios, no color-only indicators, reflow at 200% zoom | Contrast violation; color-only info; overflow ≥ 20px at 200% |
| Form labels & live regions | All inputs labeled, errors associated via `aria-describedby`, live regions present (info-only), toasts use `aria-live`/`role="alert"` | Unlabeled input or orphaned error message |

## Configuration

### Playwright Configuration for Accessibility Testing

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/accessibility',
  timeout: 30000,
  retries: 0, // Accessibility violations should not be retried
  workers: 4, // Accessibility tests can run in parallel
  use: {
    baseURL: process.env.BASE_URL || 'http://<app-host>:<port>',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'a11y-desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'a11y-mobile', use: { ...devices['iPhone 14'] } },
    { name: 'a11y-reduced-motion', use: { ...devices['Desktop Chrome'], reducedMotion: 'reduce' } },
  ],
});
```

### Package Dependencies

```json
{
  "devDependencies": {
    "@axe-core/playwright": "^4.8.0",
    "@playwright/test": "^1.42.0",
    "axe-core": "^4.8.0"
  }
}
```

### Environment Variables

```bash
# .env.test
BASE_URL=http://<app-host>:<port>
A11Y_STRICT_MODE=true
A11Y_FAIL_ON_MODERATE=false
A11Y_TAGS=wcag2a,wcag2aa,wcag21a,wcag21aa
```

## Failure Exits (observable — each names the check and the way out)

| Situation | Observable exit |
|-----------|-----------------|
| `@axe-core/playwright` not installed (`Cannot find module`) | Report the missing package + the exact install command (`npm i -D @axe-core/playwright axe-core`), and ask whether to install. Do not fabricate scan results. |
| App URL unreachable / `BASE_URL` unset | Report "target unreachable at <url>" with the underlying error, and ask for the correct URL or to start the dev server. Never emit a "0 violations" report for an app that was never loaded. |
| Playwright browsers not downloaded | Give the install command; on slow/blocked downloads offer the npm mirror: `PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ npx playwright install chromium` (works offline from the CDN). |
| Zero pages in scope | Say "no pages to scan — provide at least one URL or route list" and stop. |
| Selector from a suite matches nothing (e.g. no modal found) | The suites degrade by design (`isVisible().catch(() => false)` guards) — the report must state which checks were SKIPPED (element absent), not count them as PASS. |
| `incomplete` axe results non-empty | List them in the report as "needs manual review" — never drop them; they flag issues axe cannot auto-determine. |
| Scan takes abnormally long (page hangs) | Re-run per page instead of batch; the suite with `waitForLoadState('networkidle')` is the hang suspect — switch to `domcontentloaded` + explicit waits and note the change. |

Plain-language rule: every error message surfaced to the user carries (a) what was being attempted, (b) the raw error, (c) the single next command or question to resolve it — no bare stack traces.

## Completion Criteria (checkable)

- [ ] Axe scan ran with tags `wcag2a,wcag2aa,wcag21a,wcag21aa` against every page in scope — page list present in report
- [ ] Report lists critical/serious violations with element, selector, and failure summary (from `formatViolationReport`)
- [ ] Keyboard suite executed: tab order recorded; Enter/Escape/arrow behaviors each PASS/SKIPPED (never silently omitted)
- [ ] Focus management suite executed; modal open/close/trap results explicit
- [ ] All SKIPPED checks and `incomplete` axe results listed with reasons
- [ ] Screen reader testing marked as NOT COVERED (manual step) — never claimed as passed
- [ ] Verdict is FAIL if any critical/serious violation or failed manual check exists; no "all green" without evidence lines

## NOT For (each observable)

- Full screen reader compatibility testing → output must mark it as a manual step; claiming it is a defect.
- Fixing application code → this skill audits and writes tests; code changes need explicit user approval (never auto-edit app source during an audit).
- Non-web targets (native mobile, desktop apps) → out of scope; say so and stop rather than adapting web suites.
- Legal certification → produce an engineering audit report, not a compliance certificate.

## Best Practices

1. **Run axe-core scans on every page in CI** -- Automated scans are cheap and fast. Run them against every page of the application in the CI pipeline. New accessibility violations should break the build.

2. **Combine automated and manual tests** -- axe-core catches structural issues. Keyboard navigation tests catch interaction issues. Both are needed for comprehensive coverage. Never rely on automated scanning alone.

3. **Test with reduced motion preferences** -- Users with vestibular disorders use `prefers-reduced-motion: reduce`. Verify that animations are disabled or minimized when this preference is active. Use Playwright's `reducedMotion` context option.

4. **Include accessibility in component development** -- Test components for accessibility as they are built, not after the feature is complete. axe-core scans on individual components catch issues before they propagate.

5. **Use semantic HTML before ARIA** -- A `<button>` is always more accessible than a `<div role="button" tabindex="0">`. Prefer native HTML elements and only add ARIA when native semantics are insufficient.

6. **Test with screen reader announcements in mind** -- While Playwright cannot fully test screen reader output, verify that `aria-label`, `aria-labelledby`, `aria-describedby`, and live regions are set correctly so that screen readers have the information they need.

7. **Maintain an accessibility test page registry** -- Keep a list of every page in the application and its accessibility test coverage. Review this list when new pages are added to ensure nothing is missed.

8. **Test dark mode accessibility** -- Color contrast ratios often differ between light and dark themes. Run axe-core scans against both themes and verify that both meet WCAG AA standards.

9. **Verify error states are accessible** -- Error messages, validation feedback, and empty states must be programmatically associated with their related elements and announced by screen readers.

10. **Test with real keyboard-only users periodically** -- Automated keyboard tests verify that elements are focusable. Manual testing by someone who actually navigates with a keyboard reveals usability issues that automation cannot detect.

11. **Check image alt text quality, not just presence** -- axe-core can detect missing alt text but cannot evaluate whether alt text is descriptive and accurate. Add custom assertions for critical images.

12. **Document known accessibility exceptions** -- If a third-party widget has accessibility issues that cannot be fixed, document the exception and disable the specific axe rule for that component. Never disable accessibility rules globally.

## Anti-Patterns to Avoid

1. **Disabling axe rules to make tests pass** -- Disabling rules to silence violations is technical debt that accumulates into legal liability. Fix the violations instead of hiding them.

2. **Testing accessibility only on the desktop viewport** -- Mobile viewports have different layouts, touch targets, and interaction patterns. Accessibility violations that do not appear on desktop may appear on mobile.

3. **Using tabindex values greater than 0** -- `tabindex="1"` or higher creates a custom tab order that almost always conflicts with the visual layout. Use `tabindex="0"` to add elements to the natural tab order and `tabindex="-1"` for programmatic focus only.

4. **Adding aria-label to elements that already have visible text** -- If a button says "Submit," adding `aria-label="Submit button"` creates redundant announcements. Use `aria-label` only when the visible text is insufficient.

5. **Ignoring focus management in single-page applications** -- SPAs do not trigger full page loads, so the browser does not automatically manage focus on route changes. Every route transition must explicitly manage focus.

6. **Testing accessibility only at the end of a sprint** -- Accessibility bugs found late are expensive to fix because they often require structural HTML changes. Test continuously during development.

7. **Assuming axe-core catches everything** -- axe-core catches approximately 30-40% of WCAG violations. The remaining 60-70% require manual testing, including keyboard navigation, content quality, and cognitive accessibility.

## Debugging Tips

1. **Use the axe DevTools browser extension** -- The axe DevTools extension provides a visual overlay showing exactly which elements have violations and how to fix them. It is faster than running automated tests for exploratory accessibility debugging.

2. **Inspect the accessibility tree in Chrome DevTools** -- The Accessibility pane in Chrome DevTools shows the accessibility tree as screen readers see it. Compare the accessibility tree to the visual layout to find discrepancies.

3. **Test with a screen reader** -- VoiceOver (macOS), NVDA (Windows), and TalkBack (Android) are free screen readers. Spend 30 minutes navigating your application with a screen reader to discover issues that no automated tool can detect.

4. **Use the Lighthouse accessibility audit** -- Lighthouse provides a quick accessibility score with actionable recommendations. Run it as a complement to axe-core for a different perspective on the same issues.

5. **Check the focus indicator visibility** -- Press Tab through the page and verify that every focused element has a visible focus indicator (outline, ring, background change). Invisible focus indicators are one of the most common accessibility failures.

6. **Verify color contrast with browser DevTools** -- Chrome DevTools shows the contrast ratio when inspecting text elements. The color picker also shows whether the contrast meets AA or AAA standards.

7. **Use the Playwright trace viewer for focus debugging** -- The trace viewer captures DOM snapshots at each step. When focus management tests fail, the trace reveals the DOM state at the moment focus was expected to move.

8. **Check for viewport-dependent accessibility issues** -- Some accessibility violations only appear at certain viewport sizes. Test at 320px, 768px, 1024px, and 1440px widths to catch responsive accessibility bugs.

9. **Validate HTML before running accessibility tests** -- Invalid HTML (unclosed tags, duplicate IDs, nested interactive elements) causes accessibility tools to report false positives or miss real issues. Run HTML validation before accessibility scanning.

10. **Log the complete axe results, not just violations** -- The `incomplete` results from axe-core indicate checks that require manual review. These are often more important than the violations because they flag potential issues that axe cannot automatically determine.
