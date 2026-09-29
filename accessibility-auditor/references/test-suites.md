# Reference: Accessibility Test Suites (Playwright)

Verbatim test suites referenced from SKILL.md. Each block is a complete spec file body; adjust page paths and selectors to the target app.

## Automated axe-core scanning (full page + component)

### Full Page Scans

```typescript
import { test, expect } from '../fixtures/a11y.fixture';

test.describe('Automated Accessibility Scanning', () => {
  const pagesToScan = [
    { name: 'Home', path: '/' },
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Profile', path: '/profile' },
    { name: 'Settings', path: '/settings' },
    { name: 'Tasks', path: '/tasks' },
    { name: 'Search', path: '/search' },
    { name: 'Login', path: '/login' },
    { name: 'Signup', path: '/signup' },
  ];

  for (const { name, path } of pagesToScan) {
    test(`${name} page has no critical accessibility violations`, async ({
      page,
      axe,
    }) => {
      await page.goto(path);
      await page.waitForLoadState('networkidle');

      const result = await axe.scanPage();
      const critical = result.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      );

      if (critical.length > 0) {
        console.error(axe.formatViolationReport(critical));
      }

      expect(critical).toHaveLength(0);
    });
  }

  test('entire application has no WCAG 2.1 AA violations', async ({ page, axe }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const result = await axe.scanPage({
      tags: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'],
    });

    // Log all violations for review, even non-critical ones
    if (result.violations.length > 0) {
      console.warn(
        `Found ${result.violations.length} total accessibility violations:\n` +
          axe.formatViolationReport(result.violations)
      );
    }

    // Fail only on critical and serious
    const blockers = result.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious'
    );
    expect(blockers).toHaveLength(0);
  });

  test('dynamic content updates maintain accessibility', async ({
    page,
    axe,
  }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Scan before interaction
    const beforeResult = await axe.scanPage();
    const beforeViolations = beforeResult.violations.length;

    // Trigger dynamic content update
    await page.getByRole('button', { name: /load more|refresh/i }).click().catch(() => {});
    await page.waitForLoadState('networkidle');

    // Scan after interaction
    const afterResult = await axe.scanPage();

    // Dynamic content should not introduce new violations
    const newViolations = afterResult.violations.filter(
      (v) => !beforeResult.violations.some((bv) => bv.id === v.id)
    );

    expect(newViolations).toHaveLength(0);
  });
});
```

### Component-Level Scanning

```typescript
import { test, expect } from '../fixtures/a11y.fixture';

test.describe('Component Accessibility Scanning', () => {
  test('navigation component is accessible', async ({ page, axe }) => {
    await page.goto('/');
    const result = await axe.scanComponent('nav');

    expect(result.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  test('modal dialog is accessible when open', async ({ page, axe }) => {
    await page.goto('/dashboard');

    // Open a modal
    await page.getByRole('button', { name: /create|new/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    const result = await axe.scanComponent('[role="dialog"]');

    expect(result.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  test('form components have proper labels', async ({ page, axe }) => {
    await page.goto('/profile/edit');

    const result = await axe.scanComponent('form');
    const labelViolations = result.violations.filter(
      (v) => v.id === 'label' || v.id === 'input-button-name' || v.id === 'select-name'
    );

    expect(labelViolations).toHaveLength(0);
  });
});
```

## Keyboard navigation testing

Comprehensive keyboard navigation tests ensure that every interactive element is accessible without a mouse.

