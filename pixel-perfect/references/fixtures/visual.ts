import { test as base, expect, type Page } from '@playwright/test';

/**
 * Production-ready visual test fixture.
 *
 * Architecture: two-phase approach
 *   Phase 1 — addInitScript (runs BEFORE any page JS):
 *     - IntersectionObserver mock (lazy images load immediately)
 *     - window.__PLAYWRIGHT__ flag (for app-level animation disabling)
 *   Phase 2 — waitForPageReady() (call explicitly after page.goto()):
 *     - Double rAF — JS framework finishes initial render, layout stabilizes
 *     - Freeze GSAP timeline (if present) in final state
 *     - Wait for all images to decode
 *     - Wait for custom fonts (document.fonts.ready)
 *     - Final rAF — browser settles last paint after fonts and images
 *
 * Usage:
 *   import { test, expect, waitForPageReady } from '../fixtures/visual';
 *
 *   test('homepage', async ({ page }) => {
 *     await page.goto('/');
 *     await page.locator('h1').waitFor();   // wait for key element
 *     await waitForPageReady(page);         // stabilize before screenshot
 *     await expect(page).toHaveScreenshot('homepage.png', { fullPage: true });
 *   });
 *
 * Framer Motion (skipAnimations):
 *   The fixture sets window.__PLAYWRIGHT__ = true before page JS runs.
 *   In your app (e.g., layout.tsx or _app.tsx), add:
 *
 *   import { MotionGlobalConfig } from 'framer-motion'; // or 'motion/react'
 *   if (typeof window !== 'undefined' && (window as any).__PLAYWRIGHT__) {
 *     MotionGlobalConfig.skipAnimations = true;
 *   }
 *
 * ⚠️ IntersectionObserver mock trade-off:
 *   The mock makes all elements immediately "in-viewport" on first observe().
 *   This ensures lazy-loaded images appear in full-page screenshots.
 *   However, it means viewport-dependent UI (infinite scroll, sticky headers that
 *   hide when out of viewport, load-more triggers) will render in a state that
 *   never exists in production. If your tests include such components, consider
 *   removing the mock and using a scroll-based warm-up instead:
 *
 *     await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
 *     await page.evaluate(() => window.scrollTo(0, 0));
 */

/**
 * Stabilizes the page before taking a screenshot.
 * Call explicitly after page.goto() and after waiting for key content.
 * Works for both full-page navigations and SPA route changes.
 */
export async function waitForPageReady(page: Page): Promise<void> {
  // 1. Double rAF — let JS framework complete initial render and layout stabilize.
  //    Must run first: frameworks finish mounting, dynamic imports resolve,
  //    GSAP starts its animation loop. All subsequent steps depend on a settled DOM.
  await page.evaluate(
    () =>
      new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve()))
      )
  );

  // 2. Freeze GSAP timeline in final state (if GSAP is present on the page).
  //    Must run after initial rAF — GSAP may be loaded via dynamic import.
  //    lagSmoothing(0): prevents lag-compensation drift when calculating final state.
  //    progress(1, true): jump to end of timeline; suppressEvents=true skips callbacks.
  //    pause(): freeze the ticker — no further frame updates.
  //    The guard is best-effort: if GSAP loads after this point, animations stay live.
  //    For guaranteed animation freeze, use CSS injection in addInitScript instead:
  //      await page.addInitScript(() => {
  //        const s = document.createElement('style');
  //        s.textContent = '*, *::before, *::after { animation-duration: 0ms !important; transition-duration: 0ms !important; }';
  //        document.head.appendChild(s);
  //      })
  await page.evaluate(() => {
    const g = (window as any).gsap;
    if (g?.globalTimeline) {
      if (g.ticker?.lagSmoothing) g.ticker.lagSmoothing(0);
      g.globalTimeline.progress(1, true);
      g.globalTimeline.pause();
    }
  });

  // 3. Wait for all images to fully load.
  //    img.decode() is race-free: unlike img.onload assignment, it cannot miss
  //    an image that completed loading between the check and the handler assignment.
  //    img.complete is true for both loaded AND broken images; decode() on a broken
  //    image rejects (caught here), so broken images don't block the wait.
  await page.evaluate(() =>
    Promise.all(
      [...document.images].map((img) =>
        img.complete
          ? Promise.resolve()
          : img.decode().catch(() => {
              /* broken images (404, CORS) — don't block */
            })
      )
    )
  );

  // 4. Wait for all custom fonts to finish loading.
  //    Runs after GSAP and images — dynamic content (including JS-injected fonts)
  //    is now in the DOM, so all fonts that will ever be used are captured.
  //    .then(() => {}) discards the FontFaceSet return value — avoids serialization
  //    of a non-serializable object across the evaluate boundary.
  //    Note: page.waitForFunction(() => document.fonts.ready) is WRONG — Promise is
  //    always truthy, so waitForFunction resolves immediately without waiting.
  await page.evaluate(() => document.fonts.ready.then(() => {}));

  // 5. Final rAF — let the browser settle one last paint frame after fonts and images.
  await page.evaluate(
    () => new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
  );
}

