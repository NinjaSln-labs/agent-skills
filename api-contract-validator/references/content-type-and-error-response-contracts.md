<!-- Extracted verbatim from SKILL.md section 'Content-Type and Error Response Contracts'. Edit content in this file; SKILL.md keeps only the pointer. -->

## Content-Type and Error Response Contracts

```typescript
// tests/contracts/openapi/content-type-validation.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Content-Type and Error Response Contracts', () => {
  test('JSON responses have correct Content-Type header', async ({ request }) => {
    const response = await request.get('/api/users');
    const contentType = response.headers()['content-type'];
    expect(contentType).toMatch(/application\/json/);
  });

  test('error responses use consistent structure', async ({ request }) => {
    const errorEndpoints = [
      { path: '/api/users/nonexistent', expectedStatus: 404 },
      { path: '/api/nonexistent-endpoint', expectedStatus: 404 },
    ];

    for (const { path, expectedStatus } of errorEndpoints) {
      const response = await request.get(path);
      expect(response.status()).toBe(expectedStatus);

      const body = await response.json();
      expect(body).toHaveProperty('error');
      expect(body.error).toHaveProperty('message');
      expect(typeof body.error.message).toBe('string');
      expect(body.error.message.length).toBeGreaterThan(0);

      // Error should not contain stack traces in production
      expect(body.error).not.toHaveProperty('stack');
      expect(JSON.stringify(body)).not.toContain('at Object');
      expect(JSON.stringify(body)).not.toContain('node_modules');
    }
  });

  test('400 validation errors include field-level details', async ({ request }) => {
    const response = await request.post('/api/users', {
      data: { email: 'not-an-email', name: '' },
    });

    if (response.status() === 400 || response.status() === 422) {
      const body = await response.json();
      expect(body.error).toHaveProperty('message');

      // Should include validation details
      if (body.error.details) {
        expect(Array.isArray(body.error.details)).toBe(true);
        for (const detail of body.error.details) {
          expect(detail).toHaveProperty('field');
          expect(detail).toHaveProperty('message');
        }
      }
    }
  });

  test('API returns 406 for unsupported Accept headers', async ({ request }) => {
    const response = await request.get('/api/users', {
      headers: { Accept: 'application/xml' },
    });

    // Either serve JSON anyway or return 406
    if (response.status() === 406) {
      // Correct behavior for unsupported content type
    } else {
      const contentType = response.headers()['content-type'];
      expect(contentType).toContain('application/json');
    }
  });

  test('rate limit responses include retry headers', async ({ request }) => {
    // Make many rapid requests to trigger rate limiting
    let rateLimitResponse = null;
    for (let i = 0; i < 100; i++) {
      const response = await request.get('/api/users');
      if (response.status() === 429) {
        rateLimitResponse = response;
        break;
      }
    }

    if (rateLimitResponse) {
      const retryAfter = rateLimitResponse.headers()['retry-after'];
      const rateLimitRemaining =
        rateLimitResponse.headers()['x-ratelimit-remaining'];
      const rateLimitLimit =
        rateLimitResponse.headers()['x-ratelimit-limit'];

      expect(retryAfter || rateLimitRemaining).toBeDefined();
      if (rateLimitLimit) {
        expect(parseInt(rateLimitLimit)).toBeGreaterThan(0);
      }
    }
  });
});
```
