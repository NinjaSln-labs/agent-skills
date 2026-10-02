---
name: architecture-patterns
description: >-
  Implement proven backend architecture patterns including Clean Architecture, Hexagonal
  Architecture, and Domain-Driven Design (ports/adapters, dependency rule, in-memory
  adapters for unit tests). Use when designing clean architecture for a new microservice,
  refactoring a monolith to bounded contexts, implementing hexagonal or onion
  architecture, or debugging dependency cycles between application layers.
slug: architecture-patterns
version: 1.2.0
displayName: architecture-patterns
---

# Architecture Patterns


## 中文速览（Quick Guide）

- **做什么**：按 Clean Architecture、六边形架构与 DDD 战术模式，落地分层结构、依赖规则、接口定义与测试边界。
- **何时用**：设计新后端服务、把逻辑与 ORM/HTTP 纠缠的单体拆出边界上下文，或排查层间循环依赖、框架装饰器侵入领域实体等问题。
- **核心步骤**：①确认目标服务/模块（无则先问、模块不存在就报 not found）→ ②按 Clean/Hexagonal/DDD 组织 domain、application、ports、adapters 并守住依赖规则 → ③用内存适配器写无需数据库的用例测试 → ④对照 Troubleshooting 里的可观察症状排查。
- **国内可达性**：本技能为本地代码结构分析与改写，不依赖境外在线服务。
Master proven backend architecture patterns including Clean Architecture, Hexagonal Architecture, and Domain-Driven Design to build maintainable, testable, and scalable systems.

**Given:** a service boundary or module to architect.
**Produces:** layered structure with clear dependency rules, interface definitions, and test boundaries.

## When to Use This Skill

- Designing new backend services or microservices from scratch
- Refactoring monolithic applications where business logic is entangled with ORM models or HTTP concerns
- Establishing bounded contexts before splitting a system into services
- Debugging dependency cycles where infrastructure code bleeds into the domain layer
- Creating testable codebases where use-case tests do not require a running database
- Implementing domain-driven design tactical patterns (aggregates, value objects, domain events)

## When NOT to Use This Skill

- There is no runnable service or codebase yet and the user only wants a topic overview — this skill drives structure decisions, not essays; ask for the target module first.
- The code under discussion is a CLI/script or single-file utility — layering overhead exceeds benefit; observe the dependency rule only if growth is expected.
- The question is which *bounded contexts* exist (strategic) — use a DDD strategic-design skill first; this skill assumes contexts are decided and handles what lives inside them.
- The ask is a CQRS/Saga/event-store implementation — those are related families (see bottom), not covered here.

## Quick Diagnosis (FAQ)

Fast symptom → section lookup; each entry maps to the full fix in Troubleshooting below:

| Q: I see... | A: Go to |
|-------------|----------|
| Unit tests need a real database | "Use case tests require a running database" |
| `ImportError` between layers | "Circular imports between layers" |
| ORM/Pydantic decorators on entities | "Framework decorators appearing in domain entities" |
| Controllers doing business logic | "All logic ending up in controllers" |
| Invalid `Email`/`Money` objects exist at runtime | "Value objects raising errors too late" |
| One context importing another's entities | "Context bleed across bounded contexts" |

## Failure Exits and Edge Handling (observable)

| Situation | Observable exit |
|-----------|-----------------|
| No repository/module given ("make our code clean") | Ask which service or module to architect; do not produce a generic lecture. |
| Repo absent or the named module does not exist | Stop and report "module not found: <path>"; do not invent a structure for code you cannot see. |
| Existing code deliberately violates layering (framework-coupled core by team decision) | Flag the deviation and its cost once, then follow the team's convention — do not silently rewrite. |
| `references/details.md` / `references/advanced-patterns.md` missing from the package | Continue with the navigation-tier content in this file; report "reference file missing" instead of paraphrasing from memory as if quoted. |

## Minimal Worked Example

**Preconditions:** a module (`use_cases/`, `domain/`, `adapters/`) exists and is testable.

**Invocation:**

```
/architecture-patterns design the create-user flow in services/identity so
use-case tests run without Postgres
```

**Excerpt of the produced output (what "done" looks like):**

```text
Structure:
  domain/interfaces/user_repository.py   → IUserRepository (port)
  domain/entities/user.py                → User entity, no framework imports
  use_cases/create_user.py               → CreateUserUseCase(repo: IUserRepository)
  adapters/repositories/pg_user_repo.py  → Postgres adapter (wired in composition root)

Dependency rule check: use_cases imports only domain/  ✓
Test boundary: InMemoryUserRepository substitutes the port — no DB, no Docker ✓
```

## Core Concepts

### 1. Clean Architecture (Uncle Bob)

**Layers (dependency flows inward):**

- **Entities**: Core business models, no framework imports
- **Use Cases**: Application business rules, orchestrate entities
- **Interface Adapters**: Controllers, presenters, gateways — translate between use cases and external formats
- **Frameworks & Drivers**: UI, database, external services — all at the outermost ring

**Key Principles:**

- Dependencies point inward only; inner layers know nothing about outer layers
- Business logic is independent of frameworks, databases, and delivery mechanisms
- Every layer boundary is crossed via an abstract interface
- Testable without UI, database, or external services

