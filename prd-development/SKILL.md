---
name: prd-development
description: >-
  PRD development: build a structured Product Requirements Document that connects problem,
  users, solution, and success criteria. Use when turning discovery notes into an
  engineering-ready document for a major initiative or feature.
slug: prd-development
version: 1.1.0
displayName: prd-development
---

# PRD Development

## Purpose
Guide product managers through structured PRD (Product Requirements Document) creation by orchestrating problem framing, user research synthesis, solution definition, and success criteria into a cohesive document. Use this to move from scattered notes and Slack threads to a clear, comprehensive PRD that aligns stakeholders, provides engineering context, and serves as a source of truth—avoiding ambiguity, scope creep, and the "build what's in my head" trap.

This is not a waterfall spec—it's a living document that captures strategic context, customer problems, proposed solutions, and success criteria, evolving as you learn through delivery.

## Input

**Works best with:** The feature or initiative the PRD covers.
**Also useful:** Discovery notes, problem statements, user research, success metrics, and constraints — paste whatever exists; the workflow slots it into the right phases and skips what's already answered.

Anything supplied with the invocation itself — text after the skill name, a pasted context dump, or an appended `ARGUMENTS:` line — counts as answers already given. Use it and skip whatever it covers; don't re-ask.

**Arriving empty-handed? That works too.** The workflow starts at problem definition and builds up from there.

**Example invocation:** `Build a PRD for self-serve workspace provisioning — here are my discovery notes and the OKR it ladders to.`

## Shortest Worked Example

**Precondition:** a feature/initiative plus whatever discovery material exists; no tooling or web access needed.
**Output excerpt (what you should see):**

```markdown
## 2. Problem Statement
- 60% of trial users drop off in the first 24 hours ("I didn't know what to do first" — 8/10 churned-user interviews)
## 6. Success Metrics
- Activation rate: 40% → 60% within 30 days of launch
```

**Done when:** the problem has evidence, users resolve to a named persona, the solution stays high-level (no pixel specs), and Section 6 has a primary metric with current → target.

## Failure Exits (closed set)

- **No feature/initiative given:** ask one question ("what are we specifying, and what OKR does it serve?") — don't draft a generic PRD.
- **No evidence for the problem:** tag the problem statement [ASSUMPTION—VALIDATE] and list the discovery to run — don't fabricate quotes or statistics.
- **Template/examples missing** (`template.md`, `examples/sample.md`, `references/prd-worked-examples.md` not found): `ls` this skill's directory and report the missing file — don't improvise a different structure.
- **Component skill absent** (`problem-statement`, `proto-persona`, etc. referenced but not installed): proceed with this file's phase instructions and note the skipped component — the phases here are self-sufficient.
- **Trivial feature:** say so and point to user stories instead — a full PRD is overkill (see When NOT to Use This).

## Wrong → Fix (quick table)

| Wrong | Fix |
|---|---|
| PRD written alone, dropped on the team (Pitfall 1) | Review the draft with design + eng before finalizing |
| Problem stated with no evidence (Pitfall 2) | Add customer quotes, analytics, or ticket data |
| Pixel-level UI specs in the solution section (Pitfall 3) | Keep Phase 5 high-level; design owns the details |
| No primary metric (Pitfall 4) | Define one metric with current → target in Phase 6 |
| Nothing under "Out of Scope" (Pitfall 5) | List what you're NOT building, and why |
| Drafting a PRD unprompted | Only on request or a named initiative — don't self-trigger |

## Key Concepts

### What is a PRD?

A PRD (Product Requirements Document) is a structured document that answers:
1. **What problem are we solving?** (Problem statement)
2. **For whom?** (Target users/personas)
3. **Why now?** (Strategic context, business case)
4. **What are we building?** (Solution overview)
5. **How will we measure success?** (Metrics, success criteria)
6. **What are the requirements?** (User stories, acceptance criteria, constraints)
7. **What are we NOT building?** (Out of scope)

### PRD Structure (Standard Template)

> **Standard skeleton:** kept verbatim in [`references/prd-template-skeleton.md`](references/prd-template-skeleton.md); the fill-in version is [`template.md`](template.md).

### Why This Works
- **Alignment:** Ensures everyone (PM, design, eng, stakeholders) understands the "why"
- **Context preservation:** Captures research and strategic rationale for future reference
- **Decision log:** Documents what's in scope, out of scope, and why
- **Execution clarity:** Provides engineering with user stories and acceptance criteria

### Anti-Patterns (What This Is NOT)
- **Not a detailed spec:** PRDs frame the problem and solution; they don't specify UI pixel-by-pixel
- **Not waterfall:** PRDs evolve as you learn; they're not frozen contracts
- **Not a substitute for collaboration:** PRDs complement conversation, not replace it

