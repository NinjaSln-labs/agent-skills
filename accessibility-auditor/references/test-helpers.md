# Reference: Test Helpers and Fixture

Verbatim helper implementations referenced from SKILL.md. Copy these into the target project as-is.

## helpers/axe-helper.ts — axe-core integration

```typescript
// helpers/axe-helper.ts
import { Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

export interface AxeScanResult {
  violations: AxeViolation[];
  passes: number;
  incomplete: number;
  inapplicable: number;
}

export interface AxeViolation {
  id: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  description: string;
  helpUrl: string;
  nodes: Array<{
    html: string;
    target: string[];
    failureSummary: string;
  }>;
}

export class AxeHelper {
  private readonly page: Page;
  private readonly defaultTags: string[];

  constructor(page: Page) {
    this.page = page;
    // Default to WCAG 2.1 AA
    this.defaultTags = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];
  }

  async scanPage(options: {
    tags?: string[];
    exclude?: string[];
    include?: string[];
    disableRules?: string[];
  } = {}): Promise<AxeScanResult> {
    let builder = new AxeBuilder({ page: this.page }).withTags(
      options.tags || this.defaultTags
    );

    if (options.exclude) {
      for (const selector of options.exclude) {
        builder = builder.exclude(selector);
      }
    }

    if (options.include) {
      for (const selector of options.include) {
        builder = builder.include(selector);
      }
    }

    if (options.disableRules) {
      builder = builder.disableRules(options.disableRules);
    }

    const results = await builder.analyze();

    return {
      violations: results.violations.map((v) => ({
        id: v.id,
        impact: v.impact as AxeViolation['impact'],
        description: v.description,
        helpUrl: v.helpUrl,
        nodes: v.nodes.map((n) => ({
          html: n.html,
          target: n.target as string[],
          failureSummary: n.failureSummary || '',
        })),
      })),
      passes: results.passes.length,
      incomplete: results.incomplete.length,
      inapplicable: results.inapplicable.length,
    };
  }

  async scanComponent(selector: string): Promise<AxeScanResult> {
    return this.scanPage({ include: [selector] });
  }

  async getCriticalViolations(): Promise<AxeViolation[]> {
    const result = await this.scanPage();
    return result.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious'
    );
  }

  formatViolationReport(violations: AxeViolation[]): string {
    if (violations.length === 0) return 'No accessibility violations found.';

    return violations
      .map((v) => {
        const nodeDetails = v.nodes
          .map((n) => `    Element: ${n.html}\n    Issue: ${n.failureSummary}`)
          .join('\n');
        return `[${v.impact.toUpperCase()}] ${v.id}: ${v.description}\n  Help: ${v.helpUrl}\n${nodeDetails}`;
      })
      .join('\n\n');
  }
}
```

## helpers/keyboard-navigator.ts — systematic keyboard navigation

```typescript
// helpers/keyboard-navigator.ts
import { Page, Locator } from '@playwright/test';

interface FocusedElement {
  tagName: string;
  role: string | null;
  text: string;
  ariaLabel: string | null;
  tabIndex: number;
  selector: string;
}

export class KeyboardNavigator {
  private readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async getFocusedElement(): Promise<FocusedElement> {
    return this.page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) {
        return {
          tagName: 'BODY',
          role: null,
          text: '',
          ariaLabel: null,
          tabIndex: -1,
          selector: 'body',
        };
      }

      const getSelector = (element: Element): string => {
        if (element.id) return `#${element.id}`;
        if (element.getAttribute('data-testid'))
          return `[data-testid="${element.getAttribute('data-testid')}"]`;
        const tag = element.tagName.toLowerCase();
        const role = element.getAttribute('role');
        if (role) return `${tag}[role="${role}"]`;
        return tag;
      };

      return {
        tagName: el.tagName,
        role: el.getAttribute('role'),
        text: (el as HTMLElement).innerText?.slice(0, 100) || '',
        ariaLabel: el.getAttribute('aria-label'),
        tabIndex: (el as HTMLElement).tabIndex,
        selector: getSelector(el),
      };
    });
  }

  async tabForward(count: number = 1): Promise<FocusedElement[]> {
    const elements: FocusedElement[] = [];
    for (let i = 0; i < count; i++) {
      await this.page.keyboard.press('Tab');
      elements.push(await this.getFocusedElement());
    }
    return elements;
  }

  async tabBackward(count: number = 1): Promise<FocusedElement[]> {
    const elements: FocusedElement[] = [];
    for (let i = 0; i < count; i++) {
      await this.page.keyboard.press('Shift+Tab');
      elements.push(await this.getFocusedElement());
    }
    return elements;
  }

  async getFullTabOrder(): Promise<FocusedElement[]> {
    // Focus the first element
    await this.page.keyboard.press('Tab');
    const firstElement = await this.getFocusedElement();
    const tabOrder: FocusedElement[] = [firstElement];

    const maxIterations = 200; // Safety limit
    for (let i = 0; i < maxIterations; i++) {
      await this.page.keyboard.press('Tab');
      const current = await this.getFocusedElement();

      // If we have cycled back to the first element or body, we are done
      if (
        current.selector === firstElement.selector ||
        current.tagName === 'BODY'
      ) {
        break;
      }

      tabOrder.push(current);
    }

    return tabOrder;
  }

  async pressEnter(): Promise<void> {
    await this.page.keyboard.press('Enter');
  }

  async pressSpace(): Promise<void> {
    await this.page.keyboard.press('Space');
  }

  async pressEscape(): Promise<void> {
    await this.page.keyboard.press('Escape');
  }

  async pressArrowDown(): Promise<void> {
    await this.page.keyboard.press('ArrowDown');
  }

  async pressArrowUp(): Promise<void> {
    await this.page.keyboard.press('ArrowUp');
  }

  async isElementFocusable(selector: string): Promise<boolean> {
    return this.page.evaluate((sel) => {
      const el = document.querySelector(sel);
      if (!el) return false;

      const tabIndex = (el as HTMLElement).tabIndex;
      const isNativelyFocusable = [
        'A',
        'BUTTON',
        'INPUT',
        'SELECT',
        'TEXTAREA',
      ].includes(el.tagName);
      const isDisabled = (el as HTMLInputElement).disabled;

      return (isNativelyFocusable || tabIndex >= 0) && !isDisabled;
    }, selector);
  }
}
```

## helpers/focus-tracker.ts — focus change tracking

```typescript
// helpers/focus-tracker.ts
import { Page } from '@playwright/test';