### 2. Hexagonal Architecture (Ports and Adapters)

**Components:**

- **Domain Core**: Business logic lives here, framework-free
- **Ports**: Abstract interfaces that define how the core interacts with the outside world (driving and driven)
- **Adapters**: Concrete implementations of ports (PostgreSQL adapter, Stripe adapter, REST adapter)

**Benefits:**

- Swap implementations without touching the core (e.g., replace PostgreSQL with DynamoDB)
- Use in-memory adapters in tests — no Docker required
- Technology decisions deferred to the edges

### 3. Domain-Driven Design (DDD)

**Strategic Patterns:**

- **Bounded Contexts**: Isolate a coherent model for one subdomain; avoid sharing a single model across the whole system
- **Context Mapping**: Define how contexts relate (Anti-Corruption Layer, Shared Kernel, Open Host Service)
- **Ubiquitous Language**: Every term in code matches the term used by domain experts

**Tactical Patterns:**

- **Entities**: Objects with stable identity that change over time
- **Value Objects**: Immutable objects identified by their attributes (Email, Money, Address)
- **Aggregates**: Consistency boundaries; only the root is accessible from outside
- **Repositories**: Persist and reconstitute aggregates; abstract over the storage mechanism
- **Domain Events**: Capture things that happened inside the domain; used for cross-aggregate coordination

## Detailed patterns and worked examples

Detailed pattern documentation lives in `references/details.md`. Read that file when the navigation tier above is insufficient.

## Testing — In-Memory Adapters

The hallmark of correctly applied Clean Architecture is that every use case can be exercised in a plain unit test with no real database, no Docker, and no network:

```python
# tests/unit/test_create_user.py
import asyncio
from typing import Dict, Optional
from domain.entities.user import User
from domain.interfaces.user_repository import IUserRepository
from use_cases.create_user import CreateUserUseCase, CreateUserRequest


class InMemoryUserRepository(IUserRepository):
    def __init__(self):
        self._store: Dict[str, User] = {}

    async def find_by_id(self, user_id: str) -> Optional[User]:
        return self._store.get(user_id)

    async def find_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self._store.values() if u.email == email), None)

    async def save(self, user: User) -> User:
        self._store[user.id] = user
        return user

    async def delete(self, user_id: str) -> bool:
        return self._store.pop(user_id, None) is not None


async def test_create_user_succeeds():
    repo = InMemoryUserRepository()
    use_case = CreateUserUseCase(user_repository=repo)

    response = await use_case.execute(CreateUserRequest(email="alice@example.com", name="Alice"))

    assert response.success
    assert response.user.email == "alice@example.com"
    assert response.user.id is not None


async def test_duplicate_email_rejected():
    repo = InMemoryUserRepository()
    use_case = CreateUserUseCase(user_repository=repo)

    await use_case.execute(CreateUserRequest(email="alice@example.com", name="Alice"))
    response = await use_case.execute(CreateUserRequest(email="alice@example.com", name="Alice2"))

    assert not response.success
    assert "already exists" in response.error
```

## Troubleshooting

### Use case tests require a running database

Business logic has leaked into the infrastructure layer. Move all database calls behind an `IRepository` interface and inject an in-memory implementation in tests (see Testing section above). The use case constructor must accept the abstract port, not the concrete class.

### Circular imports between layers

A common symptom is `ImportError: cannot import name X` between `use_cases` and `adapters`. This happens when a use case imports a concrete adapter class instead of the abstract port. Enforce the rule: `use_cases/` imports only from `domain/` (entities and interfaces). It must never import from `adapters/` or `infrastructure/`.

### Framework decorators appearing in domain entities

If SQLAlchemy `Column()` or Pydantic `Field()` annotations appear on domain entities, the entity is no longer pure. Create a separate ORM model in `adapters/repositories/` and map to/from the domain entity in the repository's `_to_entity()` method.

### All logic ending up in controllers

When the controller grows beyond HTTP parsing and response formatting, extract the logic into a use case class. A controller method should do three things only: parse the request, call a use case, map the response.

### Value objects raising errors too late

Validate invariants in `__post_init__` (Python) or the constructor so an invalid `Email` or `Money` cannot be constructed at all. This surfaces bad data at the boundary, not deep inside business logic.

### Context bleed across bounded contexts

If the `Order` context is importing `User` entities from the `Identity` context, introduce an Anti-Corruption Layer. The `Order` context should hold its own lightweight `CustomerId` value object and only call the `Identity` context through an explicit interface.

## Advanced Patterns

For detailed DDD bounded context mapping, full multi-service project trees, Anti-Corruption Layer implementations, and Onion Architecture comparisons, see:

- [`references/advanced-patterns.md`](references/advanced-patterns.md)

## Related Pattern Families

These architecture patterns connect to broader pattern families that this skill does not itself cover:

- **Microservices patterns** — apply these architecture patterns when decomposing a monolith into services
- **CQRS** — use Clean Architecture as the structural foundation for command/query separation
- **Saga orchestration** — sagas require well-defined aggregate boundaries, which DDD tactical patterns provide
- **Event store design** — domain events produced by aggregates feed directly into an event store