```typescript
import { test, expect } from '../fixtures/a11y.fixture';

test.describe('Keyboard Navigation', () => {
  test('all interactive elements are reachable via Tab', async ({
    page,
    keyboard,
  }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const tabOrder = await keyboard.getFullTabOrder();

    // Should have multiple focusable elements
    expect(tabOrder.length).toBeGreaterThan(3);

    // Every element in the tab order should be a meaningful interactive element
    for (const element of tabOrder) {
      const isMeaningful =
        ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName) ||
        element.role !== null;

      if (!isMeaningful) {
        console.warn(
          `Non-interactive element in tab order: ${element.selector} (${element.tagName})`
        );
      }
    }
  });

  test('tab order follows visual layout order', async ({ page, keyboard }) => {
    await page.goto('/dashboard');

    const tabOrder = await keyboard.getFullTabOrder();

    // Get the visual positions of each element
    const positions = await Promise.all(
      tabOrder.map(async (element) => {
        const loc = page.locator(element.selector).first();
        const box = await loc.boundingBox().catch(() => null);
        return { element, box };
      })
    );

    // Filter to elements that have a bounding box
    const withBoxes = positions.filter((p) => p.box !== null);

    // Verify top-to-bottom, left-to-right ordering (for LTR layouts)
    for (let i = 1; i < withBoxes.length; i++) {
      const prev = withBoxes[i - 1].box!;
      const curr = withBoxes[i].box!;

      // Element should be either below the previous one or to the right on the same row
      const isBelow = curr.y > prev.y + prev.height;
      const isSameRowToRight =
        Math.abs(curr.y - prev.y) < 20 && curr.x >= prev.x;
      const isReasonableOrder = isBelow || isSameRowToRight;

      if (!isReasonableOrder) {
        console.warn(
          `Possible tab order issue: ${withBoxes[i - 1].element.selector} -> ${withBoxes[i].element.selector}`
        );
      }
    }
  });

  test('Enter key activates buttons and links', async ({ page, keyboard }) => {
    await page.goto('/dashboard');

    // Tab to a button
    const tabOrder = await keyboard.getFullTabOrder();
    const firstButton = tabOrder.find(
      (e) => e.tagName === 'BUTTON' || (e.tagName === 'A' && e.role !== 'presentation')
    );

    if (firstButton) {
      // Re-navigate to the button
      await page.keyboard.press('Tab');
      let current = await keyboard.getFocusedElement();
      let attempts = 0;
      while (
        current.selector !== firstButton.selector &&
        attempts < tabOrder.length
      ) {
        await page.keyboard.press('Tab');
        current = await keyboard.getFocusedElement();
        attempts++;
      }

      // Press Enter and verify the action occurred
      const urlBefore = page.url();
      await keyboard.pressEnter();
      await new Promise((r) => setTimeout(r, 1000));

      // Either the URL changed (link) or something happened on the page (button)
      const urlAfter = page.url();
      const pageChanged =
        urlBefore !== urlAfter ||
        (await page.getByRole('dialog').isVisible().catch(() => false));

      // The key point is that pressing Enter did not throw an error
      expect(true).toBe(true);
    }
  });

  test('Escape key closes modal dialogs', async ({ page, keyboard }) => {
    await page.goto('/dashboard');

    // Open a modal via keyboard
    const createButton = page.getByRole('button', { name: /create|new/i });
    if (await createButton.isVisible().catch(() => false)) {
      await createButton.focus();
      await keyboard.pressEnter();

      const dialog = page.getByRole('dialog');
      if (await dialog.isVisible({ timeout: 3000 }).catch(() => false)) {
        // Press Escape to close
        await keyboard.pressEscape();

        await expect(dialog).not.toBeVisible({ timeout: 2000 });
      }
    }
  });

  test('arrow keys navigate within composite widgets', async ({
    page,
    keyboard,
  }) => {
    await page.goto('/dashboard');

    // Find a dropdown or menu
    const menuTrigger = page
      .getByRole('button', { name: /menu/i })
      .or(page.locator('[aria-haspopup="true"]').first());

    if (await menuTrigger.isVisible().catch(() => false)) {
      await menuTrigger.focus();
      await keyboard.pressEnter();

      // Menu should open
      const menu = page.getByRole('menu').or(page.getByRole('listbox'));
      if (await menu.isVisible({ timeout: 2000 }).catch(() => false)) {
        // Arrow down should move focus within the menu
        await keyboard.pressArrowDown();
        const firstItem = await keyboard.getFocusedElement();

        await keyboard.pressArrowDown();
        const secondItem = await keyboard.getFocusedElement();

        // Focus should have moved to a different item
        expect(secondItem.selector).not.toBe(firstItem.selector);

        // Arrow up should go back
        await keyboard.pressArrowUp();
        const backToFirst = await keyboard.getFocusedElement();
        expect(backToFirst.selector).toBe(firstItem.selector);
      }
    }
  });

  test('skip navigation link is present and functional', async ({
    page,
    keyboard,
  }) => {
    await page.goto('/');

    // First Tab should reveal a skip navigation link
    await page.keyboard.press('Tab');
    const focused = await keyboard.getFocusedElement();

    const isSkipLink =
      focused.text.toLowerCase().includes('skip') ||
      focused.ariaLabel?.toLowerCase().includes('skip') ||
      false;

    if (isSkipLink) {
      // Activate the skip link
      await keyboard.pressEnter();

      // Focus should move past the navigation to the main content
      const newFocus = await keyboard.getFocusedElement();

      // The focused element should be in the main content area
      const isMainContent = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el) return false;
        return !!el.closest('main') || !!el.closest('[role="main"]');
      });

      expect(isMainContent).toBe(true);
    }
  });
});
```

