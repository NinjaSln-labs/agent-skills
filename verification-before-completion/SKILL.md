---
name: verification-before-completion
description: >-
  Run verification commands and confirm fresh output before claiming work
  complete—evidence before assertions, never claim done without verification. Use when
  about to claim work is complete, fixed, or passing, before committing or creating PRs.
  NOT for: stage-level aggregation of a whole DoD spec — that is stage-gate, which runs
  the full gate and never fixes.
slug: verification-before-completion
version: 1.1.0
displayName: verification-before-completion
---

# Verification Before Completion

## Overview

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

**边界（与 stage-gate 分工）：** 本技能 = 单次验证（一条命令/一个声明/一次提交前）；`stage-gate` = 阶段级聚合（整份 stage-spec DoD 逐条执行，只验不修）——单点验证先行，阶段收口再跑门禁。

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✓ [Run test command] [See: 34/34 pass] "All tests pass"
✗ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✓ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
✗ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✓ [Run build] [See: exit 0] "Build passes"
✗ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✓ Re-read plan → Create checklist → Verify each → Report gaps or completion
✗ "Tests pass, phase complete"
```

**Agent delegation:**
```
✓ Agent reports success → Check VCS diff → Verify changes → Report actual state
✗ Trust agent report
```

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to:**
- Exact phrases
- Paraphrases and synonyms
- Implications of success
- ANY communication suggesting completion/correctness

## How to invoke

This is a behavior rule the agent loads and applies to itself — no script, no parameters. Invocation
is plain text, inline or as a slash-style reference:

```text
verification-before-completion: verify the last claim before I report this task done
```

```text
Use verification-before-completion — about to commit; run the test suite and show me fresh output first.
```

**When to reach for it (trigger summary):** the moment you are about to write any success/completion
wording ("done", "passing", "fixed", "all green"), before commit/PR, before handing a task off to
another agent, and after any agent reports success. If no such claim is imminent, this rule has nothing
to gate — that is not a violation, just nothing to verify yet.

## When verification FAILS — the recovery script

A failed verification is not a dead end; it is the system working. The wrong recovery is silence,
softening, or "almost done." The required wording:

```text
Verification failed: [command] exited 1 — [3 of 34 tests failing: <names>].
Actual status: NOT complete. Next: [the concrete fix or investigation step].
```

Rules for the recovery:

- State the command, the exit code, and the failure count — never "mostly passing."
- Claim stays withdrawn until a fresh rerun passes; a fix followed by no rerun is still an unverified
  claim.
- If the verification command itself cannot run (missing dependency, wrong path), say exactly that
  ("test suite not runnable: no `package.json` scripts found") and stop — an unrunnable gate is a
  failure to report, not a pass to assume.

### Wrong way → fix

| Wrong | Fix |
|---|---|
| "Fixed it, should pass now" | Rerun the command; report exit code + counts |
| "Tests fail but the build works, so we're good" | Both gates must pass; report the failing one as the status |
| Silent retry loop without telling the user | First failure gets the recovery script above, immediately |
| "Verification isn't possible here" (as a pass) | Name what cannot run and why; that is the status — NOT done |
