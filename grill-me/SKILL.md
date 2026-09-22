---
name: grill-me
description: >-
  User-invoked entry that runs a /plan-grilling session — a relentless interview to
  sharpen a plan or design. Use when the user wants to stress-test a plan, decision, or
  idea before committing to it. USER-INVOKED ONLY: the agent must not auto-invoke this
  entry — the user runs it explicitly.
slug: grill-me
version: 1.0.1
displayName: grill-me
disable-model-invocation: true
---

# Grill Me

Thin entry point. Immediately follow **`plan-grilling`**:

1. Load and execute the `plan-grilling` skill on the user's plan/decision/idea.
2. Do not invent a separate workflow — delegate entirely to `plan-grilling`.