### When to Use This
- Starting a major feature or product initiative
- Aligning cross-functional teams on scope and requirements
- Documenting decisions for future reference
- Onboarding new team members to a project

### When NOT to Use This
- For small bug fixes or trivial features (overkill)
- When problem and solution are already clear and aligned (just write user stories)
- For continuous discovery experiments (use Lean UX Canvas instead)

---

### Facilitation Source of Truth

When running this workflow as a guided conversation, use [`workshop-facilitation`](../workshop-facilitation/SKILL.md) as the interaction protocol.

It defines:
- session heads-up + entry mode (Guided, Context dump, Best guess)
- one-question turns with plain-language prompts
- progress labels (for example, Context Qx/8 and Scoring Qx/5)
- interruption handling and pause/resume behavior
- numbered recommendations at decision points
- quick-select numbered response options for regular questions (include `Other (specify)` when useful)

This file defines the workflow sequence and domain-specific outputs. If there is a conflict, follow this file's workflow logic.

## Application

Use `template.md` as the fill-in document. The template includes:

- **Per-section coaching blocks** — each section has its own Instructions, Steps, Contributing Skills, and Activities so the template is self-guiding even without this workflow.
- **Inline gap tagging** — tag every gap as **Assumption** (plausible but unvalidated) or **Open Question** (unknown, needs discovery). Tag inline where the gap appears, not just at the end.
- **Cross-section recommendation prompts** — after completing each section, a "Before moving on" block checks consistency with prior sections and warns about what the next section will need.
- **Self-assessment** — after Section 10, a diagnostic captures the strongest section, weakest section, top assumptions to validate, and the recommended next step before sharing the PRD.
- **Skill cross-reference table** — maps 15 skills to the specific sections they feed (e.g., problem framing canvas → Section 2, epic breakdown patterns → Section 7).

This workflow orchestrates **8 phases** over **2-4 days**, using multiple component and interactive skills. The phases below describe the facilitation sequence; the template captures the output.

---

## Phase 1: Executive Summary (30 minutes)

**Goal:** Write a one-paragraph overview for skimmers.

### Activities

**1. Draft Executive Summary**
- **Format:** "We're building [solution] for [persona] to solve [problem], which will result in [impact]."
- **Example:**
  > "We're building a guided onboarding checklist for non-technical small business owners to solve the problem of 60% drop-off in the first 24 hours due to lack of guidance, which will increase activation rate from 40% to 60% and reduce churn by 10%."

- **Participants:** PM
- **Duration:** 30 minutes
- **Output:** One-paragraph summary

**Tip:** Write this first (forces clarity), but refine it last (after other sections are complete).

---

## Phase 2: Problem Statement (60 minutes)

**Goal:** Frame the customer problem with evidence.

### Activities

**1. Write Problem Statement**
- **Use:** [`problem-statement`](../problem-statement/SKILL.md) (component)
- **Input:** Discovery insights from problem discovery work (framing canvas or interview synthesis)
- **Participants:** PM
- **Duration:** 30 minutes
- **Output:** Structured problem statement

**Example Problem Statement:**

**Example Problem Statement:** verbatim in [`references/prd-worked-examples.md`](references/prd-worked-examples.md) (§ Phase 2).

**2. Add Supporting Context (Optional)**
- **Customer journey map:** If problem spans multiple touchpoints
- **Use:** [`customer-journey-map`](../customer-journey-map/SKILL.md) output
- **Jobs-to-be-done:** If motivations are key
- **Use:** [`jobs-to-be-done`](../jobs-to-be-done/SKILL.md) output

### Outputs from Phase 2

- **Problem statement:** Who, what, why, evidence
- **Supporting artifacts:** Journey map, JTBD (if relevant)

---

## Phase 3: Target Users & Personas (30 minutes)

**Goal:** Define who you're building for.

### Activities

**1. Document Personas**
- **Use:** [`proto-persona`](../proto-persona/SKILL.md) (component) output
- **Participants:** PM
- **Duration:** 30 minutes
- **Format:** Include persona name, role, goals, pain points, behaviors

**Example:**

**Example:** verbatim in [`references/prd-worked-examples.md`](references/prd-worked-examples.md) (§ Phase 3).

### Outputs from Phase 3

- **Primary persona:** Detailed profile
- **Secondary personas:** (if applicable)

---

## Phase 4: Strategic Context (45 minutes)

**Goal:** Explain why this matters to the business and why now.

### Activities

**1. Document Business Goals**
- **Source:** Company OKRs, strategic memos, roadmap
- **Format:** Link feature to business outcomes
- **Example:**
  > "This initiative supports our Q1 OKR: Reduce churn from 15% to 8%. Improving onboarding activation directly impacts retention."

