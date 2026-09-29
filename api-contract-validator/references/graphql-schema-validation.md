<!-- Extracted verbatim from SKILL.md section 'GraphQL Schema Validation'. Edit content in this file; SKILL.md keeps only the pointer. -->

## GraphQL Schema Validation

```typescript
// tests/contracts/graphql/schema-validation.spec.ts
import { test, expect } from '@playwright/test';

test.describe('GraphQL Schema Validation', () => {
  test('introspection returns expected types', async ({ request }) => {
    const response = await request.post('/graphql', {
      data: {
        query: `
          {
            __schema {
              types {
                name
                kind
              }
              queryType { name }
              mutationType { name }
            }
          }
        `,
      },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    const typeNames = body.data.__schema.types.map(
      (t: { name: string }) => t.name
    );

    // Verify expected types exist
    expect(typeNames).toContain('User');
    expect(typeNames).toContain('Document');
    expect(typeNames).toContain('Query');
    expect(typeNames).toContain('Mutation');
  });

  test('query returns data matching declared return type', async ({ request }) => {
    const response = await request.post('/graphql', {
      data: {
        query: `
          query GetUser($id: ID!) {
            user(id: $id) {
              id
              name
              email
              createdAt
            }
          }
        `,
        variables: { id: '1' },
      },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();

    expect(body.errors).toBeUndefined();
    expect(body.data.user).toBeDefined();
    expect(typeof body.data.user.id).toBe('string');
    expect(typeof body.data.user.name).toBe('string');
    expect(typeof body.data.user.email).toBe('string');
  });

  test('non-nullable fields never return null', async ({ request }) => {
    const response = await request.post('/graphql', {
      data: {
        query: `
          {
            __type(name: "User") {
              fields {
                name
                type {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
          }
        `,
      },
    });

    const body = await response.json();
    const fields = body.data.__type?.fields || [];

    const nonNullableFields = fields
      .filter((f: Record<string, unknown>) => {
        const fieldType = f.type as { kind: string };
        return fieldType.kind === 'NON_NULL';
      })
      .map((f: Record<string, unknown>) => f.name as string);

    // Fetch actual data and verify non-nullable fields are not null
    const dataResponse = await request.post('/graphql', {
      data: {
        query: `{ users { ${nonNullableFields.join(' ')} } }`,
      },
    });

    const dataBody = await dataResponse.json();
    if (dataBody.data?.users) {
      for (const user of dataBody.data.users) {
        for (const field of nonNullableFields) {
          expect(
            user[field],
            `Non-nullable field "${field}" is null`
          ).not.toBeNull();
        }
      }
    }
  });

  test('deprecated fields trigger warnings but still work', async ({ request }) => {
    const schemaResponse = await request.post('/graphql', {
      data: {
        query: `
          {
            __type(name: "User") {
              fields(includeDeprecated: true) {
                name
                isDeprecated
                deprecationReason
              }
            }
          }
        `,
      },
    });

    const body = await schemaResponse.json();
    const deprecatedFields = body.data.__type?.fields?.filter(
      (f: Record<string, boolean>) => f.isDeprecated
    ) || [];

    for (const field of deprecatedFields) {
      expect(
        field.deprecationReason,
        `Deprecated field "${field.name}" should have a deprecation reason`
      ).toBeTruthy();

      // Verify deprecated field still returns data
      const queryResponse = await request.post('/graphql', {
        data: {
          query: `{ users { ${field.name} } }`,
        },
      });
      expect(queryResponse.status()).toBe(200);
    }
  });
});
```
