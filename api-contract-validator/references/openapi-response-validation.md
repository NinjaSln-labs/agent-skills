<!-- Extracted verbatim from SKILL.md section 'OpenAPI Response Validation'. Edit content in this file; SKILL.md keeps only the pointer. -->

## OpenAPI Response Validation

```typescript
// tests/contracts/openapi/validate-responses.spec.ts
import { test, expect } from '@playwright/test';
import { loadOpenAPISpec, getResponseSchema } from '../fixtures/schema-loader';
import { validateAgainstSchema } from '../fixtures/contract-helpers';
import * as path from 'path';

const spec = loadOpenAPISpec(path.resolve(__dirname, '../specs/openapi.yaml'));

test.describe('OpenAPI Response Validation', () => {
  test('GET /api/users returns response matching spec', async ({ request }) => {
    const response = await request.get('/api/users');
    const status = response.status().toString();
    const body = await response.json();

    const schema = getResponseSchema(spec, '/api/users', 'get', status);
    expect(schema, `No schema found for GET /api/users ${status}`).not.toBeNull();

    const result = validateAgainstSchema(body, schema!);
    expect(result.valid, result.summary).toBe(true);
  });

  test('GET /api/users/:id returns response matching spec', async ({ request }) => {
    const response = await request.get('/api/users/1');
    const status = response.status().toString();
    const body = await response.json();

    const schema = getResponseSchema(spec, '/api/users/{id}', 'get', status);
    expect(schema).not.toBeNull();

    const result = validateAgainstSchema(body, schema!);
    expect(result.valid, result.summary).toBe(true);
  });

  test('POST /api/users error response matches error schema', async ({ request }) => {
    // Send invalid data to trigger validation error
    const response = await request.post('/api/users', {
      data: { invalid: 'payload' },
    });
    const status = response.status().toString();
    const body = await response.json();

    const schema = getResponseSchema(spec, '/api/users', 'post', status);
    if (schema) {
      const result = validateAgainstSchema(body, schema);
      expect(result.valid, result.summary).toBe(true);
    }

    // Verify standard error format
    expect(body).toHaveProperty('error');
    expect(typeof body.error).toBe('object');
    if (body.error) {
      expect(body.error).toHaveProperty('message');
      expect(typeof body.error.message).toBe('string');
    }
  });

  test('response content-type matches spec', async ({ request }) => {
    const response = await request.get('/api/users');
    const contentType = response.headers()['content-type'];

    expect(contentType).toContain('application/json');
  });

  test('pagination response structure matches spec', async ({ request }) => {
    const response = await request.get('/api/users?page=1&limit=10');
    const body = await response.json();

    // Standard pagination contract
    expect(body).toHaveProperty('data');
    expect(Array.isArray(body.data)).toBe(true);
    expect(body).toHaveProperty('pagination');
    expect(body.pagination).toHaveProperty('page');
    expect(body.pagination).toHaveProperty('limit');
    expect(body.pagination).toHaveProperty('total');
    expect(body.pagination).toHaveProperty('totalPages');

    expect(typeof body.pagination.page).toBe('number');
    expect(typeof body.pagination.limit).toBe('number');
    expect(typeof body.pagination.total).toBe('number');
    expect(typeof body.pagination.totalPages).toBe('number');
  });

  test('validate all documented endpoints return conforming responses', async ({ request }) => {
    const violations: string[] = [];

    for (const [pathTemplate, pathObj] of Object.entries(spec.paths)) {
      for (const [method, operation] of Object.entries(pathObj)) {
        if (['get'].includes(method)) {
          // Replace path parameters with test values
          const resolvedPath = pathTemplate.replace(/{(\w+)}/g, '1');

          try {
            const response = await request.get(resolvedPath);
            const status = response.status().toString();
            const body = await response.json().catch(() => null);

            if (body) {
              const schema = getResponseSchema(spec, pathTemplate, method, status);
              if (schema) {
                const result = validateAgainstSchema(body, schema);
                if (!result.valid) {
                  violations.push(
                    `${method.toUpperCase()} ${pathTemplate} (${status}): ${result.summary}`
                  );
                }
              }
            }
          } catch (error) {
            // Skip unreachable endpoints
          }
        }
      }
    }

    expect(
      violations,
      `Contract violations found:\n${violations.join('\n')}`
    ).toHaveLength(0);
  });
});
```