export const test = base.extend({
  page: async ({ page }, use) => {
    // ── Phase 1: addInitScript — runs BEFORE any page JavaScript ──────────────
    // Registered in a single call to minimize browser round-trips.
    // Scripts re-apply automatically on every navigation (including SPA pushState).
    await page.addInitScript(() => {
      // Set window.__PLAYWRIGHT__ flag for app-level animation disabling.
      // Framer Motion, custom animation libs, etc. can check this flag.
      (window as any).__PLAYWRIGHT__ = true;

      // Mock IntersectionObserver so lazy loaders fire immediately.
      // Must be in addInitScript — after page JS runs, components already hold
      // references to the original IntersectionObserver class.
      //
      // queueMicrotask: fires after the current call stack unwinds but BEFORE
      // any macrotask (setTimeout). This ensures the callback runs after the
      // framework finishes registering all observers in the current tick, but
      // before any next-tick logic that checks intersection state. Using
      // setTimeout(0) instead would fire too late — after promises and microtasks
      // have already run, potentially after the app has already checked state.
      window.IntersectionObserver = class MockIntersectionObserver
        implements IntersectionObserver
      {
        readonly root: Element | Document | null = null;
        readonly rootMargin: string = '0px';
        readonly thresholds: ReadonlyArray<number> = [0];

        private readonly _callback: IntersectionObserverCallback;

        constructor(callback: IntersectionObserverCallback) {
          this._callback = callback;
        }

        observe(target: Element): void {
          queueMicrotask(() => {
            const rect = target.getBoundingClientRect();
            this._callback(
              [
                {
                  isIntersecting: true,
                  intersectionRatio: 1,
                  target,
                  boundingClientRect: rect,
                  intersectionRect: rect,
                  rootBounds: {
                    x: 0,
                    y: 0,
                    top: 0,
                    left: 0,
                    width: window.innerWidth,
                    height: window.innerHeight,
                    bottom: window.innerHeight,
                    right: window.innerWidth,
                    toJSON() {
                      return {
                        x: 0,
                        y: 0,
                        top: 0,
                        left: 0,
                        width: window.innerWidth,
                        height: window.innerHeight,
                        bottom: window.innerHeight,
                        right: window.innerWidth,
                      };
                    },
                  } as DOMRectReadOnly,
                  time: performance.now(),
                } as IntersectionObserverEntry,
              ],
              this as unknown as IntersectionObserver
            );
          });
        }

        unobserve(_target: Element): void {}
        disconnect(): void {}
        takeRecords(): IntersectionObserverEntry[] {
          return [];
        }
      };
    });

    await use(page);
  },
});

export { expect };
