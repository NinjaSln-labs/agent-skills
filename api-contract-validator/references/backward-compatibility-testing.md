<!-- Extracted verbatim from SKILL.md section 'Backward Compatibility Testing'. Edit content in this file; SKILL.md keeps only the pointer. -->

## Backward Compatibility Testing

```typescript
// tests/contracts/openapi/backward-compat.spec.ts
import { test, expect } from '@playwright/test';
import { loadOpenAPISpec } from '../fixtures/schema-loader';
import { checkBackwardCompatibility } from '../fixtures/contract-helpers';
import * as path from 'path';

test.describe('Backward Compatibility', () => {
  test('current schema is backward compatible with previous version', () => {
    const previousSpec = loadOpenAPISpec(
      path.resolve(__dirname, '../specs/openapi-v1.yaml')
    );
    const currentSpec = loadOpenAPISpec(
      path.resolve(__dirname, '../specs/openapi.yaml')
    );

    const schemasToCheck = ['User', 'Document', 'Error'];

    for (const schemaName of schemasToCheck) {
      const oldSchema = previousSpec.components.schemas[schemaName];
      const newSchema = currentSpec.components.schemas[schemaName];

      if (oldSchema && newSchema) {
        const result = checkBackwardCompatibility(oldSchema, newSchema);
        expect(
          result.compatible,
          `Breaking changes in ${schemaName}:\n${result.breakingChanges.join('\n')}`
        ).toBe(true);
      }
    }
  });

  test('API version header is present and correct', async ({ request }) => {
    const response = await request.get('/api/users');
    const apiVersion = response.headers()['api-version'] ||
      response.headers()['x-api-version'];

    expect(apiVersion).toBeDefined();
    expect(apiVersion).toMatch(/^\d+\.\d+\.\d+$/);
  });

  test('deprecated fields still present but marked', async ({ request }) => {
    const response = await request.get('/api/users/1');
    const body = await response.json();

    // If deprecated fields exist, they should still be present for backward compat
    const spec = loadOpenAPISpec(path.resolve(__dirname, '../specs/openapi.yaml'));
    const userSchema = spec.components.schemas['User'];

    if (userSchema?.properties) {
      for (const [field, fieldSchema] of Object.entries(userSchema.properties)) {
        if ((fieldSchema as Record<string, unknown>).deprecated) {
          // Deprecated fields should still be in the response
          expect(
            body,
            `Deprecated field "${field}" removed before deprecation period ended`
          ).toHaveProperty(field);
        }
      }
    }
  });

  test('new required fields are not added without version bump', async ({ request }) => {
    const v1Response = await request.get('/api/v1/users/1');
    const v2Response = await request.get('/api/v2/users/1');

    if (v1Response.status() === 200 && v2Response.status() === 200) {
      const v1Body = await v1Response.json();
      const v2Body = await v2Response.json();

      const v1Fields = new Set(Object.keys(v1Body));
      const v2Fields = new Set(Object.keys(v2Body));

      // All v1 fields must still exist in v2
      for (const field of v1Fields) {
        expect(
          v2Fields.has(field),
          `Field "${field}" from v1 is missing in v2`
        ).toBe(true);
      }
    }
  });
});
```
