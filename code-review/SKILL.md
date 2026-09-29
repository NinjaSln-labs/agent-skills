---
name: code-review
description: >-
  Review the changes since a fixed point (commit, branch, tag, or merge-base) along two
  axes — Standards (does the code follow this repo's documented coding standards?) and
  Spec (does the code match what the originating issue/PRD asked for?). Runs both reviews
  in parallel sub-agents and reports them side by side. Stage-end mode: fixed point is the
  parent of the stage's first commit, Spec axis checks the stage spec's DoD, output is a
  statusized open/fixed/recorded findings list. Use when the user wants to review a branch,
  a PR, work-in-progress changes, asks to "review since X", asks to review for code smells,
  or at a stage completion (stage-end review).
slug: code-review
version: 1.1.0
displayName: code-review
---

# Code Review

Two-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards** — does the code conform to this repo's documented coding standards?
- **Spec** — does the code faithfully implement the originating issue / PRD / spec?

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings.

The Spec axis often needs the project's issue tracker. Prefer whatever tracker conventions the project already documents (e.g. `docs/agents/issue-tracker.md`). If that file is missing, ask the user where issues live (a tracker URL, local files, or a PRD path) and record the answer there; if you installed an upstream skill-suite, its setup command may bootstrap this file for you.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point — a commit SHA, branch name, tag, `main`, `HEAD~5`, etc. If they didn't specify one, ask for it.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here — not inside two parallel sub-agents.

### 2. Identify the spec source

Look for the originating spec, in this order:

1. Issue references in the commit messages (`#123`, `Closes #45`, GitLab `!67`, etc.) — fetch via the workflow in `docs/agents/issue-tracker.md` if that file exists; otherwise ask the user how to reach the tracker (or probe the repo's remote host) — never assume the file is present.
2. A path the user passed as an argument.
3. A PRD/spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. If nothing is found, ask the user where the spec is. If they say there isn't one, the **Spec** sub-agent will skip and report "no spec available".

### 3. Identify the standards sources

Anything in the repo that documents how code should be written, such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below — a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation — and, like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name** — a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code** — the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy** — a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps** — the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession** — a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches** — the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery** — one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change** — one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality** — abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains** — long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man** — a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest** — a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 4. Spawn both sub-agents in parallel

Send a single message with two `Agent` tool calls. Use the `general-purpose` subagent for both.

**Standards sub-agent prompt** — include:

- The full diff command and commit list.
- The list of standards-source files you found in step 3, **plus the smell baseline from step 3** pasted in full — the sub-agent has no other access to it.
- The brief: "Report — per file/hunk where relevant — (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls — documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling enforces. Under 400 words."

**Spec sub-agent prompt** — include:

- The diff command and commit list.
- The path or fetched contents of the spec.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Under 400 words."

If the spec is missing, skip the Spec sub-agent and note this in the final report.

### 5. Aggregate

Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do **not** merge or rerank findings — the two axes are deliberately separate (see _Why two axes_).

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes — that's the reranking the separation exists to prevent.

## 阶段末即时评审模式（Stage-End Review）

阶段完成声明 → stage-gate 之前的收口评审（NeonForge 已实践，回写为可复用模式）：

- **固定点**：阶段首 commit^（`git log --oneline --grep="S{N}"` 找该阶段首个 commit，取其父提交）；无阶段 commit 则从用户确认。
- **Spec 轴**：以 stage-spec DoD 为 spec 来源（`docs/design/stage-specs/S{N}.md`）——逐条核对代码是否实现（DoD 未实现 = Spec fail）。
- **Standards 轴**：同普通模式（仓库规范 + smell 基线）。
- **产出 = 状态化报告**：每条 finding 标注状态——`open`（待修）/ `fixed`（本次已修，含 commit+回归测试证据）/ `recorded`（裁决不修，含理由）——落盘 `docs/audits/stage-review-S{N}-YYYY-MM-DD.md`。
- **下游**：open 项 → `audit-item` 入账（入本仓约定的审计台账位置）；阶段收口 → `stage-gate` 跑 DoD（含审计状态核对）。

与普通模式的差异：普通模式输出双轴报告即可；阶段模式要求**状态化清单**（每条 finding 带状态 + 证据），可直接被 audit-item 消费、被 stage-gate 枚举。

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.

## Minimal worked example

Precondition: HEAD has commits since `v1.2.0`, `CODING_STANDARDS.md` exists, a commit message references `#42`.

User says: **"review the changes since v1.2.0"**

What happens:

1. `git rev-parse v1.2.0` resolves; `git diff v1.2.0...HEAD` is non-empty; `git log v1.2.0..HEAD --oneline` shows 3 commits.
2. Spec source: `#42` found in a commit message, fetched per `docs/agents/issue-tracker.md`.
3. Both sub-agents run in parallel; the aggregated report looks like:

```markdown
## Standards
- src/utils/date.ts:12 — Mysterious Name: `fn2` doesn't reveal intent → rename (judgement call)
- src/api/orders.ts:48 — bare `except:` violates CODING_STANDARDS.md §3 (hard violation)

## Spec
- #42 asked for CSV export; not present in the diff (missing requirement)
- Diff adds a `/health` endpoint not mentioned in #42 (scope creep)

Summary: Standards 2 findings (worst: bare except), Spec 2 findings (worst: CSV export missing).
```

## Failure exits

| Situation | Observable signal | Exit action |
|-----------|-------------------|-------------|
| Fixed point doesn't resolve | `git rev-parse <fixed-point>` exits non-zero ("unknown revision") | Tell the user which ref failed and ask for a corrected one. Do **not** spawn sub-agents. |
| Empty diff | `git diff <fixed-point>...HEAD` prints nothing | Report "no changes since `<fixed-point>`" and stop. |
| No spec found after the step-2 lookups | none of the four lookups matched | Ask the user where the spec is; if there is none, run Standards only and write "Spec skipped: no spec available" in the report. |
| Repo documents no standards | no `CODING_STANDARDS.md` / `CONTRIBUTING.md` / similar | Proceed with the smell baseline only and note "no documented repo standards found" at the top of the Standards section. |

## Wrong way → right way (FAQ)

| Wrong | Right |
|-------|-------|
| Running a review without the user asking for one | Run only on request ("review since X", a PR review, stage-end review); otherwise propose it |
| Merging both axis reports into one ranked list | Keep `## Standards` and `## Spec` separate; end with one summary line per axis |
| Telling the sub-agent "see step 3 of the skill" | Paste the smell baseline in full into the sub-agent prompt — sub-agents cannot see this skill |
| Reporting a baseline smell as a hard violation | Label smells as judgement calls; a documented repo standard overrides the baseline |
| Reviewing the whole repo instead of the change | Review only `git diff <fixed-point>...HEAD`; uncommitted worktree edits are out of scope unless the user asks to include them |

## NOT for

- Not a vulnerability/CVE sweep — that's `security-scan`.
- Not for secrets or credential detection — that's `secrets-scan`.
- Not for writing or auto-fixing code; the report is the deliverable (fixes happen after, with the user's go-ahead).