**2. Size Market Opportunity (Optional)**
- **Use:** market sizing (TAM/SAM/SOM) output
- **When:** For major initiatives, new products, exec presentations
- **Example:**
  > "TAM: 50M small businesses globally. SAM: 5M using SaaS tools. SOM: 500K solopreneurs in our target segments. Improving onboarding could unlock 30% of SAM (1.5M potential customers)."

**3. Document Competitive Landscape (Optional)**
- **Source:** Competitor research, G2/Capterra reviews
- **Example:**
  > "Competitors (Competitor A, B) have guided onboarding. Our lack of guidance is cited as a churn reason in exit surveys."

**4. Explain "Why Now?"**
- **Rationale:** Why prioritize this now vs. later?
- **Example:**
  > "Churn spiked 15% in Q4. Onboarding is the #1 driver (60% churn in first 30 days). Fixing this is critical to hitting retention OKR."

### Outputs from Phase 4

- **Business goals:** OKRs or strategic initiatives
- **Market opportunity:** TAM/SAM/SOM (if applicable)
- **Competitive context:** How competitors address this
- **Why now:** Urgency rationale

---

## Phase 5: Solution Overview (60 minutes)

**Goal:** Describe what you're building (high-level, not detailed spec).

### Activities

**1. Write Solution Description**
- **Format:** High-level overview, 2-3 paragraphs
- **Example:**

**Example:** verbatim in [`references/prd-worked-examples.md`](references/prd-worked-examples.md) (§ Phase 5).

**2. Add User Flows or Wireframes (Optional)**
- **Use:** Design tools (Figma, Sketch), or hand-drawn sketches
- **When:** For complex features requiring visual explanation
- **Output:** Embedded in PRD or linked

**3. Reference Story Map (Optional)**
- **Use:** story map from a story-mapping activity output
- **When:** For complex features with multiple release slices
- **Output:** Link to story map

### Outputs from Phase 5

- **Solution description:** High-level overview
- **User flows/wireframes:** (if applicable)
- **Story map:** (if applicable)

---

## Phase 6: Success Metrics (30 minutes)

**Goal:** Define how you'll measure success.

### Activities

**1. Define Primary Metric**
- **Question:** What is the ONE metric this feature must move?
- **Example:** "Activation rate (% of users completing first action within 24 hours)"
- **Target:** "Increase from 40% to 60%"

**2. Define Secondary Metrics**
- **Question:** What else should we monitor (but not optimize for)?
- **Examples:**
  - Time-to-first-action (reduce from 3 days to 1 day)
  - Completion rate of onboarding checklist (target: 80%)
  - Support ticket volume (reduce "How do I get started?" tickets by 50%)

**3. Define Guardrail Metrics**
- **Question:** What should NOT get worse?
- **Example:** "Sign-up conversion rate (don't add friction to signup flow)"

**Example:**

**Example:** verbatim in [`references/prd-worked-examples.md`](references/prd-worked-examples.md) (§ Phase 6).

### Outputs from Phase 6

- **Primary metric:** What you're optimizing for
- **Secondary metrics:** Additional success indicators
- **Guardrail metrics:** What shouldn't regress

---

## Phase 7: User Stories & Requirements (90-120 minutes)

**Goal:** Break solution into user stories with acceptance criteria.

### Activities

**1. Write Epic Hypothesis**
- **Use:** epic hypothesis statement (component-style activity)
- **Participants:** PM
- **Duration:** 30 minutes
- **Output:** Epic hypothesis statement

**Example:**
> "We believe that adding a guided onboarding checklist for non-technical users will increase activation rate from 40% to 60% because users currently drop off due to lack of guidance. We'll measure success by activation rate 30 days post-launch."

