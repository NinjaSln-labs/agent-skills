---
name: problem-resolution-flow
description: >-
  Problem Resolution Flow: end-to-end evidence-driven pipeline from symptom to shipped
  fix — locate, classify by scope, design with external research cross-validation, fix
  with a failing test, verify, and close the loop. Use when handling any bug, UX
  complaint, or behavior gap, before jumping to fixes.
---

# Problem Resolution Flow

## Core Principle

Every fix must be traceable back to evidence. **Never patch the symptom.** If the same
symptom is fixed three times, stop and question the design.

## The Flow

```
① LOCATE     — evidence first: error message → logs → reproduced behavior → which component
② TRACE      — follow the data/call chain back to the original trigger (root-cause-tracing)
③ CLASSIFY   — problem type: single-point / logic error / interaction UX / design or architecture
④ SCOPE      — line / function / module / project → determines fix depth
⑤ DRAFT      — form your own solution before looking outward
⑥ RESEARCH   — external evidence by type (competitor behavior / user logs / official or academic
               docs); key claims cross-validated across 2+ independent channels
⑦ CROSS-CHECK — solution vs evidence; mismatch → back to ③ or ①
⑧ FIX        — TDD: write a failing test first, then the minimum change
⑨ VERIFY     — run the verifier (a check that produces pass/fail); full regression stays green
⑩ CLOSE      — refill tickets / handoff deltas
```

## Rules

- **No fix without location.** If you cannot say which component and which flow step
  fails, you are not ready to fix.
- **3 strikes = upgrade.** Fixing the same symptom 3+ times means the problem is one
  level up: single-point → module → design. Stop and question the architecture.
- **Scope discipline.** Fix at the scope the type demands — no bigger, no smaller.
  A single-point bug gets a line fix, not a refactor.
- **Draft before research.** Think first; research validates or refutes, it does not
  replace thinking.
- **Research is not optional for UX problems.** Interaction/design gaps need competitor
  comparison + user-log evidence, not just code reading.
- **Dual-channel verification.** Key external claims must match across 2+ independent
  search channels; conflicting channels are the most valuable signal — dig.
- **Ship with a test.** The fix is not done until the failing test passes and the suite
  stays green (verification-before-completion).

## Anti-patterns

- Patching the symptom and declaring done
- Skipping classification and scope ("just fix it")
- Single-channel research conclusions
- Fixing beyond the scope (refactoring while fixing a typo)
- No regression check before closing

## Relationship to sibling skills

- `problem-dive` — intake methodology when a problem/UX complaint arrives: evidence first,
  do not start fixing. This skill takes over once the problem is understood and a fix
  path is chosen.
- `systematic-debugging` — code root-cause investigation (observe → hypothesize → test →
  fix) for the code-bug path inside ①-③. Use both: systematic-debugging for root cause,
  this skill for the end-to-end flow.
