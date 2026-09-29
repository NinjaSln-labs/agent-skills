# More Examples (extracted from SKILL.md)

Python, Java, locale-specific data, and full database seeding examples. Referenced from SKILL.md; content unchanged.

## Locale-Specific Data

```typescript
import { faker } from '@faker-js/faker';
import { fakerDE } from '@faker-js/faker';
import { fakerJA } from '@faker-js/faker';

// German locale
const germanUser = {
  name: fakerDE.person.fullName(),
  address: fakerDE.location.streetAddress(),
  phone: fakerDE.phone.number(),
};

// Japanese locale
const japaneseUser = {
  name: fakerJA.person.fullName(),
  address: fakerJA.location.streetAddress(),
};
```

## Python -- Faker and Factory Boy

### Faker (Python)

```python
from faker import Faker

fake = Faker()
Faker.seed(42)  # For reproducibility

user = {
    "id": fake.uuid4(),
    "email": fake.email(),
    "first_name": fake.first_name(),
    "last_name": fake.last_name(),
    "phone": fake.phone_number(),
    "address": fake.address(),
    "company": fake.company(),
    "created_at": fake.date_time_this_year().isoformat(),
}
```

### Factory Boy (Python)

```python
import factory
from faker import Faker
from myapp.models import User, Order

fake = Faker()

class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(fake.uuid4)
    email = factory.LazyFunction(fake.email)
    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    role = "user"
    is_active = True

    class Params:
        admin = factory.Trait(role="admin")
        inactive = factory.Trait(is_active=False)

# Usage
user = UserFactory()
admin = UserFactory(admin=True)
inactive_users = UserFactory.create_batch(5, inactive=True)
```

## Java -- Test Data Generation

```java
import com.github.javafaker.Faker;
import java.util.Locale;

public class TestDataGenerator {
    private static final Faker faker = new Faker(new Locale("en-US"));

    public static Map<String, Object> generateUser() {
        Map<String, Object> user = new HashMap<>();
        user.put("email", faker.internet().emailAddress());
        user.put("firstName", faker.name().firstName());
        user.put("lastName", faker.name().lastName());
        user.put("phone", faker.phoneNumber().cellPhone());
        user.put("address", faker.address().fullAddress());
        return user;
    }

    public static Map<String, Object> generateProduct() {
        Map<String, Object> product = new HashMap<>();
        product.put("name", faker.commerce().productName());
        product.put("price", Double.parseDouble(faker.commerce().price()));
        product.put("category", faker.commerce().department());
        product.put("description", faker.lorem().paragraph());
        return product;
    }
}
```

## Database Seeding

```typescript
// seeders/db-seeder.ts
import { UserFactory } from '../factories/user.factory';
import { ProductFactory } from '../factories/product.factory';
import { OrderBuilder } from '../builders/order.builder';
import { db } from '../../src/database';

export class DatabaseSeeder {
  async seedUsers(count: number = 50): Promise<string[]> {
    const users = UserFactory.createMany(count);
    const ids: string[] = [];

    for (const user of users) {
      const result = await db.users.create({ data: user });
      ids.push(result.id);
    }

    return ids;
  }

  async seedProducts(count: number = 100): Promise<string[]> {
    const products = ProductFactory.createMany(count);
    const ids: string[] = [];

    for (const product of products) {
      const result = await db.products.create({ data: product });
      ids.push(result.id);
    }

    return ids;
  }

  async seedOrders(userIds: string[], productIds: string[], count: number = 200): Promise<void> {
    for (let i = 0; i < count; i++) {
      const customerId = userIds[Math.floor(Math.random() * userIds.length)];
      const order = new OrderBuilder()
        .withCustomer(customerId)
        .withItems(Math.floor(Math.random() * 5) + 1)
        .withStatus(['pending', 'confirmed', 'shipped', 'delivered'][Math.floor(Math.random() * 4)] as any)
        .build();

      await db.orders.create({ data: order });
    }
  }

  async seedAll(): Promise<void> {
    const userIds = await this.seedUsers();
    const productIds = await this.seedProducts();
    await this.seedOrders(userIds, productIds);
    console.log('Database seeded successfully');
  }

  async cleanup(): Promise<void> {
    await db.orders.deleteMany({});
    await db.products.deleteMany({});
    await db.users.deleteMany({});
    console.log('Database cleaned up');
  }
}
```