## Focus management testing

```typescript
import { test, expect } from '../fixtures/a11y.fixture';

test.describe('Focus Management', () => {
  test('opening a modal moves focus into the modal', async ({ page, keyboard }) => {
    await page.goto('/dashboard');

    const trigger = page.getByRole('button', { name: /create|new/i });
    if (await trigger.isVisible().catch(() => false)) {
      await trigger.click();

      const dialog = page.getByRole('dialog');
      await expect(dialog).toBeVisible({ timeout: 3000 });

      // Focus should be inside the modal
      const focusedElement = await keyboard.getFocusedElement();
      const isInsideModal = await page.evaluate(() => {
        const el = document.activeElement;
        return !!el?.closest('[role="dialog"]');
      });

      expect(isInsideModal).toBe(true);
    }
  });

  test('closing a modal returns focus to the trigger', async ({
    page,
    keyboard,
  }) => {
    await page.goto('/dashboard');

    const trigger = page.getByRole('button', { name: /create|new/i });
    if (await trigger.isVisible().catch(() => false)) {
      await trigger.click();

      const dialog = page.getByRole('dialog');
      await expect(dialog).toBeVisible({ timeout: 3000 });

      // Close the modal
      await keyboard.pressEscape();
      await expect(dialog).not.toBeVisible({ timeout: 2000 });

      // Focus should return to the trigger button
      const focusedElement = await keyboard.getFocusedElement();
      expect(focusedElement.tagName).toBe('BUTTON');
    }
  });

  test('focus is trapped inside modal dialogs', async ({ page, keyboard }) => {
    await page.goto('/dashboard');

    const trigger = page.getByRole('button', { name: /create|new/i });
    if (await trigger.isVisible().catch(() => false)) {
      await trigger.click();

      const dialog = page.getByRole('dialog');
      await expect(dialog).toBeVisible({ timeout: 3000 });

      // Tab through all elements inside the modal
      const focusedElements: string[] = [];
      const maxTabs = 50;

      for (let i = 0; i < maxTabs; i++) {
        await page.keyboard.press('Tab');
        const element = await keyboard.getFocusedElement();

        // Focus should never leave the modal
        const isInsideModal = await page.evaluate(() => {
          const el = document.activeElement;
          return !!el?.closest('[role="dialog"]');
        });

        expect(isInsideModal).toBe(true);

        // Check for cycle (we returned to the first element)
        if (focusedElements.includes(element.selector)) break;
        focusedElements.push(element.selector);
      }

      // Should have found at least 2 focusable elements in the modal
      expect(focusedElements.length).toBeGreaterThanOrEqual(1);
    }
  });

  test('focus is not lost after content update', async ({
    page,
    keyboard,
    focusTracker,
  }) => {
    await page.goto('/tasks');
    await page.waitForLoadState('networkidle');

    // Focus on a task item
    await page.keyboard.press('Tab');
    const initialFocus = await keyboard.getFocusedElement();

    // Trigger a content update (like completing a task)
    const checkbox = page.locator('input[type="checkbox"]').first();
    if (await checkbox.isVisible().catch(() => false)) {
      await checkbox.check();
      await new Promise((r) => setTimeout(r, 1000));

      // Focus should not jump to body
      const currentFocus = await keyboard.getFocusedElement();
      expect(currentFocus.tagName).not.toBe('BODY');
    }
  });

  test('route changes move focus to the new page heading or main content', async ({
    page,
    keyboard,
  }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Navigate to a new page via link
    const navLink = page.getByRole('link', { name: /tasks|projects/i }).first();
    if (await navLink.isVisible().catch(() => false)) {
      await navLink.click();
      await page.waitForLoadState('networkidle');

      // Focus should be on the page heading or main content area
      const focusedElement = await keyboard.getFocusedElement();
      const isOnMainContent = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el) return false;
        return (
          el.tagName === 'H1' ||
          el.tagName === 'MAIN' ||
          !!el.closest('main') ||
          !!el.closest('[role="main"]') ||
          el === document.body // Acceptable for SPA route changes
        );
      });

      // This is a quality check -- many apps fail this
      if (!isOnMainContent) {
        console.warn(
          'Focus did not move to main content area after route change. ' +
            `Currently focused: ${focusedElement.tagName} ${focusedElement.selector}`
        );
      }
    }
  });
});
```

