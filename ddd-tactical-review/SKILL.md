---
name: ddd-tactical-review
description: >-
  Detects anemic domain models, validates and refactors them into rich domain models, and
  enforces tactical DDD patterns (Entities, Value Objects, Aggregates, Domain Services,
  Domain Events). Use when the user asks to validate, review, or check domain models or
  DDD code; detect anemia; refactor domain objects; improve encapsulation; or mentions
  terms like "anemic model", "rich domain", "aggregate", "value object", "domain event",
  "ubiquitous language", "is this good DDD", "does this follow DDD", or "check my domain".
  Do NOT use for module or service boundary design, architectural decomposition, strategic
  DDD context mapping, or code outside the domain layer (DTOs, controllers, infrastructure
  adapters).
slug: ddd-tactical-review
version: 1.1.0
displayName: ddd-tactical-review
---

# Tactical DDD — Rich Domain Modeling

## Workflow

Determine the user's intent first:

| Intent | Phases to run |
|--------|--------------|
| "validate / review / check / is this correct?" | Phase 1 + 2 only → report findings, ask before refactoring |
| "fix / refactor / improve / clean up" | Phase 1 + 2 + 3 |
| "how should I design / model this?" | Load [reference.md](reference.md) directly |

### Phase 1 — Detect
Load [detection.md](detection.md) and scan the target code for anemia signals. Produce a severity score and list of affected classes.

### Phase 2 — Assess
For each affected class, determine the correct building block:

| Has unique identity tracked over time? | Has invariants tying multiple objects? | → Building Block |
|----------------------------------------|----------------------------------------|-----------------|
| Yes | — | **Entity** |
| No | — | **Value Object** |
| Yes (root) + children with shared invariants | Yes | **Aggregate** |
| Operation spans multiple Aggregates/doesn't belong to any | — | **Domain Service** |

Prefer Value Objects over Entities. Prefer small Aggregates over large ones.

**If intent was validate/review**: stop here. Report findings using the output format below. Ask "Would you like me to apply these fixes?" before proceeding.

### Phase 3 — Refactor
Load [refactoring.md](refactoring.md) for step-by-step moves. Apply in this order:
1. Replace setter chains with a single expressive method
2. Move service logic into the Aggregate that owns it
3. Add business guards at the top of each method
4. Publish a Domain Event after each successful state change
5. Replace primitive types with Value Objects

For deep pattern questions (boundary design, event modeling, service vs. entity decision), load [reference.md](reference.md).

---

## Quick Anemia Signals (scan first)

```
public setX() / public setY()        → behaviour should be encapsulated
service.doX(entity, ...)              → logic likely belongs in entity
entity.setA(); entity.setB(); ...     → setter chain = missing intent method
no domain methods beyond getters      → pure data bag
```

---

## Golden Rules

1. **Behaviour with data** — Objects own both state and the operations that change it
2. **Ubiquitous Language** — Method names come from the domain, not CRUD (`commitTo`, not `setStatus`)
3. **Small Aggregates** — Root + Value Objects by default; add child Entities only for true invariants
4. **One transaction = one Aggregate** — Cross-Aggregate rules use eventual consistency via Domain Events
5. **Reference by ID** — Never hold object references to other Aggregates
6. **Value Objects first** — Use Entities only when individual identity is essential
7. **Domain Services sparingly** — Excessive services → anemic model
8. **Protect invariants** — The Aggregate is the last line of defence; never trust the caller

---

## Output Format

When reviewing code, report:

```
## Anemia Diagnosis: <ClassName>

Severity: [None | Mild | Moderate | Severe]

Issues:
- <description of problem>

Recommended refactoring:
- <specific move from refactoring.md>
```

When refactoring, show a before/after diff for each class touched.

## Minimal Worked Example

**Input (user):** "Check my domain — is this anemic?" with a file containing:

```java
public class Order {
    private OrderStatus status;
    private BigDecimal total;
    public OrderStatus getStatus() { return status; }
    public void setStatus(OrderStatus s) { this.status = s; }
    public BigDecimal getTotal() { return total; }
    public void setTotal(BigDecimal t) { this.total = t; }
}
public class OrderService {
    public void complete(Order o) {
        o.setStatus(OrderStatus.COMPLETED);
        o.setTotal(o.getTotal().add(fee));
    }
}
```

**Output excerpt (Phase 1+2, validate intent — report, then ask before refactoring):**

```
## Anemia Diagnosis: Order

Severity: Severe

Issues:
- No domain methods beyond getters/setters — pure data bag
- OrderService.complete() mutates Order state — logic that belongs in the Aggregate
- setStatus() allows arbitrary transitions; no invariant guard

Recommended refactoring:
- Move complete() into Order as an intent method with a business guard
- Replace setStatus() setter chains with a single expressive method
```

Then ask: "Would you like me to apply these fixes?"

## Wrong Way → Fix (FAQ)

| Wrong way | Observable symptom | Fix |
|-----------|--------------------|-----|
| Refactoring immediately on a "review/check" request | Diffs appear without a diagnosis report or permission question | Phase 1+2 only; stop at the report and ask before Phase 3. |
| Reviewing DTOs, controllers, or infrastructure adapters | "Anemic" findings on classes outside the domain layer | Out of scope — DTOs are deliberately data bags. State that the class is outside the domain layer and skip it; do not report it as anemia. |
| Treating every primitive as a defect | A proposed Value Object for every `int`/`string` | Prefer VOs where invariants or vocabulary exist (`Money`, `Email`); report only primitives that carry domain meaning. |
| Large Aggregate "to keep everything consistent" | One Aggregate spanning many child Entities | Default to root + Value Objects; add child Entities only for true invariants; cross-Aggregate rules go via Domain Events. |
| Answering strategic questions (context mapping, service boundaries) with this skill | Advice about bounded contexts or microservice split | Out of scope. Say the question belongs to strategic DDD / architecture work and stop. |

## Failure Exits and Boundaries (observable)

This skill reads whatever code you point it at — there is no script and no exit code. Each dead end has a visible, sayable outcome:

- **No repository / no code in context:** do not invent sample code and review it. Say "no domain code to review" and ask the user to point at the module or paste the classes.
- **Wrong repo / framework code only (no domain layer found):** report "no domain-layer classes detected in the provided code" and name what would qualify (entities with state+behavior candidates). Do not grade DTO layers as anemia.
- **Empty or trivial model (1–2 classes, no behavior):** run Phase 1 honestly; if severity is `None`, output the report with `Severity: None` and "no issues" — do not fabricate findings to seem useful.
- **Not a review/refactor/modeling request:** out of scope (see description NOT for). Name the actual capability boundary in one sentence and stop.
