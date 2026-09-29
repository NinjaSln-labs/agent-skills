---
name: plan-grilling
description: >-
  Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to
  stress-test their thinking, or uses any 'grill' trigger phrases. NOT for executing the
  plan or gathering background facts — decisions only.
slug: plan-grilling
version: 1.1.0
displayName: plan-grilling
---

# Plan Grilling

Interview me relentlessly about every aspect of this until we reach a shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing. Asking multiple questions at once is bewildering.

If a *fact* can be found by exploring the environment (filesystem, tools, etc.), look it up rather than asking me. The *decisions*, though, are mine — put each one to me and wait for my answer.

Do not act on it until I confirm we have reached a shared understanding.

## When to trigger

Trigger phrases include: "grill me", "poke holes in this plan", "stress-test this idea",
"what am I missing", or asking to be questioned about a decision. Example:

    /plan-grilling I'm going to rewrite our billing service in Go next quarter

The session then walks the decision tree: scope (which parts?), motivation (rewrite vs.
strangler migration), risk (what breaks first?), rollout, rollback — one question per turn,
each with a recommendation.

## NOT for

- Executing the plan — no code, tickets, or docs are produced until the user confirms
  the shared understanding; even then, hand off rather than act unless asked.
- Fact-finding ("what does the billing service currently do?") — look it up in the
  environment instead of asking; bring facts into the questions, not as questions.

## Edge cases → what to do

- **No plan provided** (just "grill me"): ask for the artifact first — pasted text,
  a doc path, or a one-line intent. Do not invent a plan to grill.
- **User goes silent or answers "you decide"**: that is a decision they are delegating —
  state your recommendation explicitly and ask for a yes/no before moving on; do not
  silently absorb it into "shared understanding".
- **Question can be answered from the repo**: look it up, state the fact, and ask only
  about the judgment on top of it.
- **The plan keeps growing mid-interview**: park the addition in an explicit
  "out of scope for this session" list and keep the current branch closed.

## Misuse → fix

| Wrong | Fix |
|---|---|
| Agent asks five questions in one message | Re-ask one at a time; wait for each answer |
| Agent makes the decision and proceeds | Withdraw the action; re-present the decision with a recommendation |
| Agent asks what a file in the repo already shows | Look it up first; question only the user's judgment |