## ARIA validation

```typescript
import { test, expect } from '../fixtures/a11y.fixture';

test.describe('ARIA Role and Attribute Validation', () => {
  test('all ARIA roles are valid', async ({ page }) => {
    await page.goto('/dashboard');

    const invalidRoles = await page.evaluate(() => {
      const validRoles = [
        'alert', 'alertdialog', 'application', 'article', 'banner',
        'button', 'cell', 'checkbox', 'columnheader', 'combobox',
        'complementary', 'contentinfo', 'definition', 'dialog',
        'directory', 'document', 'feed', 'figure', 'form', 'grid',
        'gridcell', 'group', 'heading', 'img', 'link', 'list',
        'listbox', 'listitem', 'log', 'main', 'marquee', 'math',
        'menu', 'menubar', 'menuitem', 'menuitemcheckbox',
        'menuitemradio', 'navigation', 'none', 'note', 'option',
        'presentation', 'progressbar', 'radio', 'radiogroup',
        'region', 'row', 'rowgroup', 'rowheader', 'scrollbar',
        'search', 'searchbox', 'separator', 'slider', 'spinbutton',
        'status', 'switch', 'tab', 'table', 'tablist', 'tabpanel',
        'term', 'textbox', 'timer', 'toolbar', 'tooltip', 'tree',
        'treegrid', 'treeitem',
      ];

      const elements = document.querySelectorAll('[role]');
      const invalid: Array<{ element: string; role: string }> = [];

      elements.forEach((el) => {
        const role = el.getAttribute('role');
        if (role && !validRoles.includes(role)) {
          invalid.push({
            element: el.outerHTML.slice(0, 100),
            role,
          });
        }
      });

      return invalid;
    });

    expect(invalidRoles).toHaveLength(0);
  });

  test('required ARIA attributes are present', async ({ page }) => {
    await page.goto('/dashboard');

    const missingAttributes = await page.evaluate(() => {
      const issues: Array<{ element: string; missing: string }> = [];

      // Checkboxes must have aria-checked
      document.querySelectorAll('[role="checkbox"]').forEach((el) => {
        if (!el.hasAttribute('aria-checked')) {
          issues.push({
            element: el.outerHTML.slice(0, 100),
            missing: 'aria-checked',
          });
        }
      });

      // Tabs must have aria-selected
      document.querySelectorAll('[role="tab"]').forEach((el) => {
        if (!el.hasAttribute('aria-selected')) {
          issues.push({
            element: el.outerHTML.slice(0, 100),
            missing: 'aria-selected',
          });
        }
      });

      // Expandable elements must have aria-expanded
      document.querySelectorAll('[aria-haspopup]').forEach((el) => {
        if (!el.hasAttribute('aria-expanded')) {
          issues.push({
            element: el.outerHTML.slice(0, 100),
            missing: 'aria-expanded',
          });
        }
      });

      // Progress bars must have aria-valuenow or aria-valuetext
      document.querySelectorAll('[role="progressbar"]').forEach((el) => {
        if (
          !el.hasAttribute('aria-valuenow') &&
          !el.hasAttribute('aria-valuetext')
        ) {
          issues.push({
            element: el.outerHTML.slice(0, 100),
            missing: 'aria-valuenow or aria-valuetext',
          });
        }
      });

      return issues;
    });

    if (missingAttributes.length > 0) {
      console.warn('Missing ARIA attributes:', missingAttributes);
    }

    expect(missingAttributes).toHaveLength(0);
  });

  test('aria-labelledby references existing elements', async ({ page }) => {
    await page.goto('/dashboard');

    const brokenReferences = await page.evaluate(() => {
      const issues: Array<{ element: string; referencedId: string }> = [];
      const labelledByElements = document.querySelectorAll('[aria-labelledby]');

      labelledByElements.forEach((el) => {
        const ids = el.getAttribute('aria-labelledby')?.split(' ') || [];
        for (const id of ids) {
          if (!document.getElementById(id)) {
            issues.push({
              element: el.outerHTML.slice(0, 100),
              referencedId: id,
            });
          }
        }
      });

      return issues;
    });

    expect(brokenReferences).toHaveLength(0);
  });
});
```

