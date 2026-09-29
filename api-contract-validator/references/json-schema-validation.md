<!-- Extracted verbatim from SKILL.md section 'JSON Schema Validation'. Edit content in this file; SKILL.md keeps only the pointer. -->

## JSON Schema Validation

```typescript
// tests/contracts/json-schema/schema-validation.spec.ts
import { test, expect } from '@playwright/test';
import { loadJSONSchema } from '../fixtures/schema-loader';
import { validateAgainstSchema } from '../fixtures/contract-helpers';
import * as path from 'path';

const userSchema = loadJSONSchema(
  path.resolve(__dirname, '../specs/schemas/user.schema.json')
);

const errorSchema = loadJSONSchema(
  path.resolve(__dirname, '../specs/schemas/error.schema.json')
);

test.describe('JSON Schema Validation', () => {
  test('user object conforms to user schema', async ({ request }) => {
    const response = await request.get('/api/users/1');
    expect(response.status()).toBe(200);

    const user = await response.json();
    const result = validateAgainstSchema(user, userSchema);
    expect(result.valid, result.summary).toBe(true);
  });

  test('user list items all conform to user schema', async ({ request }) => {
    const response = await request.get('/api/users');
    expect(response.status()).toBe(200);

    const body = await response.json();
    const users = body.data || body;

    for (let i = 0; i < users.length; i++) {
      const result = validateAgainstSchema(users[i], userSchema);
      expect(result.valid, `User at index ${i}: ${result.summary}`).toBe(true);
    }
  });

  test('error responses conform to error schema', async ({ request }) => {
    const response = await request.get('/api/users/nonexistent-id');

    if (response.status() >= 400) {
      const error = await response.json();
      const result = validateAgainstSchema(error, errorSchema);
      expect(result.valid, result.summary).toBe(true);
    }
  });

  test('required fields are always present', async ({ request }) => {
    const response = await request.get('/api/users/1');
    const user = await response.json();

    const requiredFields = userSchema.required || [];
    for (const field of requiredFields) {
      expect(
        user,
        `Required field "${field}" is missing from user response`
      ).toHaveProperty(field);
    }
  });

  test('field types match schema definitions', async ({ request }) => {
    const response = await request.get('/api/users/1');
    const user = await response.json();
    const properties = userSchema.properties || {};

    for (const [field, fieldSchema] of Object.entries(properties)) {
      if (user[field] !== undefined && user[field] !== null) {
        switch (fieldSchema.type) {
          case 'string':
            expect(typeof user[field], `${field} should be string`).toBe('string');
            break;
          case 'number':
          case 'integer':
            expect(typeof user[field], `${field} should be number`).toBe('number');
            break;
          case 'boolean':
            expect(typeof user[field], `${field} should be boolean`).toBe('boolean');
            break;
          case 'array':
            expect(Array.isArray(user[field]), `${field} should be array`).toBe(true);
            break;
          case 'object':
            expect(typeof user[field], `${field} should be object`).toBe('object');
            break;
        }
      }
    }
  });

  test('string format constraints are enforced', async ({ request }) => {
    const response = await request.get('/api/users/1');
    const user = await response.json();
    const properties = userSchema.properties || {};

    for (const [field, fieldSchema] of Object.entries(properties)) {
      if (user[field] && fieldSchema.type === 'string') {
        if (fieldSchema.format === 'email') {
          expect(user[field]).toMatch(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
        }
        if (fieldSchema.format === 'date-time') {
          expect(new Date(user[field]).toISOString()).toBeTruthy();
        }
        if (fieldSchema.format === 'uri') {
          expect(() => new URL(user[field])).not.toThrow();
        }
        if (fieldSchema.minLength) {
          expect(user[field].length).toBeGreaterThanOrEqual(fieldSchema.minLength);
        }
        if (fieldSchema.maxLength) {
          expect(user[field].length).toBeLessThanOrEqual(fieldSchema.maxLength);
        }
      }
    }
  });
});
```