**2. Break Down Epic into User Stories**
- **Use:** epic breakdown (interactive - with Richard Lawrence's 9 patterns)
- **Participants:** PM, design, engineering
- **Duration:** 90 minutes
- **Output:** User stories split by patterns (workflow, CRUD, business rules, etc.)

**3. Write User Stories**
- **Use:** user story + acceptance criteria (component-style activity)
- **Participants:** PM
- **Duration:** 30 minutes per story
- **Format:** User story + acceptance criteria

**Example User Stories:**

**Example User Stories:** verbatim in [`references/prd-worked-examples.md`](references/prd-worked-examples.md) (§ Phase 7).

**4. Document Constraints & Edge Cases**
- **Technical constraints:** Platform limitations, browser support, etc.
- **Edge cases:** What if user skips step 2? What if they complete steps out of order?

### Outputs from Phase 7

- **Epic hypothesis:** Testable statement
- **User stories:** 3-10 stories with acceptance criteria
- **Constraints:** Technical limitations, edge cases

---

## Phase 8: Out of Scope & Dependencies (30 minutes)

**Goal:** Define what you're NOT building and what you depend on.

### Activities

**1. Document Out of Scope**
- **Format:** List features/requests explicitly excluded
- **Rationale:** Why not building now?

**Example:**

**Example:** verbatim in [`references/prd-worked-examples.md`](references/prd-worked-examples.md) (§ Phase 8).

**2. Document Dependencies**
- **Technical dependencies:** Platform upgrades, API changes required
- **External dependencies:** Third-party integrations, partnerships
- **Team dependencies:** Design handoff, data pipeline work

**Example:**

**Example:** verbatim in [`references/prd-worked-examples.md`](references/prd-worked-examples.md) (§ Phase 9).

**3. Document Open Questions**
- **Unresolved decisions:** Areas requiring discovery or discussion

**Example:**

**Example:** verbatim in [`references/prd-worked-examples.md`](references/prd-worked-examples.md) (§ Phase 10).

### Outputs from Phase 8

- **Out of scope:** What we're NOT building
- **Dependencies:** What we need before starting
- **Risks:** Potential blockers and mitigations
- **Open questions:** Unresolved decisions

---

## Complete Workflow: End-to-End Summary

> The full end-to-end timeline (Day 1 → Day 4, durations, and which skill feeds which phase) is kept verbatim in [`references/prd-worked-examples.md`](references/prd-worked-examples.md) (§ End-to-End Timeline).

**Total Time Investment:**
- **Fast track:** 1.5-2 days (straightforward feature, clear requirements)
- **Typical:** 2-3 days (includes discovery synthesis, stakeholder review)
- **Complex:** 3-4 days (major initiative, multiple personas, extensive user stories)

---

## Examples

See `examples/sample.md` for full PRD examples.

Mini example excerpt:

```markdown
## 2. Problem Statement
- 60% of trial users drop off in first 24 hours
## 6. Success Metrics
- Activation rate: 40% → 60%
```

## Common Pitfalls

### Pitfall 1: PRD Written in Isolation
**Symptom:** PM writes PRD alone, presents finished doc to team

**Consequence:** No buy-in, team doesn't understand rationale

**Fix:** Collaborate on Phase 7 (user stories) with design + eng; review draft PRD before finalizing

---

### Pitfall 2: No Evidence in Problem Statement
**Symptom:** "We believe users have this problem" (no data, no quotes)

**Consequence:** Team questions whether problem is real

**Fix:** Use discovery insights from your discovery work; include customer quotes, analytics, support tickets

---

### Pitfall 3: Solution Too Prescriptive
**Symptom:** PRD specifies exact UI, pixel dimensions, button colors

**Consequence:** Removes design collaboration, becomes waterfall spec

**Fix:** Keep Phase 5 high-level; let design own UI details

---

### Pitfall 4: No Success Metrics
**Symptom:** PRD defines problem + solution but no metrics

**Consequence:** Can't validate if feature succeeded

**Fix:** Always define primary metric in Phase 6 (what you're optimizing for)

---

### Pitfall 5: Out of Scope Not Documented
**Symptom:** No section on what's NOT being built

**Consequence:** Scope creep, stakeholders expect features not planned

**Fix:** Explicitly document out of scope in Phase 8

---

## References

### Related Skills (Orchestrated by This Workflow)

**Phase 2:**
- [`problem-statement`](../problem-statement/SKILL.md) (component)
- problem framing canvas (interactive, for context)
- [`customer-journey-map`](../customer-journey-map/SKILL.md) (optional)

**Phase 3:**
- [`proto-persona`](../proto-persona/SKILL.md) (component)
- [`jobs-to-be-done`](../jobs-to-be-done/SKILL.md) (component, optional)

**Phase 4:**
- market sizing TAM/SAM/SOM (interactive, optional)

**Phase 5:**
- user story mapping workshop (interactive, optional)

**Phase 7:**
- epic hypothesis statement (component-style)
- epic breakdown patterns (interactive)
- user story + acceptance criteria (component-style)

### External Frameworks
- Martin Eriksson, "How to Write a Good PRD" (2012) — PRD structure
- Marty Cagan, *Inspired* (2017) — Product spec principles
- Amazon, "Working Backwards" (PR/FAQ format) — Alternative to PRD

### Dean's Work
- [If Dean has PRD templates, link here]

---

**Skill type:** Workflow
**Suggested filename:** `prd-development.md`
**Suggested placement:** `/skills/workflows/`
**Dependencies:** Orchestrates 8+ component and interactive skills across 8 phases