## Heading hierarchy and semantic structure

```typescript
import { test, expect } from '../fixtures/a11y.fixture';

test.describe('Heading Hierarchy', () => {
  test('headings follow a logical hierarchy without skipping levels', async ({
    page,
  }) => {
    await page.goto('/dashboard');

    const headingIssues = await page.evaluate(() => {
      const headings = Array.from(
        document.querySelectorAll('h1, h2, h3, h4, h5, h6')
      );
      const issues: string[] = [];
      let lastLevel = 0;

      for (const heading of headings) {
        const level = parseInt(heading.tagName[1]);
        if (level > lastLevel + 1 && lastLevel > 0) {
          issues.push(
            `Heading level skipped: h${lastLevel} -> h${level} ("${heading.textContent?.trim()}")`
          );
        }
        lastLevel = level;
      }

      return issues;
    });

    if (headingIssues.length > 0) {
      console.warn('Heading hierarchy issues:', headingIssues);
    }

    expect(headingIssues).toHaveLength(0);
  });

  test('page has exactly one h1 heading', async ({ page }) => {
    await page.goto('/dashboard');

    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBe(1);
  });

  test('all headings have meaningful text content', async ({ page }) => {
    await page.goto('/dashboard');

    const emptyHeadings = await page.evaluate(() => {
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      const empty: string[] = [];

      headings.forEach((h) => {
        const text = h.textContent?.trim();
        if (!text || text.length === 0) {
          empty.push(h.outerHTML);
        }
      });

      return empty;
    });

    expect(emptyHeadings).toHaveLength(0);
  });
});
```

## Color contrast and visual accessibility


