---
name: ddd-contexts
description: "Design bounded contexts and their ubiquitous language: boundaries, responsibilities, glossary, team ownership, and boundary ADRs. Use when defining bounded contexts."
lang: en
risk: safe
source: self
tags: "[ddd, strategic, bounded-context, ubiquitous-language]"
date_added: "2026-05-08"
---

# DDD Contexts

> 中文版本: [Chinese](SKILL.md)
>
> 描述权威源＝同目录 `SKILL.md`（本件为正文英译，frontmatter 的 description 与主件逐字同步，勿单改）。

## When to Use

- Subdomains have been classified, and you need to design Bounded Context boundaries in the solution space.
- You need to establish a Ubiquitous Language for each context to eliminate terminology ambiguity.
- When `ddd-aggregates` reports "invariants span multiple contexts," or `ddd-model-review` reports "terminology conflict rate > 20%," re-execute this skill as a backtrack target.

## Input Requirements

- **Required**: Subdomain classification table and core domain declaration (from `ddd-subdomains`), event flows and hotspot annotations (from `ddd-discover`).
- **Optional**: Organizational information (team boundaries, delivery cadence), terminology seeds (from `ddd-scope`).
- **When input is incomplete**: missing subdomain classification or event flows → state what is missing in one line and point to the skill that produces it ("missing the subdomain classification table — run `ddd-subdomains` first, or paste your subdomain list"); if the user insists on a verbal description only → cluster from the description but label every context as Assumption and list "pending inputs" at the top of the output. Never silently fill required inputs with guesses.

## Process

1. **Clustering**: Using consistency boundaries and language boundaries as criteria, cluster capabilities into context candidates. Terms within a single context must have unambiguous meanings.
2. **Define responsibilities**: For each context, clarify business responsibilities, core concepts, main events, and data ownership.
3. **Establish language**: For each core term within a context, create a definition (including 1 business example); annotate synonyms and anti-terms.
4. **Delineate boundaries**: Specify which concepts are valid only within this context and which must be translated when crossing context boundaries.
5. **Ownership & ADR**: Assign the responsible team, decision-maker, and contract owner; output boundary decision ADRs (including rationale, trade-offs, risks, and alternatives).
6. **Conflict resolution**: Handle same-name-different-meaning terms across contexts — provide translation strategies or renaming recommendations.

## Output

| Artifact                     | Structure Requirements                                                                               |
| :--------------------------- | :--------------------------------------------------------------------------------------------------- |
| Context Directory            | Table: context name, responsibilities, core terms, main events, data ownership, responsible team     |
| Ubiquitous Language Glossary | Table: term, definition, business example, owning context, synonyms, anti-terms, conflict resolution |
| Anti-Term List               | Table: prohibited term, prohibition reason, recommended alternative                                  |
| Boundary ADR List            | Each entry includes: decision, rationale, trade-offs, risks, alternatives                            |
| Language Evolution Rules     | List: addition/change process, review roles, versioning strategy                                     |

## Validation Checklist

- [ ] Each context has explicit "responsibilities" and "non-responsibilities"
- [ ] Data ownership has no conflicts; cross-context access must go through contracts/translation
- [ ] Each context has at least 1 explicit trade-off point and risk point (ADR)
- [ ] All terminology conflicts have been resolved (translation or renaming)
- [ ] Anti-term list covers technical word pollution (Manager, Processor, Handler, and other generic terms) and ambiguous business terms
- [ ] If intermediate concepts such as "request/intent" types (e.g., ShippingRequest, OrderDraft, BookingIntent) are introduced in ordering/transaction flows, their lifecycle relationship with the main aggregate has been declared (promoted to independent aggregate vs. treated as a VO of the main aggregate) — both choices are valid but **must be explicitly stated and recorded as an ADR**

## Backtrack Triggers

- More than 5 terms have irreconcilable cross-context conflicts -> backtrack to `ddd-discover`; domain understanding is insufficient.
- Triggered by `ddd-aggregates`: invariants span multiple contexts -> consistency requirements are fragmented by boundaries and need re-partitioning.
- Triggered by `ddd-model-review`: aggregate boundaries contradict context boundaries, or terminology conflict rate > 20%.

## Example

```text
@ddd-contexts
Based on the following subdomain classification and event flows, help me design Bounded Contexts:
- Core: Booking & Conflict Management
- Supporting: Meeting Room Resource Management
- Generic: User Identity & Permissions
[paste event flow table]
Please output context directory, Ubiquitous Language glossary, and boundary ADRs.
```

Output excerpt (same scenario, abridged):

```text
| Context    | Responsibility          | Core terms        | Data ownership | Team    |
| :--------- | :---------------------- | :---------------- | :------------- | :------ |
| Booking    | create/cancel/arbitrate | Booking, Conflict | booking table  | Booking |
| Room Mgmt  | rooms/capacity upkeep   | Room, Capacity    | rooms table    | Rooms   |

Boundary ADR-1: Booking and Room live in separate contexts — the booking side holds
only a room_id reference; cross-context lookups go through a "room snapshot" translation
(rationale: availability rules change far more often than room master data;
risk: stale capacity shown while translation lags; alternative: one merged context —
rejected by team boundaries).
```

## Wrong way → fix

| Wrong | Fix |
| :--- | :--- |
| Slicing contexts by technical layers ("data/service/UI layer") | Cluster by consistency and language boundaries; layers are not bounded contexts |
| Treating a term's cross-context meaning clash as "close enough" | Same-name-different-meaning must be explicitly translated or renamed, recorded as an ADR |
| Glossary with nouns only, no anti-terms | The anti-term list is a required artifact (Manager/Handler-style generic words, vague business words) |
| Drawing boundaries without ADRs — "why this cut" is unanswerable later | At least 1 trade-off + risk per context (see validation checklist) |
| Forcing clusters without a subdomain classification, output looking complete | State the missing input in one line and mark Assumptions (see "when input is incomplete") |
