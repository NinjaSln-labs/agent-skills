---
name: test-data-generation
description: >-
  Test data strategies using Faker.js, factories, builders, and database seeding. Use when
  generating test data, fixtures, or seeded databases, or when flaky tests fail on
  inconsistent data — deterministic seeds and factory patterns are the fix.
slug: test-data-generation
version: 1.1.0
displayName: test-data-generation
---

# Test Data Generation Skill

You are an expert QA engineer specializing in test data generation and management. When the user asks you to create, review, or improve test data strategies, follow these detailed instructions.

## When to use / NOT for

- **Use when**: the user asks to generate test data or fixtures, set up factories/builders, seed a test database, or make flaky data-dependent tests deterministic.
- **NOT for**: anonymizing or masking real production data (different risk model — use a dedicated data-masking process); production seed scripts; load-testing datasets at scale (generate a small fixture set here, scale separately). If the request involves real PII at all, stop and confirm the data is synthetic (see Anti-Pattern 6).

## Minimal worked example

Precondition: npm project with `@faker-js/faker` installed (`npm install --save-dev @faker-js/faker`).

Invocation (paste the TypeScript Factory + "Using Factories in Tests" snippets from this skill into `tests/data/factories/user.factory.ts` and a spec file), then run:

```bash
npx playwright test
```

Output excerpt — a generated input looks like:

```json
{ "email": "kianna.satterfield47@unknown-fawn.name", "firstName": "Marcos", "lastName": "Yundt", "password": "u7#kQ2vPz9xR", "role": "user" }
```

and the test asserts:

```
✓  should create a new user
  expect(received).toBe(expected) // response.status() === 201
  1 passed
```

Note: re-running with the same `faker.seed(12345)` reproduces the exact same email/firstName; without a seed, every run generates different values (both are valid — see Seeded Random Data).

## Failure exits

| Situation | Observable signal | Exit action |
|-----------|-------------------|-------------|
| Faker not installed | `Cannot find module '@faker-js/faker'` (test run exits non-zero) | Run `npm install --save-dev @faker-js/faker`, rerun. |
| Same test, different data each run (reproducibility broken) | assertion on a generated value fails intermittently | Confirm `faker.seed(N)` is called before generation with the same N in both runs; unseeded random data must never be asserted exactly (Anti-Pattern 7). |
| App validation rejects generated data | API returns 400/422 on factory-created input | Tighten the factory field to the app's format constraints (Anti-Pattern 9) — do not loosen the validation to fit the data. |
| Parallel tests collide | duplicate unique-key errors (e.g. same email twice) | Replace hardcoded fields with per-test unique values (uuid/timestamp); see Anti-Pattern 1. |
| Faker seed method error / old version | `faker.seed is not a function` | The snippet targets `@faker-js/faker` v7+; check `npm ls @faker-js/faker` and upgrade. |
| Wrong repo / no test framework | no `tests/` dir, no playwright/vitest/jest config found | Ask the user which framework and directory the tests live in; do not scaffold into a guessed location. |

## FAQ (wrong way → right way)

| Wrong | Right |
|-------|-------|
| Hardcoding `"user1@test.com"` in every test | `UserFactory.createInput()` — unique per test, overrides only what matters |
| Asserting exact values on unseeded random data | Either seed (`faker.seed(42)`) or assert shape/presence, not exact content |
| One shared user row mutated by many tests (`beforeAll` setup) | Each test creates its own data (Core Principle 4); teardown deletes it |
| Pasting real user emails/names into fixtures | Always faker-generated or clearly fake (`test@example.com`) — never real PII |
| Generating 1000 rows "to be safe" | Generate the minimum the test asserts on (Core Principle 3) |

## Core Principles

1. **Deterministic when needed** -- Use seeded randomness for reproducible test runs.
2. **Realistic but safe** -- Data should look real but never contain actual PII.
3. **Minimal and focused** -- Generate only the data attributes each test actually needs.
4. **Independent** -- Each test creates its own data; never share mutable state.
5. **Clean up after** -- Remove generated data in teardown to prevent pollution.

## Project Structure

```
tests/
  data/
    factories/
      user.factory.ts
      product.factory.ts
      order.factory.ts
    builders/
      user.builder.ts
      order.builder.ts
    fixtures/
      static-data.json
    seeders/
      db-seeder.ts
      api-seeder.ts
    generators/
      fake-data.ts
      credit-card.ts
  utils/
    data-cleanup.ts
```

## Faker.js -- TypeScript

### Installation

```bash
npm install --save-dev @faker-js/faker
```

### Basic Usage