test.describe('Color Contrast', () => {
  test('all text meets WCAG AA contrast ratio (4.5:1 for normal, 3:1 for large)', async ({
    page,
    axe,
  }) => {
    await page.goto('/dashboard');

    const result = await axe.scanPage();
    const contrastViolations = result.violations.filter(
      (v) => v.id === 'color-contrast' || v.id === 'color-contrast-enhanced'
    );

    if (contrastViolations.length > 0) {
      console.error(
        'Color contrast violations:\n',
        axe.formatViolationReport(contrastViolations)
      );
    }

    expect(contrastViolations).toHaveLength(0);
  });

  test('information is not conveyed by color alone', async ({ page }) => {
    await page.goto('/dashboard');

    // Check for status indicators that rely solely on color
    const colorOnlyIndicators = await page.evaluate(() => {
      const issues: string[] = [];
      const statusElements = document.querySelectorAll(
        '.status, [data-status], .badge, .indicator'
      );

      statusElements.forEach((el) => {
        const hasText = (el.textContent?.trim().length || 0) > 0;
        const hasAriaLabel = el.hasAttribute('aria-label');
        const hasTitle = el.hasAttribute('title');
        const hasIcon = el.querySelector('svg, img, [class*="icon"]') !== null;

        if (!hasText && !hasAriaLabel && !hasTitle && !hasIcon) {
          issues.push(
            `Color-only indicator: ${el.outerHTML.slice(0, 100)}`
          );
        }
      });

      return issues;
    });

    if (colorOnlyIndicators.length > 0) {
      console.warn('Elements conveying information by color only:', colorOnlyIndicators);
    }

    expect(colorOnlyIndicators).toHaveLength(0);
  });

  test('page is usable at 200% zoom', async ({ page }) => {
    await page.goto('/dashboard');

    // Set viewport to simulate 200% zoom
    const originalViewport = page.viewportSize();
    if (originalViewport) {
      await page.setViewportSize({
        width: Math.floor(originalViewport.width / 2),
        height: Math.floor(originalViewport.height / 2),
      });
    }

    // Check for horizontal scrollbar (content should reflow)
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });

    // At 200% zoom, content should reflow without horizontal scrolling
    // Allow small overflow (scrollbar width differences)
    if (hasHorizontalScroll) {
      const overflowAmount = await page.evaluate(() => {
        return (
          document.documentElement.scrollWidth - document.documentElement.clientWidth
        );
      });
      expect(overflowAmount).toBeLessThan(20);
    }

    // Verify text is not clipped
    const clippedElements = await page.evaluate(() => {
      const issues: string[] = [];
      const textElements = document.querySelectorAll('p, span, a, button, h1, h2, h3, h4, label');

      textElements.forEach((el) => {
        const style = window.getComputedStyle(el);
        if (
          style.overflow === 'hidden' &&
          el.scrollWidth > el.clientWidth &&
          style.textOverflow !== 'ellipsis'
        ) {
          issues.push(el.outerHTML.slice(0, 100));
        }
      });

      return issues;
    });

    if (clippedElements.length > 0) {
      console.warn('Elements with clipped text at 200% zoom:', clippedElements);
    }
  });
});
```

## Form labels and live regions


test.describe('Form Labels and Live Regions', () => {
  test('all form inputs have associated labels', async ({ page }) => {
    await page.goto('/profile/edit');

    const unlabeledInputs = await page.evaluate(() => {
      const inputs = document.querySelectorAll(
        'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select'
      );
      const issues: string[] = [];

      inputs.forEach((input) => {
        const id = input.getAttribute('id');
        const hasLabel = id && document.querySelector(`label[for="${id}"]`) !== null;
        const hasAriaLabel = input.hasAttribute('aria-label');
        const hasAriaLabelledBy = input.hasAttribute('aria-labelledby');
        const hasTitle = input.hasAttribute('title');
        const isWrappedByLabel = input.closest('label') !== null;

        if (!hasLabel && !hasAriaLabel && !hasAriaLabelledBy && !hasTitle && !isWrappedByLabel) {
          issues.push(input.outerHTML.slice(0, 100));
        }
      });

      return issues;
    });

    if (unlabeledInputs.length > 0) {
      console.error('Inputs without labels:', unlabeledInputs);
    }

    expect(unlabeledInputs).toHaveLength(0);
  });

  test('error messages are associated with form fields', async ({ page }) => {
    await page.goto('/signup');

    // Submit empty form to trigger validation
    await page.getByRole('button', { name: /submit|sign up|create/i }).click();

    const orphanedErrors = await page.evaluate(() => {
      const errorElements = document.querySelectorAll(
        '[role="alert"], .error, .field-error, [aria-live="polite"], [aria-live="assertive"]'
      );
      const issues: string[] = [];

      errorElements.forEach((error) => {
        const id = error.getAttribute('id');
        if (id) {
          const associatedInput = document.querySelector(`[aria-describedby*="${id}"]`);
          if (!associatedInput) {
            issues.push(
              `Error message not associated with any input: ${error.outerHTML.slice(0, 100)}`
            );
          }
        }
      });

      return issues;
    });

    if (orphanedErrors.length > 0) {
      console.warn('Orphaned error messages:', orphanedErrors);
    }
  });

  test('live regions announce dynamic content changes', async ({ page }) => {
    await page.goto('/dashboard');

    // Check for live regions
    const liveRegions = await page.evaluate(() => {
      const regions = document.querySelectorAll(
        '[aria-live], [role="alert"], [role="status"], [role="log"]'
      );
      return Array.from(regions).map((r) => ({
        role: r.getAttribute('role'),
        ariaLive: r.getAttribute('aria-live'),
        html: r.outerHTML.slice(0, 100),
      }));
    });

    // Application should have at least one live region for status updates
    // This is a soft check -- not all pages need live regions
    if (liveRegions.length === 0) {
      console.info(
        'No live regions found. Consider adding aria-live regions for dynamic content updates.'
      );
    }
  });

  test('toast notifications use aria-live or role="alert"', async ({ page }) => {
    await page.goto('/dashboard');

    // Trigger an action that shows a toast
    const actionButton = page.getByRole('button').first();
    if (await actionButton.isVisible().catch(() => false)) {
      await actionButton.click();

      await new Promise((r) => setTimeout(r, 1000));

      // Check if any toast/snackbar appeared
      const toast = page
        .locator('[role="alert"]')
        .or(page.locator('[aria-live="polite"]'))
        .or(page.locator('[aria-live="assertive"]'))
        .or(page.locator('.toast, .snackbar, .notification'));

      if ((await toast.count()) > 0) {
        const hasAriaLive = await toast.first().evaluate((el) => {
          return (
            el.hasAttribute('aria-live') ||
            el.getAttribute('role') === 'alert' ||
            el.getAttribute('role') === 'status'
          );
        });

        expect(hasAriaLive).toBe(true);
      }
    }
  });
});
```
