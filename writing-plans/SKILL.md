---
name: writing-plans
description: >-
  Write comprehensive implementation plans from a spec or requirements—break multi-step
  work into bite-sized tasks with exact file paths, complete code, and verification steps
  (DRY, YAGNI, TDD, frequent commits; no placeholders). Plans are saved as dated markdown
  docs under the project's plans directory (probe for an existing convention, default
  docs/plans/; user preferences override). Use when you have a spec or requirements for a multi-step task,
  before touching code. NOT for: stage contract specs (DoD/gate assertions + TDD grid) —
  those are stage-spec, executed by stage-gate.
slug: writing-plans
version: 1.1.1
displayName: writing-plans
---

# Writing Plans

## When to Use / How to Invoke

Use this skill when **all** of these hold (do not self-trigger otherwise):

- There is a spec, requirements doc, or user-described feature for **multi-step** work.
- Code has not been touched yet for this work — plans come before implementation.
- The work needs task decomposition with exact file paths, code, and verification steps.

Explicit invocation form: `use writing-plans: <paste spec or point to spec file>`. Defaults applied when unspecified: save location `docs/plans/` (probed/overridden as below), filename `YYYY-MM-DD-<feature-name>.md`, TDD-style task structure.

**NOT for:** stage contract specs (DoD/gate assertions + TDD grid) — those are `stage-spec`, executed by `stage-gate` (see 边界 below). Not for single-step fixes that don't need a plan.

## Example (precondition → invocation → output excerpt)

Precondition: a short spec exists (e.g. "add rate limiting to the login endpoint").

Invocation:

```text
use writing-plans: spec below — add per-IP rate limiting to POST /login, 5 req/min, Redis backed
```

Output excerpt (saved to `docs/plans/2026-09-29-login-rate-limit.md`):

```markdown
# Login Rate Limit Implementation Plan
**Goal:** Cap POST /login at 5 requests/minute per IP using Redis.
### Task 1: Rate limiter middleware
**Files:**
- Create: src/middleware/rate-limit.ts
- Test: tests/middleware/rate-limit.test.ts
- [ ] **Step 1: Write the failing test**
...
- [ ] **Step 2: Run test to verify it fails** — Run: `npm test -- rate-limit` Expected: FAIL
```

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** If working in an isolated git worktree, ensure one exists before execution starts — create it from the current branch if the project has no worktree yet.

**Save plans to:** the project's plans directory. Probe first: if the repo already has a plans directory or a documented plan-location convention, use that; otherwise default to `docs/plans/`.
Filename: `YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Task Right-Sizing

A task is the smallest unit that carries its own test cycle and is worth a
fresh reviewer's gate. When drawing task boundaries: fold setup,
configuration, scaffolding, and documentation steps into the task whose
deliverable needs them; split only where a reviewer could meaningfully
reject one task while approving its neighbor. Each task ends with an
independently testable deliverable.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header** — Goal/Architecture/Tech Stack + a Global Constraints section carrying the spec's project-wide requirements verbatim (full template: [references/plan-templates.md](references/plan-templates.md)).

## Task Structure

Each task = exact Files (Create/Modify/Test) + Interfaces (Consumes/Produces with exact signatures) + a fixed test-first step cycle: write failing test → verify FAIL → minimal implementation → verify PASS → commit (full template: [references/plan-templates.md](references/plan-templates.md)).

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.

## Failure Exits (observable)

- **Spec too vague to plan** (no measurable behavior, no target files, contradictory requirements): do **not** generate a placeholder-ridden plan. Output a blocking question list naming the missing decisions (e.g. "undefined: rate limit window; no test runner configured — which?") and stop. Observable exit: the response ends with numbered questions, no plan file is written.
- **No repo / empty directory**: state that file paths cannot be exact, ask whether to scaffold first or plan against a target stack, and do not invent paths under an assumed layout.
- **Plans directory unwritable or probe fails**: say where the plan *would* be saved, ask the user to confirm an alternative location, do not silently write elsewhere.
- **Spec covers multiple independent subsystems** (see Scope Check): stop and propose the split before writing any plan.

## FAQ / Wrong Way → Fix

| Wrong way | Fix |
|-----------|-----|
| Generating a plan from a one-line vague request without asking anything | Run the Failure Exit: list missing decisions, wait for answers, then plan |
| Writing "TBD" / "add appropriate error handling" to keep momentum | That is a plan failure — write the actual code or the exact assertion (see No Placeholders) |
| Planning stage DoD/gate assertions because the spec is staged | That is `stage-spec` territory; check the 边界 section and hand off |
| One giant task "implement the feature" | Split into bite-sized tasks, each with its own test→fail→pass→commit cycle |
| Inventing file paths in a repo you haven't inspected | Read the repo first (File Structure section); exact paths are a hard requirement |
| Self-triggering plan writing on any coding request | Only when a spec precedes multi-step implementation; otherwise just do the work |

## 边界（与 stage-spec 分工）

- **stage-spec**（阶段契约）：DoD 机器可验证断言 + TDD 网格 + 产出物 + 边界——被 `stage-gate` 逐条执行；用户要「写 S{N} spec / 回填阶段 spec」→ 走 `stage-spec` 技能。
- **writing-plans**（本技能）：通用任务分解——bite-size 步骤 + 完整代码 + 验证步骤。
- 顺序：stage-spec 定稿（契约先行）→ 需要时再按 writing-plans 拆任务；DoD 断言是验收依据，plan 的任务不得超出 DoD 边界。

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `<plans-dir>/<filename>.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session, task-by-task with batch execution and checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- Dispatch a fresh subagent per task, with two-stage review between tasks

**If Inline Execution chosen:**
- Execute task-by-task in this session, with checkpoints for review