```typescript
import { faker } from '@faker-js/faker';

// Generate consistent data with a seed
faker.seed(12345);

// User data
const user = {
  id: faker.string.uuid(),
  firstName: faker.person.firstName(),
  lastName: faker.person.lastName(),
  email: faker.internet.email(),
  phone: faker.phone.number(),
  avatar: faker.image.avatar(),
  address: {
    street: faker.location.streetAddress(),
    city: faker.location.city(),
    state: faker.location.state(),
    zip: faker.location.zipCode(),
    country: faker.location.country(),
  },
  company: faker.company.name(),
  jobTitle: faker.person.jobTitle(),
  bio: faker.lorem.paragraph(),
  createdAt: faker.date.past().toISOString(),
};

// Product data
const product = {
  id: faker.string.uuid(),
  name: faker.commerce.productName(),
  description: faker.commerce.productDescription(),
  price: parseFloat(faker.commerce.price({ min: 1, max: 1000 })),
  category: faker.commerce.department(),
  sku: faker.string.alphanumeric(10).toUpperCase(),
  inStock: faker.datatype.boolean(),
  rating: faker.number.float({ min: 1, max: 5, fractionDigits: 1 }),
  imageUrl: faker.image.url(),
};

// Financial data
const transaction = {
  id: faker.string.uuid(),
  amount: parseFloat(faker.finance.amount({ min: 10, max: 5000 })),
  currency: faker.finance.currencyCode(),
  accountNumber: faker.finance.accountNumber(),
  routingNumber: faker.finance.routingNumber(),
  transactionType: faker.helpers.arrayElement(['credit', 'debit', 'transfer']),
  date: faker.date.recent({ days: 30 }).toISOString(),
  status: faker.helpers.arrayElement(['pending', 'completed', 'failed', 'reversed']),
};
```

### Locale-Specific Data

For `fakerDE` / `fakerJA` locale examples, see `references/more-examples.md` (Locale-Specific Data).

## Factory Pattern

### TypeScript Factory

```typescript
// factories/user.factory.ts
import { faker } from '@faker-js/faker';

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'user' | 'viewer';
  isActive: boolean;
  createdAt: string;
}

export interface CreateUserInput {
  email: string;
  firstName: string;
  lastName: string;
  password: string;
  role?: 'admin' | 'user' | 'viewer';
}

export class UserFactory {
  static create(overrides: Partial<User> = {}): User {
    return {
      id: faker.string.uuid(),
      email: faker.internet.email(),
      firstName: faker.person.firstName(),
      lastName: faker.person.lastName(),
      role: 'user',
      isActive: true,
      createdAt: faker.date.past().toISOString(),
      ...overrides,
    };
  }

  static createMany(count: number, overrides: Partial<User> = {}): User[] {
    return Array.from({ length: count }, () => this.create(overrides));
  }

  static createInput(overrides: Partial<CreateUserInput> = {}): CreateUserInput {
    return {
      email: faker.internet.email(),
      firstName: faker.person.firstName(),
      lastName: faker.person.lastName(),
      password: faker.internet.password({ length: 12, memorable: false }),
      role: 'user',
      ...overrides,
    };
  }

  static createAdmin(overrides: Partial<User> = {}): User {
    return this.create({ role: 'admin', ...overrides });
  }

  static createInactive(overrides: Partial<User> = {}): User {
    return this.create({ isActive: false, ...overrides });
  }
}
```

### Using Factories in Tests

```typescript
import { test, expect } from '@playwright/test';
import { UserFactory } from '../data/factories/user.factory';

test('should create a new user', async ({ request }) => {
  const userData = UserFactory.createInput();

  const response = await request.post('/api/users', { data: userData });
  expect(response.status()).toBe(201);

  const body = await response.json();
  expect(body.email).toBe(userData.email);
  expect(body.firstName).toBe(userData.firstName);
});

test('should list users with pagination', async ({ request }) => {
  // Create multiple users
  const users = UserFactory.createMany(15);
  for (const user of users) {
    await request.post('/api/users', {
      data: UserFactory.createInput({
        email: user.email,
        firstName: user.firstName,
      }),
    });
  }

  const response = await request.get('/api/users?page=1&pageSize=10');
  const body = await response.json();
  expect(body.data.length).toBe(10);
  expect(body.total).toBeGreaterThanOrEqual(15);
});
```

## Builder Pattern

### TypeScript Builder

