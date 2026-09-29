---
name: grill-me
description: >-
  User-invoked entry that runs a plan-grilling session — a relentless one-question-at-a-time
  interview to sharpen a plan or design. Use when the user wants to stress-test a plan,
  decision, or idea before committing to it. USER-INVOKED ONLY: the agent must not
  auto-invoke this entry — the user runs it explicitly. NOT for gathering facts or doing
  research — grilling is for decisions, not lookups.
slug: grill-me
version: 1.1.0
displayName: grill-me
disable-model-invocation: true
---

# Grill Me

A thin alias: `/grill-me` starts a plan-grilling session.

1. Load and execute the `plan-grilling` skill on the user's plan/decision/idea.
2. Do not invent a separate workflow — delegate entirely to `plan-grilling`.
3. If the `plan-grilling` skill is not installed, conduct the interview inline using its
   core method (one question at a time, recommendation attached, facts looked up from the
   environment, decisions reserved for the user), and say that you are doing so.

## Input / Output

- **Input**: a plan, decision, or idea — pasted text, a design-doc path, or a one-line intent.
- **Output**: a one-question-at-a-time interview, each question paired with your recommended
  answer, ending in a written shared-understanding summary. No files are changed and no code
  is written during the session.

## Example

Input:

    /grill-me migrate the cron jobs from server A to Kubernetes

What happens: the agent asks one question at a time — "Which of the cron jobs are
order-critical? My recommendation: start with the two payment jobs" — waits for the answer,
then walks down the next branch (cutover order, rollback, monitoring) until every decision
is resolved. It ends with a summary the user confirms before anything is acted on.

## NOT for

- Fact-finding or research questions ("what does X do?") — look those up in the environment
  or delegate them; grilling is for decisions the user must make.
- Executing the plan — nothing is implemented until the interview concludes and the user
  confirms the shared understanding.

## Misuse → fix

| Wrong | Fix |
|---|---|
| Agent auto-invokes grill-me mid-task | Never — user-invoked only; suggest it instead of running it |
| Agent asks several questions in one message | Re-ask one at a time and wait for each answer |
| Agent decides for the user | Withdraw the decision; re-present it with a recommendation and wait |