interface FocusEvent {
  type: 'focus' | 'blur';
  element: string;
  timestamp: number;
}

export class FocusTracker {
  private events: FocusEvent[] = [];
  private readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async startTracking(): Promise<void> {
    await this.page.addInitScript(() => {
      (window as any).__focusEvents = [];

      document.addEventListener(
        'focusin',
        (e) => {
          const target = e.target as HTMLElement;
          (window as any).__focusEvents.push({
            type: 'focus',
            element: target.tagName + (target.id ? `#${target.id}` : ''),
            timestamp: Date.now(),
          });
        },
        true
      );

      document.addEventListener(
        'focusout',
        (e) => {
          const target = e.target as HTMLElement;
          (window as any).__focusEvents.push({
            type: 'blur',
            element: target.tagName + (target.id ? `#${target.id}` : ''),
            timestamp: Date.now(),
          });
        },
        true
      );
    });
  }

  async getEvents(): Promise<FocusEvent[]> {
    return this.page.evaluate(() => (window as any).__focusEvents || []);
  }

  async hasFocusBeenLost(): Promise<boolean> {
    const events = await this.getEvents();
    // Check if focus ever went to BODY unexpectedly (indicates focus loss)
    return events.some(
      (e) => e.type === 'focus' && e.element === 'BODY'
    );
  }
}
```

## fixtures/a11y.fixture.ts — custom Playwright fixture

```typescript
import { test as base, expect } from '@playwright/test';
import { AxeHelper } from '../helpers/axe-helper';
import { KeyboardNavigator } from '../helpers/keyboard-navigator';
import { FocusTracker } from '../helpers/focus-tracker';

interface A11yFixtures {
  axe: AxeHelper;
  keyboard: KeyboardNavigator;
  focusTracker: FocusTracker;
  assertNoA11yViolations: (options?: {
    exclude?: string[];
    disableRules?: string[];
  }) => Promise<void>;
}

export const test = base.extend<A11yFixtures>({
  axe: async ({ page }, use) => {
    const helper = new AxeHelper(page);
    await use(helper);
  },

  keyboard: async ({ page }, use) => {
    const navigator = new KeyboardNavigator(page);
    await use(navigator);
  },

  focusTracker: async ({ page }, use) => {
    const tracker = new FocusTracker(page);
    await tracker.startTracking();
    await use(tracker);
  },

  assertNoA11yViolations: async ({ axe }, use) => {
    const assertFn = async (
      options: { exclude?: string[]; disableRules?: string[] } = {}
    ) => {
      const result = await axe.scanPage(options);
      const critical = result.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      );

      if (critical.length > 0) {
        throw new Error(
          `Found ${critical.length} critical/serious accessibility violations:\n` +
            axe.formatViolationReport(critical)
        );
      }
    };
    await use(assertFn);
  },
});

export { expect };
```