```typescript
// builders/order.builder.ts
import { faker } from '@faker-js/faker';

export interface OrderItem {
  productId: string;
  name: string;
  quantity: number;
  price: number;
}

export interface Order {
  id: string;
  customerId: string;
  items: OrderItem[];
  status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  shippingAddress: {
    street: string;
    city: string;
    state: string;
    zip: string;
    country: string;
  };
  totalAmount: number;
  createdAt: string;
}

export class OrderBuilder {
  private order: Order;

  constructor() {
    this.order = {
      id: faker.string.uuid(),
      customerId: faker.string.uuid(),
      items: [],
      status: 'pending',
      shippingAddress: {
        street: faker.location.streetAddress(),
        city: faker.location.city(),
        state: faker.location.state(),
        zip: faker.location.zipCode(),
        country: 'US',
      },
      totalAmount: 0,
      createdAt: new Date().toISOString(),
    };
  }

  withCustomer(customerId: string): this {
    this.order.customerId = customerId;
    return this;
  }

  withItem(item?: Partial<OrderItem>): this {
    const newItem: OrderItem = {
      productId: item?.productId ?? faker.string.uuid(),
      name: item?.name ?? faker.commerce.productName(),
      quantity: item?.quantity ?? faker.number.int({ min: 1, max: 5 }),
      price: item?.price ?? parseFloat(faker.commerce.price({ min: 5, max: 200 })),
    };
    this.order.items.push(newItem);
    this.order.totalAmount = this.order.items.reduce(
      (sum, i) => sum + i.price * i.quantity, 0
    );
    return this;
  }

  withItems(count: number): this {
    for (let i = 0; i < count; i++) {
      this.withItem();
    }
    return this;
  }

  withStatus(status: Order['status']): this {
    this.order.status = status;
    return this;
  }

  withShippingTo(country: string): this {
    this.order.shippingAddress.country = country;
    return this;
  }

  cancelled(): this {
    return this.withStatus('cancelled');
  }

  delivered(): this {
    return this.withStatus('delivered');
  }

  build(): Order {
    if (this.order.items.length === 0) {
      this.withItem(); // Add at least one item
    }
    return { ...this.order };
  }
}

// Usage in tests
const order = new OrderBuilder()
  .withCustomer('customer-123')
  .withItem({ name: 'Widget', price: 29.99, quantity: 2 })
  .withItem({ name: 'Gadget', price: 49.99, quantity: 1 })
  .withShippingTo('US')
  .build();
```

## Python -- Faker and Factory Boy

Full Python examples (Faker + Factory Boy) moved to `references/more-examples.md` (Python section).

## Java -- Test Data Generation

The JavaFaker `TestDataGenerator` example moved to `references/more-examples.md` (Java section).

## Database Seeding

The full `DatabaseSeeder` class (seedUsers / seedProducts / seedOrders / seedAll / cleanup against `db.users` / `db.products` / `db.orders`) moved to `references/more-examples.md` (Database Seeding section). Seeding order matters: users → products → orders (orders reference both); cleanup runs in reverse order.

## Test Data Strategies

### 1. Just-in-Time Generation

Generate data within each test. Best for unit and integration tests.

```typescript
test('should validate email format', () => {
  const validEmail = faker.internet.email();
  const result = validateEmail(validEmail);
  expect(result).toBe(true);
});
```

### 2. Fixture-Based Data

Static data loaded from JSON files. Best for snapshot testing and deterministic scenarios.

```json
{
  "validUser": {
    "email": "test@example.com",
    "password": "ValidPass123!",
    "name": "Test User"
  },
  "invalidEmails": ["not-email", "@missing.com", "spaces here@bad.com"]
}
```

### 3. Seeded Random Data

Deterministic random data using a fixed seed. Best for reproducible randomized tests.

```typescript
beforeEach(() => {
  faker.seed(Date.now()); // Different seed each run
  // OR
  faker.seed(42); // Same data every run
});
```

### 4. API-Seeded Data

Create test data via API calls before tests run. Best for E2E tests.

```typescript
test.beforeAll(async ({ request }) => {
  const user = UserFactory.createInput();
  await request.post('/api/users', { data: user });
});
```

## Best Practices

1. **Seed random generators** -- Use fixed seeds when reproducibility matters.
2. **Use factories for complex objects** -- Factories ensure valid default data.
3. **Use builders for varied objects** -- Builders make it easy to create different variations.
4. **Generate unique data per test** -- Include timestamps or UUIDs to avoid collisions.
5. **Separate creation from assertion** -- Factory creates data; test asserts behavior.
6. **Use realistic formats** -- Phone numbers, emails, and addresses should look real.
7. **Handle cleanup** -- Delete generated data in teardown hooks.
8. **Avoid PII** -- Never use real names, emails, or SSNs in test data.
9. **Parameterize edge cases** -- Use data providers for boundary value testing.
10. **Version your fixtures** -- Static fixture files should be version-controlled.

## Anti-Patterns to Avoid

1. **Hardcoded test data** -- `"user1@test.com"` causes conflicts in parallel tests.
2. **Shared mutable data** -- Multiple tests modifying the same record causes flakiness.
3. **Over-generating** -- Creating 1000 users when 5 suffice wastes time.
4. **Ignoring data dependencies** -- Creating an order without a valid customer ID fails.
5. **No cleanup** -- Leftover test data pollutes the environment.
6. **Real PII in fixtures** -- Using actual names or emails violates privacy regulations.
7. **Non-deterministic assertions on random data** -- Do not assert exact values on random data.
8. **Global test data setup** -- `beforeAll` with shared data leads to coupled tests.
9. **Ignoring data format constraints** -- Generated data must pass validation rules.
10. **Not testing with empty/null data** -- Always include edge cases in your data strategy.
